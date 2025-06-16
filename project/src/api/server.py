import os
import sys
import json
from flask import Flask, request, Response, jsonify
from flask_cors import CORS

# Add the parent directory to the path to import rag module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rag_2 import main as rag_main
except ImportError:
    print("Error: Could not import rag module. Make sure rag.py is in the correct location.")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

@app.route('/api/reform-description', methods=['POST'])
def reform_description():
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({'error': 'No prompt provided'}), 400
        
        prompt = data['prompt']
        use_streaming = data.get('use_streaming', False)
        
        if use_streaming:
            def generate():
                try:
                    # Get streaming response from rag module
                    stream_generator = rag_main(prompt, use_streaming=True)
                    
                    for chunk in stream_generator:
                        if chunk.strip():
                            yield f"data: {json.dumps({'content': chunk})}\n\n"
                    
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return Response(generate(), mimetype='text/plain')
        else:
            # Non-streaming response
            result = rag_main(prompt, use_streaming=False)
            return jsonify({'content': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)