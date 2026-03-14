import os
from gtts import gTTS
import uuid
import streamlit as st
import base64

def text_to_speech(text, lang='vi'):
    """
    Convert text to speech and save as an mp3 file.
    Returns the path to the generated audio file.
    """
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        # Generate a unique filename to avoid browser caching issues in Streamlit
        filename = f"temp_audio/response_{uuid.uuid4().hex[:8]}.mp3"
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"Error in text_to_speech: {e}")
        return None

def get_audio_html(audio_file_path):
    """
    Helper function to generate HTML to play audio automatically in Streamlit.
    """
    with open(audio_file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        # HTML tag to play audio invisibly/automatically
        audio_html = f'''
            <audio autoplay="true">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            '''
        return audio_html
