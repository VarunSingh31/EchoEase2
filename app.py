import os
from flask import Flask, request, render_template, redirect, url_for, jsonify
import speech_recognition as sr
from pydub import AudioSegment
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
    
    score = stammering_count * 10  # Basic score based on occurrences of stuttering words
    
    words = text.split()
    pause_threshold = 1.5
    pauses = 0
    
    for i in range(1, len(words)):
        if len(words[i]) == 0:  # Detects space between words as pause
            pauses += 1
    
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

@app.route('/results.html')
def results():
    # Extract query parameters from the URL
    text = request.args.get('text', '')
    score = request.args.get('score', '')
    stammering_count = request.args.get('stammering_count', '')
    pauses = request.args.get('pauses', '')

    # Ensure that all necessary data is being passed to the template
    return render_template('results.html', text=text, score=score, stammering_count=stammering_count, pauses=pauses)


if __name__ == '__main__':
    app.run(debug=True)
