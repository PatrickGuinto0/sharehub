from flask import Blueprint, render_template
from flask_login import current_user, login_required

from models import CATEGORY_LABELS, ITEM_TYPE_LABELS, Item, ItemRequest

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.route("/", strict_slashes=False)
@login_required
def index():
    my_items = (
        Item.query.filter_by(owner_id=current_user.id)
        .order_by(Item.created_at.desc())
        .all()
    )
    incoming = (
        ItemRequest.query.join(Item)
        .filter(Item.owner_id == current_user.id)
        .order_by(ItemRequest.created_at.desc())
        .all()
    )
    outgoing = (
        ItemRequest.query.filter_by(requester_id=current_user.id)
        .order_by(ItemRequest.created_at.desc())
        .all()
    )
    return render_template(
        "dashboard.html",
        my_items=my_items,
        incoming=incoming,
        outgoing=outgoing,
        category_labels=CATEGORY_LABELS,
        item_type_labels=ITEM_TYPE_LABELS,
    )
