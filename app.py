import os
from flask import Flask, render_template, request, jsonify
from processor import process_base64_frames

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Serve static files from 'public' so local Flask and Vercel route URLs consistently
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, 'public'),
    static_url_path=''
)

# Set max payload size to 4.5MB to stay within Vercel's serverless limit
app.config['MAX_CONTENT_LENGTH'] = int(4.5 * 1024 * 1024)

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "Payload too large. Request exceeds the 4.5MB serverless limit."}), 413

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_strip', methods=['POST'])
def process_strip():
    # Defensive check on content-length
    if request.content_length and request.content_length > app.config['MAX_CONTENT_LENGTH']:
        return jsonify({"error": "Payload too large. Request exceeds the 4.5MB serverless limit."}), 413

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON or payload exceeds size limit."}), 400

    frames = data.get('frames')
    layout = data.get('layout', 'vertical')
    mode = data.get('mode', 'standard')
    previous_strip = data.get('previous_strip', None)
    
    if not frames or len(frames) != 3:
        return jsonify({"error": "Invalid number of frames provided. Exactly 3 frames required."}), 400
        
    try:
        strip_b64 = process_base64_frames(frames, layout=layout, mode=mode, prev_strip_b64=previous_strip)
        return jsonify({"result_image": strip_b64})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Start the local server
    app.run(debug=True, port=5000)
