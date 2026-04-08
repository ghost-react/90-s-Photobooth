from flask import Flask, render_template, request, jsonify
from processor import process_base64_frames

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_strip', methods=['POST'])
def process_strip():
    data = request.json
    frames = data.get('frames')
    layout = data.get('layout', 'vertical')
    mode = data.get('mode', 'standard')
    previous_strip = data.get('previous_strip', None)
    
    if not frames or len(frames) != 3:
        return jsonify({"error": "Invalid number of frames provided."}), 400
        
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
