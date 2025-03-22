from flask import Flask, render_template, request, jsonify
from main import process_question

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    language = data.get('language', 'en')  # Get language preference
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    try:
        result = process_question(question)
        return jsonify({'summary': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 