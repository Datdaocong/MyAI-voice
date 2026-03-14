from __future__ import annotations

from io import BytesIO

try:
    import speech_recognition as sr
except Exception:
    sr = None


def speech_available() -> bool:
    return sr is not None


def microphone_supported() -> bool:
    """Return True when microphone access is available in runtime."""
    if not speech_available():
        return False
    try:
        with sr.Microphone() as source:
            _ = source
        return True
    except Exception:
        return False


def record_and_recognize(timeout: int = 5, phrase_time_limit: int = 10):
    """Use local microphone + Google STT to recognize Vietnamese speech."""
    if not speech_available():
        return "[Lỗi: Chưa cài SpeechRecognition/PyAudio. Hãy dùng nhập văn bản hoặc cài requirements-voice.txt]"

    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        return recognizer.recognize_google(audio, language="vi-VN")

    except sr.WaitTimeoutError:
        return "[Lỗi: Hết thời gian ghi âm vì không nghe thấy gì.]"
    except sr.UnknownValueError:
        return "[Lỗi: Xin lỗi, tôi không nghe rõ câu đó.]"
    except sr.RequestError:
        return "[Lỗi mạng: Không thể kết nối API Google Speech Recognition.]"
    except OSError:
        return "[Lỗi: Không tìm thấy micro. Hãy dùng tab nhập văn bản hoặc tải file audio.]"
    except Exception as e:
        return f"[Lỗi hệ thống: {e}]"


def transcribe_uploaded_audio(file_bytes: bytes):
    """Recognize Vietnamese speech from uploaded WAV/AIFF/FLAC audio bytes."""
    if not speech_available():
        return "[Lỗi: Chưa cài SpeechRecognition. Hãy dùng tab nhập văn bản hoặc cài requirements-audio.txt]"

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(BytesIO(file_bytes)) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language="vi-VN")
    except sr.UnknownValueError:
        return "[Lỗi: Không nhận diện được nội dung trong file audio.]"
    except sr.RequestError:
        return "[Lỗi mạng: Không thể kết nối API Google Speech Recognition.]"
    except Exception as e:
        return f"[Lỗi: File audio chưa đúng định dạng hỗ trợ (WAV/AIFF/FLAC). Chi tiết: {e}]"
