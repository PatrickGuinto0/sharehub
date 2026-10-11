from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from extensions import db
from models import CATEGORIES, CONDITIONS, ITEM_TYPES, User


class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=64)],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters."),
        ],
    )
    confirm = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")

    def validate_username(self, field):
        if User.query.filter(db.func.lower(User.username) == field.data.lower()).first():
            raise ValidationError("That username is already taken.")

    def validate_email(self, field):
        if User.query.filter(db.func.lower(User.email) == field.data.lower()).first():
            raise ValidationError("That email is already registered.")


class LoginForm(FlaskForm):
    identifier = StringField(
        "Username or Email",
        validators=[DataRequired()],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")


class ItemForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField(
        "Description",
        validators=[DataRequired(), Length(max=2000)],
    )
    category = SelectField("Category", choices=CATEGORIES, validators=[DataRequired()])
    condition = SelectField("Condition", choices=CONDITIONS, validators=[DataRequired()])
    item_type = SelectField("Listing type", choices=ITEM_TYPES, validators=[DataRequired()])
    photo = FileField(
        "Photo (optional)",
        validators=[
            FileAllowed(
                ["jpg", "jpeg", "png", "webp", "gif"],
                "Images only (jpg, png, webp, gif).",
            )
        ],
    )
    submit = SubmitField("Save listing")


class RequestForm(FlaskForm):
    message = TextAreaField(
        "Message (optional)",
        validators=[Length(max=500)],
        render_kw={"placeholder": "Tell the owner when you can pick it up…", "rows": 3},
    )
    submit = SubmitField("Send request")
