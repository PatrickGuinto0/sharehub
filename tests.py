"""Smoke test for Phase 2 auth flow. Run: python tests.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    from app import create_app
    from extensions import db

    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    app = create_app(
        config_overrides={
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        }
    )

    with app.app_context():
        db.create_all()

        client = app.test_client()

        # 1. Register
        r = client.post(
            "/auth/register",
            data={
                "username": "alice",
                "email": "Alice@Example.com",
                "password": "supersecret1",
                "confirm": "supersecret1",
            },
            follow_redirects=True,
        )
        assert r.status_code == 200, f"register failed: {r.status_code}"
        assert b"Welcome to ShareHub, alice" in r.data, "no welcome flash"

        # 2. Logged in after register — navbar shows username
        r = client.get("/")
        assert b"alice" in r.data, "username not in navbar after register"
        assert b"Logout" in r.data, "logout link missing"

        # 3. Logout
        r = client.post("/auth/logout", follow_redirects=True)
        assert b"logged out" in r.data.lower(), "no logout flash"

        # 4. Duplicate username rejected (case-insensitive)
        r = client.post(
            "/auth/register",
            data={
                "username": "ALICE",
                "email": "other@example.com",
                "password": "supersecret1",
                "confirm": "supersecret1",
            },
        )
        assert b"username is already taken" in r.data.lower(), "duplicate username allowed"

        # 5. Login with email (case-insensitive)
        r = client.post(
            "/auth/login",
            data={"identifier": "ALICE@EXAMPLE.COM", "password": "supersecret1"},
            follow_redirects=True,
        )
        assert b"Logged in as alice" in r.data, "login with email failed"

        # 5. Wrong password rejected
        client.post("/auth/logout")
        r = client.post(
            "/auth/login",
            data={"identifier": "alice", "password": "wrongpass1"},
            follow_redirects=True,
        )
        assert b"Invalid username/email or password" in r.data, "wrong password accepted"

        # 6. Login with username works
        r = client.post(
            "/auth/login",
            data={"identifier": "alice", "password": "supersecret1"},
            follow_redirects=True,
        )
        assert b"Logged in as alice" in r.data, "login with username failed"

        # 7. Navbar shows username when logged in
        r = client.get("/")
        assert b"alice" in r.data, "username not in navbar"
        assert b"Logout" in r.data, "logout link missing"

        phase3_tests(client)
        phase4_tests(client)

    os.unlink(db_path)
    print("All Phase 2 + 3 + 4 tests passed.")


def phase3_tests(client):
    import io

    # 8. Create item with photo
    photo = (io.BytesIO(b"\xff\xd8\xff\xe0fakejpeg"), "shelf.jpg")
    r = client.post(
        "/items/new",
        data={
            "title": "Wooden bookshelf",
            "description": "Sturdy 3-shelf unit, free to a good home.",
            "category": "furniture",
            "condition": "good",
            "item_type": "donation",
            "photo": photo,
        },
        follow_redirects=True,
    )
    assert r.status_code == 200, f"create item failed: {r.status_code}"
    assert b"Wooden bookshelf" in r.data, "item not on detail page"

    from extensions import db
    from models import Item

    item = Item.query.filter_by(title="Wooden bookshelf").first()
    assert item is not None, "item not in DB"
    assert item.photo_url is not None, "photo not saved"
    assert item.owner_id == 1, "owner not set"

    # 9. Browse shows the item
    r = client.get("/")
    assert b"Wooden bookshelf" in r.data, "item missing from browse"

    # 10. Search finds it, keyword miss does not
    r = client.get("/?q=bookshelf")
    assert b"Wooden bookshelf" in r.data, "search failed"
    r = client.get("/?q=zzznotfound")
    assert b"No items found" in r.data, "empty search state missing"

    # 11. Filter by category
    r = client.get("/?category=furniture")
    assert b"Wooden bookshelf" in r.data, "category filter failed"
    r = client.get("/?category=books")
    assert b"Wooden bookshelf" not in r.data, "category filter leaked item"

    # 12. Non-photo item works
    client.post(
        "/items/new",
        data={
            "title": "Board game",
            "description": "Family game night classic.",
            "category": "toys",
            "condition": "like_new",
            "item_type": "exchange",
        },
        follow_redirects=True,
    )
    r = client.get("/?type=exchange")
    assert b"Board game" in r.data, "type filter failed"

    # 13. Edit by owner works
    r = client.post(
        f"/items/{item.id}/edit",
        data={
            "title": "Wooden bookshelf (updated)",
            "description": "Now with free books included.",
            "category": "furniture",
            "condition": "good",
            "item_type": "donation",
        },
        follow_redirects=True,
    )
    assert b"Wooden bookshelf (updated)" in r.data, "edit failed"
    assert b"Listing updated" in r.data, "edit flash missing"

    # 14. Non-owner gets 403 on edit
    client.post("/auth/logout")
    client.post(
        "/auth/register",
        data={
            "username": "bob",
            "email": "bob@example.com",
            "password": "supersecret1",
            "confirm": "supersecret1",
        },
    )
    r = client.get(f"/items/{item.id}/edit")
    assert r.status_code == 403, f"non-owner edit allowed: {r.status_code}"

    # 15. Bob can view the item detail
    r = client.get(f"/items/{item.id}")
    assert r.status_code == 200
    assert b"Wooden bookshelf (updated)" in r.data

    # 16. Bob cannot delete alice's item
    r = client.post(f"/items/{item.id}/delete")
    assert r.status_code == 403, f"non-owner delete allowed: {r.status_code}"

    # 17. Owner can delete
    client.post("/auth/logout")
    client.post("/auth/login", data={"identifier": "alice", "password": "supersecret1"})
    r = client.post(f"/items/{item.id}/delete", follow_redirects=True)
    assert r.status_code == 200
    assert b"Listing deleted" in r.data, "delete flash missing"
    assert db.session.get(Item, item.id) is None, "item still in DB"

    # 18. Anonymous cannot post
    client.post("/auth/logout")
    r = client.get("/items/new", follow_redirects=False)
    assert r.status_code == 302, "anonymous access to new item not redirected"


def phase4_tests(client):
    from extensions import db
    from models import Item, ItemRequest, User

    def dave_id():
        return User.query.filter_by(username="dave").first().id

    # 19. Carol registers and posts an item
    client.post(
        "/auth/register",
        data={
            "username": "carol",
            "email": "carol@example.com",
            "password": "supersecret1",
            "confirm": "supersecret1",
        },
    )
    client.post(
        "/items/new",
        data={
            "title": "Spare monitor",
            "description": "24-inch LED monitor, works perfectly.",
            "category": "electronics",
            "condition": "good",
            "item_type": "donation",
        },
        follow_redirects=True,
    )
    item = Item.query.filter_by(title="Spare monitor").first()
    assert item is not None, "carol's item not created"

    # 20. Dave requests the item with a message
    client.post("/auth/logout")
    client.post(
        "/auth/register",
        data={
            "username": "dave",
            "email": "dave@example.com",
            "password": "supersecret1",
            "confirm": "supersecret1",
        },
    )
    r = client.post(
        f"/requests/new/{item.id}",
        data={"message": "Can pick up Saturday morning!"},
        follow_redirects=True,
    )
    assert b"Request sent" in r.data, "request flash missing"
    req = ItemRequest.query.filter_by(item_id=item.id, requester_id=dave_id()).first()
    assert req is not None, "request not in DB"
    assert req.message == "Can pick up Saturday morning!", "message not saved"

    # 21. Duplicate pending request blocked
    r = client.post(
        f"/requests/new/{item.id}",
        data={"message": "Second try"},
        follow_redirects=True,
    )
    assert b"already have a pending request" in r.data, "duplicate request allowed"

    # 22. Dave cannot accept his own request (not the owner)
    r = client.post(f"/requests/{req.id}/accept")
    assert r.status_code == 403, f"non-owner accept allowed: {r.status_code}"

    # 23. Dave cannot request his own item
    client.post(
        "/items/new",
        data={
            "title": "Dave's kettle",
            "description": "Barely used electric kettle.",
            "category": "kitchen",
            "condition": "like_new",
            "item_type": "exchange",
        },
        follow_redirects=True,
    )
    kettle = Item.query.filter_by(title="Dave's kettle").first()
    r = client.post(
        f"/requests/new/{kettle.id}",
        data={"message": "testing"},
        follow_redirects=True,
    )
    assert b"request your own item" in r.data, "self-request allowed"

    # 24. Carol sees the incoming request on her dashboard
    client.post("/auth/logout")
    client.post("/auth/login", data={"identifier": "carol", "password": "supersecret1"})
    r = client.get("/dashboard")
    assert b"Spare monitor" in r.data, "item missing from dashboard"
    assert b"dave" in r.data, "requester missing from dashboard"
    assert b"Can pick up Saturday morning" in r.data, "request message missing"

    # 25. Carol accepts — item becomes reserved, other pending auto-declined
    r = client.post(f"/requests/{req.id}/accept", follow_redirects=True)
    assert b"accepted" in r.data.lower(), "accept flash missing"
    assert db.session.get(Item, item.id).status == "reserved", "item not reserved"
    assert db.session.get(ItemRequest, req.id).status == "accepted", "request not accepted"

    # 26. Reserved item no longer in browse
    r = client.get("/")
    assert b"Spare monitor" not in r.data, "reserved item still in browse"

    # 27. New request on reserved item rejected
    client.post("/auth/logout")
    client.post("/auth/login", data={"identifier": "dave", "password": "supersecret1"})
    r = client.post(
        f"/requests/new/{item.id}",
        data={"message": "too late?"},
        follow_redirects=True,
    )
    assert b"no longer available" in r.data, "request on reserved item allowed"

    # 28. Decline flow: carol's second item, dave requests, carol declines
    client.post("/auth/logout")
    client.post("/auth/login", data={"identifier": "carol", "password": "supersecret1"})
    client.post(
        "/items/new",
        data={
            "title": "Plant cuttings",
            "description": "Pothos cuttings, rooted.",
            "category": "garden",
            "condition": "new",
            "item_type": "donation",
        },
        follow_redirects=True,
    )
    plant = Item.query.filter_by(title="Plant cuttings").first()

    client.post("/auth/logout")
    client.post("/auth/login", data={"identifier": "dave", "password": "supersecret1"})
    client.post(f"/requests/new/{plant.id}", data={"message": "pls"}, follow_redirects=True)
    plant_req = ItemRequest.query.filter_by(item_id=plant.id, requester_id=dave_id()).first()

    client.post("/auth/logout")
    client.post("/auth/login", data={"identifier": "carol", "password": "supersecret1"})
    client.post(f"/requests/{plant_req.id}/decline", follow_redirects=True)
    assert db.session.get(ItemRequest, plant_req.id).status == "declined", "decline failed"
    assert db.session.get(Item, plant.id).status == "available", "declined item should stay available"

    # 29. Dave's dashboard shows outgoing statuses
    client.post("/auth/logout")
    client.post("/auth/login", data={"identifier": "dave", "password": "supersecret1"})
    r = client.get("/dashboard")
    assert b"Spare monitor" in r.data, "outgoing item missing"
    assert b"accepted" in r.data, "accepted status missing"
    assert b"declined" in r.data, "declined status missing"

    # 30. Anonymous cannot request
    client.post("/auth/logout")
    r = client.post(f"/requests/new/{plant.id}", data={"message": "x"})
    assert r.status_code == 302, "anonymous request not redirected"


if __name__ == "__main__":
    main()
