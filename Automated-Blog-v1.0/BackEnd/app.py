from flask import Flask, request, jsonify
from flask_cors import CORS
from urllib.parse import parse_qs


app = Flask(__name__)
CORS(app)


@app.route('/process-form', methods=['POST'])
def process_form():
    print("Hello World")
    if request.method == 'POST':
        form_data = request.form.get('data')  # Retrieve form data from 'data' field
        parsed_data = parse_qs(form_data)  # Parse the form data into a dictionary

        # Access the name and email values from the parsed data
        name = parsed_data.get('name', [''])[0]
        email = parsed_data.get('email', [''])[0]

        # Process the form data as needed (e.g., store in a database)
        
        # Send a response back to the client
        response_data = {'name': name, 'email': email}
        print(name)
        print(email)
        print(request.form)
        return jsonify(response_data)
    else:
        return "Method Not Allowed", 405

if __name__ == '__main__':
    app.run(port=5000, debug=True)
