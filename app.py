import os
from flask import Flask, request, render_template, jsonify
import speech_recognition as sr
from pydub import AudioSegment
from io import BytesIO
import time

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to simulate stammering score calculation and long pause detection
def calculate_stammering_score(text):
    stammering_keywords = ['uh', 'um', 'err', 'ah', 'like', 'so', 'you know']
    stammering_count = sum(text.lower().count(word) for word in stammering_keywords)
    
    # Adding logic for stuttering severity based on frequency of stammering keywords
    score = stammering_count * 10  # Basic score based on occurrences of stuttering words
    
    # Detecting long pauses (we can consider more than 1.5 seconds of pause as long pause)
    words = text.split()
    pause_threshold = 1.5  # 1.5 seconds pause between words
    pauses = 0
    
    # This example uses simple logic, you might want to improve this with audio analysis (timestamps, etc.)
    for i in range(1, len(words)):
        if len(words[i]) == 0:  # Detects space between words as pause
            pauses += 1
    
    # Adding pause penalties to the score (higher score for more pauses)
    if pauses > 2:  # Threshold for significant pauses
        score += pauses * 5

    return score, stammering_count, pauses

@app.route('/')
def index():
    return render_template('record.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    audio_file = request.files['audio']
    filename = os.path.join(app.config['UPLOAD_FOLDER'], 'audio.wav')
    audio_file.save(filename)

    # Convert audio to WAV format if needed
    audio = AudioSegment.from_file(filename)
    audio.export(filename, format="wav")

    # Use SpeechRecognition to convert speech to text
    recognizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand the audio"}), 400
    except sr.RequestError:
        return jsonify({"error": "Could not request results from Google Speech Recognition service"}), 500

    # Calculate stammering score and pauses
    score, stammering_count, pauses = calculate_stammering_score(text)

    return jsonify({
        "text": text,
        "score": score,
        "stammering_count": stammering_count,
        "pauses": pauses
    })

if __name__ == '__main__':
    app.run(debug=True)