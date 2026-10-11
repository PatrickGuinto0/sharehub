import os
import secrets

from flask import Flask, flash, redirect, render_template, send_from_directory, url_for

from extensions import csrf, db, login_manager

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB


def get_secret_key():
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    key_file = os.path.join(BASE_DIR, ".secret_key")
    if os.path.exists(key_file):
        with open(key_file) as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(key_file, "w") as f:
        f.write(key)
    return key


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = get_secret_key()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'sharehub.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    if config_overrides:
        app.config.update(config_overrides)

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from blueprints.auth import bp as auth_bp
    from blueprints.dashboard import bp as dashboard_bp
    from blueprints.items import bp as items_bp
    from blueprints.main import bp as main_bp
    from blueprints.requests import bp as requests_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(requests_bp)

    @app.route("/uploads/<path:filename>")
    def uploads(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(413)
    def too_large(error):
        flash("That photo is too large — the maximum size is 5 MB.", "warning")
        return redirect(url_for("main.index"))

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
