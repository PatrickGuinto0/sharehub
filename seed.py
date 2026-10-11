"""Seed the database with demo users, items, and requests.

Usage:
    python seed.py            # wipes users/items/requests and reseeds
    python seed.py --keep     # abort if any data already exists
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

from app import UPLOAD_FOLDER, create_app
from extensions import db
from models import Item, ItemRequest, User

CATEGORY_COLORS = {
    "furniture": "#8b6f47",
    "clothing": "#b0709c",
    "books": "#5b7f6e",
    "electronics": "#4a6fa5",
    "toys": "#c47a4a",
    "kitchen": "#7a8b5c",
    "sports": "#4f8a8b",
    "garden": "#6a994e",
    "other": "#8d8d8d",
}

DEMO_USERS = [
    ("alice", "alice@example.com"),
    ("bob", "bob@example.com"),
]

DEMO_ITEMS = [
    ("alice", "Wooden bookshelf", "Sturdy 3-shelf oak bookshelf. A few scuffs on top but very solid. Pickup near the community center.", "furniture", "good", "donation"),
    ("alice", "Road bike", "2018 hybrid road bike, size M, recently serviced. Looking to exchange for a decent camera or running shoes.", "sports", "like_new", "exchange"),
    ("alice", "Box of paperbacks", "Around 20 mixed-genre paperbacks, all readable. Free to anyone who wants them!", "books", "good", "donation"),
    ("alice", "HDMI monitor", "24-inch 1080p monitor with stand and cable. Happy to swap for a tablet or espresso maker.", "electronics", "good", "exchange"),
    ("alice", "Pothos cuttings", "Rooted pothos cuttings in water jars. Bring a small pot and soil if you can.", "garden", "new", "donation"),
    ("bob", "Desk lamp", "Adjustable LED desk lamp with warm/cool modes. Works perfectly, upgrading to a bigger one.", "electronics", "like_new", "donation"),
    ("bob", "Chess set", "Classic wooden chess set with felted pieces. Looking to exchange for board games or puzzles.", "toys", "like_new", "exchange"),
    ("bob", "Cooking pots", "Set of 3 non-stick pots, one has a small scratch inside. Still cooks like a charm.", "kitchen", "fair", "donation"),
    ("bob", "Winter coats", "Two adult winter coats (L and XL), warm and clean. Could use a new home before winter.", "clothing", "good", "donation"),
    ("bob", "Board game bundle", "Three family board games — boxes slightly worn but all pieces complete. First come, first served.", "toys", "good", "donation"),
]

DEMO_REQUESTS = [
    ("bob", "Wooden bookshelf", "This would be perfect for my study! I can pick it up tomorrow evening."),
    ("alice", "Desk lamp", "Would love this for late-night reading. Happy to swing by this weekend."),
    ("alice", "Chess set", "My kids have been wanting to learn chess — would this work for beginners?"),
]


def write_placeholder_image(title, category):
    color = CATEGORY_COLORS.get(category, CATEGORY_COLORS["other"])
    initial = escape(title[0].upper())
    safe_title = escape(title)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <rect width="800" height="600" fill="{color}"/>
  <circle cx="400" cy="250" r="110" fill="rgba(255,255,255,0.22)"/>
  <text x="400" y="290" font-family="Arial, sans-serif" font-size="96" font-weight="bold"
        fill="#ffffff" text-anchor="middle">{initial}</text>
  <text x="400" y="450" font-family="Arial, sans-serif" font-size="30"
        fill="rgba(255,255,255,0.92)" text-anchor="middle">{safe_title}</text>
  <text x="400" y="500" font-family="Arial, sans-serif" font-size="18"
        fill="rgba(255,255,255,0.7)" text-anchor="middle">ShareHub community item</text>
</svg>"""
    filename = f"seed_{category}_{abs(hash(title)) % 10**8}.svg"
    with open(os.path.join(UPLOAD_FOLDER, filename), "w", encoding="utf-8") as f:
        f.write(svg)
    return filename


def main():
    keep = "--keep" in sys.argv
    app = create_app()

    with app.app_context():
        if keep and (User.query.count() or Item.query.count() or ItemRequest.query.count()):
            print("Data already exists — nothing seeded (use without --keep to reseed).")
            return

        ItemRequest.query.delete()
        Item.query.delete()
        User.query.delete()
        db.session.commit()

        now = datetime.now(timezone.utc)
        users = {}
        for username, email in DEMO_USERS:
            user = User(username=username, email=email)
            user.set_password("sharehub123")
            db.session.add(user)
            users[username] = user
        db.session.flush()

        for i, (owner, title, description, category, condition, item_type) in enumerate(DEMO_ITEMS):
            item = Item(
                title=title,
                description=description,
                category=category,
                condition=condition,
                item_type=item_type,
                photo_url=write_placeholder_image(title, category),
                owner_id=users[owner].id,
                created_at=now - timedelta(hours=len(DEMO_ITEMS) - i),
            )
            db.session.add(item)
        db.session.flush()

        for requester, item_title, message in DEMO_REQUESTS:
            item = Item.query.filter_by(title=item_title).first()
            db.session.add(
                ItemRequest(
                    item_id=item.id,
                    requester_id=users[requester].id,
                    message=message,
                    created_at=now - timedelta(hours=2),
                )
            )

        db.session.commit()
        print(f"Seeded {len(DEMO_USERS)} users, {len(DEMO_ITEMS)} items, {len(DEMO_REQUESTS)} requests.")
        print("Demo login — username: alice (or bob) · password: sharehub123")


if __name__ == "__main__":
    main()
