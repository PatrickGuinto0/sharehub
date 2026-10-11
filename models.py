from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db

CATEGORIES = [
    ("furniture", "Furniture"),
    ("clothing", "Clothing"),
    ("books", "Books"),
    ("electronics", "Electronics"),
    ("toys", "Toys & Games"),
    ("kitchen", "Kitchen"),
    ("sports", "Sports & Outdoors"),
    ("garden", "Garden"),
    ("other", "Other"),
]

CONDITIONS = [
    ("new", "New"),
    ("like_new", "Like new"),
    ("good", "Good"),
    ("fair", "Fair"),
    ("worn", "Worn but usable"),
]

ITEM_TYPES = [
    ("donation", "Donation"),
    ("exchange", "Exchange"),
]

CATEGORY_LABELS = dict(CATEGORIES)
CONDITION_LABELS = dict(CONDITIONS)
ITEM_TYPE_LABELS = dict(ITEM_TYPES)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    condition = db.Column(db.String(20), nullable=False)
    item_type = db.Column(db.String(10), nullable=False)  # donation | exchange
    photo_url = db.Column(db.String(200))  # filename inside uploads/
    status = db.Column(db.String(12), nullable=False, default="available")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    owner = db.relationship("User", backref=db.backref("items", lazy="dynamic"))

    def __repr__(self):
        return f"<Item {self.title!r}>"


class ItemRequest(db.Model):
    __tablename__ = "requests"

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    status = db.Column(db.String(12), nullable=False, default="pending")  # pending | accepted | declined
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    item = db.relationship("Item", backref=db.backref("requests", lazy="dynamic"))
    requester = db.relationship(
        "User",
        foreign_keys=[requester_id],
        backref=db.backref("outgoing_requests", lazy="dynamic"),
    )

    def __repr__(self):
        return f"<ItemRequest {self.id} item={self.item_id} requester={self.requester_id} {self.status}>"
