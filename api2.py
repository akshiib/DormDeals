import os
import requests
import json

# URL for the API request
url = "https://data.opendatasoft.com/api/explore/v2.1/catalog/datasets/us-colleges-and-universities@public/records?select=%2A"

# API key and parameters
params = {
    'apikey': os.getenv("COLLEGE_API"),
}

# Make the GET request to the API
resp = requests.get(url, params=params)
data = resp.json()
print(data.keys())
# Extract the records from the response
records = data['results']
count = 0
# Open the file in write mode
print(len(records))

with open("again.txt","w") as filename:
    for record in records:
        filename.write(record.get('name') + "\n")