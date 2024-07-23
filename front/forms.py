from flask import url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DecimalField, IntegerField, FileField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    college = StringField('College', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            login_link = url_for('login')
            raise ValidationError(f'That email is already in use. Please choose a different one or login <a href="{login_link}">here</a>.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class SellForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    item_name = StringField('Item Name', validators=[DataRequired()])
    condition = SelectField('Condition', choices=[('worn', 'Worn'), ('used', 'Used, but good'), ('unused', 'Unused')], validators=[DataRequired()])
    category = SelectField('Category', choices=[('appliances', 'Appliances'), ('study supplies', 'Study Supplies'), ('organization & storage', 'Organization & Storage'), ('laundry & cleaning', 'Laundry & Cleaning'), ('decoration', 'Decoration'), ('bed & bath', 'Bed & Bath')], validators=[DataRequired()])
    college = StringField('College', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired()])
    file = FileField('Image', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    tags = StringField('Tags', validators=[DataRequired()])
    upload_date = DateField('Upload Date', format='%Y-%m-%d', validators=[DataRequired()])

    
