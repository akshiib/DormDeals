from flask import url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DecimalField, IntegerField, FileField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from .models import User

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

class SellerForm(FlaskForm):
    item_name = StringField('Item Name', validators=[DataRequired(), Length(max=100)])
    price = DecimalField('Price ($)', validators=[DataRequired(), NumberRange(min=0)], places=2)
    years_used = IntegerField('Number of Years Used', validators=[DataRequired(), NumberRange(min=0, max=10)])
    image = FileField('Image', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('decor', 'Decor'), 
        ('laundry_cleaning', 'Laundry/Cleaning Essentials'), 
        ('organization_storage', 'Organization/Storage'), 
        ('appliances', 'Appliances'), 
        ('study_supplies', 'Study Supplies'), 
        ('bed_bath', 'Bed and Bath')
    ], validators=[DataRequired()])
    submit = SubmitField('Sell Item')

    
