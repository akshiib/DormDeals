import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient
import base64
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

load_dotenv()

# Load keys and db name
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')
CHAT_DB = os.getenv('DB_NAME')
# Set up connection with MongoDB
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
collection = db['items']   
db2 = client[CHAT_DB]
chat_collection = db['messages']


# Constants for the upload folder and allowed upload extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

"""
Function returns a list containing chats for specified user in parameter. For example, if user is speaking to 3 people,
list of length 3 will be returned. Each element of the list will be a dict storing 2 keys. 
Key 1: participants array (length 2 - who the chat is between)
Key 2: messages (sorted list of messages with sender, message, timestamp)
"""
def find_chats_with_user(username):
    query = { "participants": username }        # return chats where participants array contains the param user
    chats = list(collection.find(query))
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


"""
Function that displays the form, saves the uploaded image in the upload folder, and send all information
to be stored in MONGODB
"""
@app.route('/', methods=['GET', 'POST'])
def upload_file():
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
            return 'File successfully uploaded'

        
    return render_template('upload.html', colleges=colleges)


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
   
   
if __name__ == "__main__":
    # If upload folder doesn't exist, create it in the same dir
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
    # retrieve_college_cursors()



