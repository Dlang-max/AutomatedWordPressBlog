from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/process-form', methods=['POST'])
def process_form():
    if request.method == 'POST':
        topic = request.form.get('topic')
        title = request.form.get('title')
        links = request.form.get('links')
        keywords_and_phrases = request.form.get('keywords-and-phrases')
        preview_image = request.form.get('preview-image')

        # Process the form data as needed (e.g., store in a database)
        print(topic)
        print(title)
        print(links)
        print(keywords_and_phrases)
        print(preview_image)

        response_data = { 'response': 'Form data received successfully.' }
        # Send a response back to the client
        return jsonify(response_data)
    else:
        return "Method Not Allowed", 405

if __name__ == '__main__':
    app.run(port=5000, debug=True)
