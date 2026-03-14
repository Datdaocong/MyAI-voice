import base64
from pathlib import Path
import uuid

AUDIO_DIR = Path("temp_audio")

try:
    from gtts import gTTS
except Exception:
    gTTS = None


def tts_available() -> bool:
    return gTTS is not None


def text_to_speech(text, lang="vi"):
    """
    Convert text to speech and save as an mp3 file.
    Returns the path to the generated audio file.
    """
    if not text or not tts_available():
        return None

    try:
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        tts = gTTS(text=text, lang=lang, slow=False)
        filename = AUDIO_DIR / f"response_{uuid.uuid4().hex[:8]}.mp3"
        tts.save(str(filename))
        return str(filename)
    except Exception:
        return None


def get_audio_html(audio_file_path):
    """
    Helper function to generate HTML to play audio automatically in Streamlit.
    """
    if not audio_file_path:
        return ""

    file_path = Path(audio_file_path)
    if not file_path.exists():
        return ""

    with file_path.open("rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        return f'''
            <audio autoplay="true">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            '''
