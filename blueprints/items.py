import os
import uuid

from flask import Blueprint, abort, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from extensions import db
from forms import ItemForm, RequestForm
from models import CATEGORY_LABELS, CONDITION_LABELS, ITEM_TYPE_LABELS, Item

bp = Blueprint("items", __name__, url_prefix="/items")


def save_photo(file):
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    return filename


def delete_photo(filename):
    if not filename:
        return
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(path):
        os.remove(path)


def get_owned_item_or_403(item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404)
    if item.owner_id != current_user.id:
        abort(403)
    return item


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = ItemForm()
    if form.validate_on_submit():
        item = Item(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            category=form.category.data,
            condition=form.condition.data,
            item_type=form.item_type.data,
            owner_id=current_user.id,
        )
        if form.photo.data and form.photo.data.filename:
            item.photo_url = save_photo(form.photo.data)
        db.session.add(item)
        db.session.commit()
        flash("Your item has been posted!", "success")
        return redirect(url_for("items.detail", item_id=item.id))
    return render_template("items/form.html", form=form, legend="Post an item")


@bp.route("/<int:item_id>")
def detail(item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404)
    return render_template(
        "items/detail.html",
        item=item,
        request_form=RequestForm(),
        category_labels=CATEGORY_LABELS,
        condition_labels=CONDITION_LABELS,
        item_type_labels=ITEM_TYPE_LABELS,
    )


@bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit(item_id):
    item = get_owned_item_or_403(item_id)
    form = ItemForm(obj=item)
    if form.validate_on_submit():
        old_photo = item.photo_url
        item.title = form.title.data.strip()
        item.description = form.description.data.strip()
        item.category = form.category.data
        item.condition = form.condition.data
        item.item_type = form.item_type.data
        if form.photo.data and form.photo.data.filename:
            item.photo_url = save_photo(form.photo.data)
            delete_photo(old_photo)
        db.session.commit()
        flash("Listing updated.", "success")
        return redirect(url_for("items.detail", item_id=item.id))
    return render_template("items/form.html", form=form, legend="Edit listing", item=item)


@bp.route("/<int:item_id>/delete", methods=["POST"])
@login_required
def delete(item_id):
    item = get_owned_item_or_403(item_id)
    delete_photo(item.photo_url)
    db.session.delete(item)
    db.session.commit()
    flash("Listing deleted.", "info")
    return redirect(url_for("main.index"))
