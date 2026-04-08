import os
import urllib.request
import wave
import struct
import math
import random

os.makedirs('assets', exist_ok=True)

# 1. Download Mock Fonts
fonts = {
    'CourierPrime-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/courierprime/CourierPrime-Regular.ttf',
    # A generic digital-style font available on github
    'Digital-7.ttf': 'https://github.com/keshikan/DSEG/raw/master/fonts/DSEG7-Classic/DSEG7Classic-Regular.ttf'
}

for font_name, url in fonts.items():
    font_path = os.path.join('assets', font_name)
    if not os.path.exists(font_path):
        try:
            print(f"Downloading {font_name}...")
            urllib.request.urlretrieve(url, font_path)
            if font_name == 'Digital-7.ttf':
                print("Note: Downloaded DSEG7 as a mock for Digital-7.")
        except Exception as e:
            print(f"Failed to download {font_name}: {e}")

# 2. Generate Mock Audio
def generate_wav(filename, duration, is_noise=False, freq=440.0):
    sample_rate = 44100
    n_samples = int(duration * sample_rate)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(n_samples):
            if is_noise:
                # White noise for "shutter crash" or "mechanical"
                value = int(random.uniform(-32767, 32767))
            else:
                # Low freq buzz for processing
                value = int(32767.0 * math.sin(2.0 * math.pi * freq * (i / float(sample_rate))))
            data = struct.pack('<h', value)
            wav_file.writeframesraw(data)

shutter_path = os.path.join('assets', 'shutter.wav')
whirr_path = os.path.join('assets', 'mechanical_whirr.wav')

if not os.path.exists(shutter_path):
    print("Generating mock shutter.wav...")
    generate_wav(shutter_path, 0.2, is_noise=True)

if not os.path.exists(whirr_path):
    print("Generating mock mechanical_whirr.wav...")
    # Low frequency buzz to simulate mechanical whirr
    generate_wav(whirr_path, 3.0, is_noise=False, freq=60.0)

print("Setup complete.")
