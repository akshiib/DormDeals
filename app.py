import os
from dotenv import load_dotenv
from pymongo import MongoClient
import base64
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

load_dotenv()

# Load keys and db name
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')

# Set up connection with MongoDB
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
collection = db['items']   

# Constants for the upload folder and allowed upload extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Function checks if the image has extensions in ALLOWED EXTENSIONS -> png, jpg, jpeg
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


"""Function takes three params -> image_path (constructed image path from upload folder), image metadata
and user_data. User data includes first & last name, email, and condition. Function inserts all params in MONGODB"""
def insert_to_db(image_path, metadata, user_data):
    # Opens image in read binary mode
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
        encoded_image = base64.b64encode(image_data).decode('utf-8')

        first_name = user_data['first_name']
        last_name = user_data['last_name']
        full_name = (first_name.replace(" ", "")) + " " + (last_name.replace(" ",""))
        document = {
            'name':full_name,
            'email':user_data['email'],
            'condition':user_data['condition'],
            'image': encoded_image,
            'metadata': metadata
        }

        collection.insert_one(document)
        print(f"Uploaded {image_path} to MongoDB with metadata.")

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)        # Saving to the uploads folder

            metadata = {
                'description': request.form['description'],
                'tags': request.form['tags'].split(','),
                'upload_date': request.form['upload_date']
            }

            user_data = {
                'first_name':request.form['first'],
                'last_name':request.form['last'],
                'email':request.form['email'],
                'condition':request.form['condition']
            }

            insert_to_db(file_path, metadata, user_data)
            return 'File successfully uploaded'

    return render_template('upload.html')


@app.route('/download', methods=['GET'])
def download_file():
    if request.method == 'GET':
        #retrieve from mongodb 
        image_doc = collection.find_one()
        print(image_doc.keys())
        if image_doc:
            image_data = image_doc['image']
            image_metadata = image_doc['metadata']
            return render_template('display_image.html', image_data=image_data, image_metadata=image_metadata)  
        else:
            return "Image not found"
   
if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
