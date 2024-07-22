import json

# Load the JSON data from a file
with open('us-colleges-and-universities.json', 'r') as file:
    data = json.load(file)

# Extract the names of the colleges and universities
records = [(record.get('name')).lower().title() for record in data]

# Write the names to a new JSON file
with open("colleges.json", 'w') as filename:
    json.dump(records, filename, indent=4)
