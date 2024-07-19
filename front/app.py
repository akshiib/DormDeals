import os
from db import db
from models import User
from collections import defaultdict
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from forms import RegistrationForm, LoginForm


# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

# Initialize SQLAlchemy
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Create tables if they don't exist
with app.app_context():
    db.create_all()

@login_manager.user_loader

def load_user(user_id):
    return User.query.get(int(user_id))


# Route for home
@app.route('/')
def home():
    return render_template('home.html', listings=mock_listings)

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('categories'))
    
    # Sets up form and functionality
    form = LoginForm()
    username_error = None
    password_error = None

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('categories'))
        
        # Input validation to inform user of input invalid
        else:
            if not user:
                username_error = 'Invalid username'
            else:
                password_error = 'Invalid password'

    return render_template('login.html', title='Login', form=form, 
                           username_error=username_error,
                           password_error=password_error)


# Route for register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('This email address is already registered. ' +
                  'Please <a href="{}">login</a> instead.'.format(url_for('login')), 'danger')
            return redirect(url_for('login')) 
        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()  
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/buy')
@login_required
def buy():
    print("buy")

@app.route('/sell')
@login_required
def sell():
    print("sell")

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    print("chat")
    return render_template('chat.html')

# Route for categories
@app.route('/categories')
@login_required
def categories():
    categories = {
        "bed & bath": url_for('static', filename='images/bed-bath.png'),
        "decorations": url_for('static', filename='images/decor.png'),
        "laundry & cleaning": url_for('static', filename='images/laund-clean.png'),
        "organization & storage": url_for('static', filename='images/stor-org.png'),
        "appliances": url_for('static', filename='images/appliance.png'),
        "studysupplies": url_for('static', filename='images/studysup.png')
    }
    return render_template('categories.html', categories=categories)

# Route for category-specific listings
@app.route('/<category>/listings')
@login_required
def listings(category):
    # categories: bed + bath, decorations, laundry + cleaning, organization + storage, appliances, study supplies
    filtered_listings = [listing for listing in mock_listings if listing['category'].replace(" ", "").lower() == category.replace(" ", "").lower()]
    return render_template('listings.html', category=category, listings=filtered_listings)


# Route for logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run()


