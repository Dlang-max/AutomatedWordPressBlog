from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/process-form', methods=['POST'])
def process_form():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        # Process the form data as needed (e.g., store in a database)
        
        # Send a response back to the client
        response_data = {'name': name, 'email': email}
        return jsonify(response_data)
    else:
        return "Method Not Allowed", 405

if __name__ == '__main__':
    app.run(port=5000, debug=True)
