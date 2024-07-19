import json

# Load the JSON data from a file
with open('us-colleges-and-universities.json', 'r') as file:
    data = json.load(file)

# Print the names from the parsed data
for record in data:
    print(record.get('name'))
