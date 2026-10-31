from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required.'),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters.')
    ])
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.'),
        Length(min=3, max=50, message='Username must be between 3 and 50 characters.')
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please provide a valid email address.'),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data.strip()).first()
        if user:
            raise ValidationError('This username is already taken. Please choose another.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.strip().lower()).first()
        if user:
            raise ValidationError('An account with this email already exists.')


class LoginForm(FlaskForm):
    username_or_email = StringField('Username or Email', validators=[
        DataRequired(message='Please enter your username or email.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter your password.')
    ])
    submit = SubmitField('Sign In')