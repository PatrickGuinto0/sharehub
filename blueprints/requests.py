from flask import Blueprint, abort, flash, redirect, url_for
from flask_login import current_user, login_required

from extensions import db
from forms import RequestForm
from models import Item, ItemRequest

bp = Blueprint("requests", __name__, url_prefix="/requests")


def get_pending_request_or_403(request_id):
    req = db.session.get(ItemRequest, request_id)
    if req is None:
        abort(404)
    if req.item.owner_id != current_user.id:
        abort(403)
    return req


@bp.route("/new/<int:item_id>", methods=["POST"])
@login_required
def new(item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404)

    form = RequestForm()
    if not form.validate_on_submit():
        flash("Invalid request.", "danger")
        return redirect(url_for("items.detail", item_id=item.id))

    if item.owner_id == current_user.id:
        flash("You can't request your own item.", "warning")
        return redirect(url_for("items.detail", item_id=item.id))

    if item.status != "available":
        flash("This item is no longer available.", "warning")
        return redirect(url_for("items.detail", item_id=item.id))

    existing = ItemRequest.query.filter_by(
        item_id=item.id, requester_id=current_user.id, status="pending"
    ).first()
    if existing:
        flash("You already have a pending request for this item.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    req = ItemRequest(
        item_id=item.id,
        requester_id=current_user.id,
        message=(form.message.data or "").strip() or None,
    )
    db.session.add(req)
    db.session.commit()
    flash(f"Request sent for “{item.title}”! The owner will get back to you.", "success")
    return redirect(url_for("items.detail", item_id=item.id))


@bp.route("/<int:request_id>/accept", methods=["POST"])
@login_required
def accept(request_id):
    req = get_pending_request_or_403(request_id)
    if req.status != "pending":
        flash("This request has already been handled.", "info")
        return redirect(url_for("dashboard.index"))

    req.status = "accepted"
    req.item.status = "reserved"
    ItemRequest.query.filter(
        ItemRequest.id != req.id,
        ItemRequest.item_id == req.item_id,
        ItemRequest.status == "pending",
    ).update({"status": "declined"})
    db.session.commit()
    flash(
        f"Request from {req.requester.username} accepted — “{req.item.title}” is now reserved.",
        "success",
    )
    return redirect(url_for("dashboard.index"))


@bp.route("/<int:request_id>/decline", methods=["POST"])
@login_required
def decline(request_id):
    req = get_pending_request_or_403(request_id)
    if req.status != "pending":
        flash("This request has already been handled.", "info")
        return redirect(url_for("dashboard.index"))

    req.status = "declined"
    db.session.commit()
    flash(f"Request from {req.requester.username} declined.", "info")
    return redirect(url_for("dashboard.index"))
