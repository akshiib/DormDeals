import os
import sys
import json
from dotenv import load_dotenv
from pymongo import MongoClient
import base64
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

from front.db import db
from front.models import User
from front.forms import RegistrationForm, LoginForm, SellForm

from collections import defaultdict
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
from flask_login import LoginManager, current_user, login_user, logout_user, login_required


load_dotenv()

# Load keys and db name
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')
CHAT_DB = os.getenv('DB_NAME')

# Set up connection with MongoDB
client = MongoClient(MONGODB_URI)
mongo_db_1 = client[MONGODB_DB]
collection = mongo_db_1['items']   
mongo_db_2 = client[CHAT_DB]
chat_collection = mongo_db_2['messages']


# Constants for the upload folder and allowed upload extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Create tables if they don't exist
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


"""
Functin loads the listings for the current user's college and writes into
file listings.json
"""
def retrieve_user_college():
    user_college = "University Of Maryland-College Park"#current_user.college
    cursor = collection.find({"college":user_college})
    # entries = list(cursor)
    entries = []
    for entry in cursor:
        entry["_id"] = str(entry["_id"])  # Convert ObjectId to string
        entries.append(entry)
    
    with open("listings.json", "w") as file:
        json.dump(entries, file, indent=4)


# Route for home
@app.route('/')
def home():
    retrieve_user_college()
    with open("listings.json", "r") as file:
        listings = json.load(file)
    mock_listings = []
    for i in range(9):
        mock_listings.append(listings[i])
    return render_template('home.html', listings=mock_listings)


# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('categories'))
    
    """
    Check if the curr user is in the chat db after clicking on chat w seller
    If user is checking on a seller listing, check if seller is in db
    if not, create a chat
    if they are, retrieve old data
    """
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
    # Loading the list of 6k colleges in colleges.json
    with open('colleges.json', 'r') as file:
        colleges = json.load(file)

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
    return render_template('register.html', title='Register', form=form, colleges=colleges)

"""
Function returns a list containing chats for specified user in parameter. For example, if user is speaking to 3 people,
list of length 3 will be returned. Each element of the list will be a dict storing 2 keys. 
Key 1: participants array (length 2 - who the chat is between)
Key 2: messages (sorted list of messages with sender, message, timestamp)
"""
@app.route('/<seller>/chat') 
def find_chats_with_user(seller):
    user = current_user.username
    participants = [user, seller]
    participants.sort()
    query = { "participants": participants }        # return chats where participants array contains the param user
    chats = list(chat_collection.find(query))

    # render chat(chats=chats)
    return chats

"""
Function returns a dictionary. A cursor is a pymongo object which can be 
iterated over to retrieve entries from the database. The key in the dict is the college, and the value is 
the cursor associated with it.
"""
def retrieve_college_cursors():    
    # Find all distinct colleges
    distinct_colleges = collection.distinct('college')
    college_cursors = {}

    # Store the college name as the key, and associated cursor as value
    for college in distinct_colleges:
        cursor = collection.find({'college': college})
        college_cursors[college] = cursor

    return college_cursors


# Function checks if the image has extensions in ALLOWED EXTENSIONS -> png, jpg, jpeg
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


"""
Function takes three params -> image_path (constructed image path from upload folder), image metadata
and user_data. User data includes first & last name, email, and condition. Function inserts all params in MONGODB
"""
def insert_to_db(image_path, metadata, user_data):
    # Opens image in read binary mode
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
        encoded_image = base64.b64encode(image_data).decode('utf-8')

        first_name = user_data['first_name']
        last_name = user_data['last_name']
        full_name = (first_name.replace(" ", "")) + " " + (last_name.replace(" ",""))
        document = {
            'name':full_name,   # Person Name
            'email':user_data['email'],
            'item':user_data['item'],   # Item Name
            'condition':user_data['condition'],
            'category':user_data['category'],
            'price':user_data['price'],
            'college':user_data['college'],
            'image': encoded_image,
            'metadata': metadata,
        }

        collection.insert_one(document)
        print(f"Uploaded {image_path} to MongoDB with metadata.")

@app.route('/buy')
@login_required
def buy():
    print("buy")


@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    return render_template('chat.html')

# Route for categories
@app.route('/categories')
@login_required
def categories():
    categories = {
        "bed&bath": url_for('static', filename='images/bed-bath.png'),
        "decorations": url_for('static', filename='images/decor.png'),
        "laundry&cleaning": url_for('static', filename='images/laund-clean.png'),
        "organization&storage": url_for('static', filename='images/stor-org.png'),
        "appliances": url_for('static', filename='images/appliance.png'),
        "study-supplies": url_for('static', filename='images/studysup.png')
    }
    return render_template('categories.html', categories=categories)

"""
Function that displays the form, saves the uploaded image in the upload folder, and send all information
to be stored in MONGODB
"""
@app.route('/sell', methods=['GET', 'POST'])
def sell():

    # Loading the list of 6k colleges in colleges.json
    with open('colleges.json', 'r') as file:
        colleges = json.load(file)

    # When upload button is clicked (form is submitted)
    if request.method == 'POST':
        file = request.files['file']

        # If file has the correct extension, sanitize the file name save the image in the upload folder
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)        # Saving to the uploads folder

            # Extracting other data from form 
            metadata = {
                'description': request.form['description'],
                'tags': request.form['tags'].split(','),
                'upload_date': request.form['upload_date']
            }

            user_data = {
                'first_name':request.form['first'],
                'last_name':request.form['last'],
                'email':request.form['email'],
                'condition':request.form['condition'],
                'category':request.form['category'],
                'price':request.form['price'],
                'college':request.form['college'],
                'item':request.form['item'],
            }

            insert_to_db(file_path, metadata, user_data)
            return render_template('confirm.html')

        
    return render_template('sell.html', colleges=colleges)


"""
Function retrieves data from MONGODB and displays the first entry's image and metadata
"""
@app.route('/download', methods=['GET'])
def download_file():
    if request.method == 'GET':
        # Retrieve the first entry
        doc = collection.find_one()
        
        # Display Image & Metadata
        if doc:
            name = doc['name']
            email = doc['email']
            price = doc['price']
            category = doc['category']
            condition = doc['condition']
            image_data = doc['image']
            image_metadata = doc['metadata']
            return render_template('display_image.html', image_data=image_data, image_metadata=image_metadata, price=price, category=category, condition=condition, name=name, email=email)  
        else:
            return "Not found"
   
@app.route('/<category>/listings') 
@login_required 
def listings(category): 
    json_file_path = "listings.json"
    with open(json_file_path, "r") as file: 
          listings = json.load(file) 
    # filtered_listings = [listing for listing in listings if listing['category'] == category] 

    filtered = defaultdict(list)
    for listing in listings:
        filtered[listing['category']].append(listing)   

    categories = [
        "bed&bath",
        "decorations",
        "laundry&cleaning",
        "organization&storage",
        "appliances",
        "study-supplies"
    ]

    for current in categories:
        if category == current:
            return render_template('listings.html', category=category, listings=filtered[category])
    


# Route for logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    # If upload folder doesn't exist, create it in the same dir
    #retrieve_user_college()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)

    


