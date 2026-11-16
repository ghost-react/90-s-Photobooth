import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from processor import process_base64_frames

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure Flask with static_folder pointing to 'public' (or 'static')
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

@app.route('/style.css')
def serve_css():
    """Explicitly serve style.css from public, static, or base directory."""
    for folder in ['public', 'static', '']:
        dir_path = os.path.join(BASE_DIR, folder) if folder else BASE_DIR
        file_path = os.path.join(dir_path, 'style.css')
        if os.path.exists(file_path):
            return send_from_directory(dir_path, 'style.css', mimetype='text/css')
    return "/* style.css */", 200, {'Content-Type': 'text/css'}

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Explicitly serve audio and font assets."""
    for folder in [
        os.path.join('public', 'assets'),
        os.path.join('static', 'assets'),
        'assets'
    ]:
        dir_path = os.path.join(BASE_DIR, folder)
        file_path = os.path.join(dir_path, filename)
        if os.path.exists(file_path):
            return send_from_directory(dir_path, filename)
    return jsonify({"error": f"Asset '{filename}' not found."}), 404

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
