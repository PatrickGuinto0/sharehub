from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from forms import LoginForm, RegisterForm
from models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f"Welcome to ShareHub, {user.username}! Your account is ready.", "success")
        return redirect(url_for("main.index"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data.strip()
        user = User.query.filter(
            db.or_(
                db.func.lower(User.username) == identifier.lower(),
                db.func.lower(User.email) == identifier.lower(),
            )
        ).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username/email or password.", "danger")
            return redirect(url_for("auth.login"))
        login_user(user, remember=form.remember.data)
        flash(f"Logged in as {user.username}.", "success")
        return redirect(url_for("main.index"))
    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
