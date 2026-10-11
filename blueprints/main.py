from flask import Blueprint, render_template, request

from extensions import db
from models import (
    CATEGORIES,
    CATEGORY_LABELS,
    CONDITIONS,
    CONDITION_LABELS,
    ITEM_TYPES,
    ITEM_TYPE_LABELS,
    Item,
)

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    query = Item.query.filter_by(status="available")

    q = (request.args.get("q") or "").strip()
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Item.title.ilike(like), Item.description.ilike(like)))

    category = request.args.get("category", "")
    if category:
        query = query.filter_by(category=category)

    condition = request.args.get("condition", "")
    if condition:
        query = query.filter_by(condition=condition)

    item_type = request.args.get("type", "")
    if item_type:
        query = query.filter_by(item_type=item_type)

    items = query.order_by(Item.created_at.desc()).all()

    return render_template(
        "index.html",
        items=items,
        q=q,
        category=category,
        condition=condition,
        item_type=item_type,
        categories=CATEGORIES,
        conditions=CONDITIONS,
        item_types=ITEM_TYPES,
        category_labels=CATEGORY_LABELS,
        condition_labels=CONDITION_LABELS,
        item_type_labels=ITEM_TYPE_LABELS,
    )
