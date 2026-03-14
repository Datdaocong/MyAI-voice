import streamlit as st

from audio_handler import get_audio_html, text_to_speech, tts_available
from logic_processor import analyze_sentiment, check_keywords_and_respond
from speech_handler import (
    microphone_supported,
    record_and_recognize,
    speech_available,
    transcribe_uploaded_audio,
)

st.set_page_config(page_title="AI Voice Assistant", page_icon="🎙️", layout="centered")

st.markdown(
    """
<style>
    .user-msg { background-color: #2b313e; padding: 10px; border-radius: 10px; margin-bottom: 10px;}
    .bot-msg { background-color: #1e2430; padding: 10px; border-radius: 10px; border: 1px solid #4CAF50; margin-bottom: 20px;}
</style>
""",
    unsafe_allow_html=True,
)

st.title("🎙️ Trợ lý ảo AI Cá Nhân")
st.markdown("Bạn có thể dùng **ghi âm**, **tải file audio**, hoặc **nhập văn bản** để hỏi.")

if "history" not in st.session_state:
    st.session_state.history = []

speech_ready = speech_available()
mic_ready = microphone_supported() if speech_ready else False
tts_ready = tts_available()

with st.expander("Trạng thái tính năng", expanded=False):
    st.write(f"- SpeechRecognition: {'✅' if speech_ready else '❌'}")
    st.write(f"- Microphone realtime: {'✅' if mic_ready else '❌'}")
    st.write(f"- Text-to-Speech (gTTS): {'✅' if tts_ready else '❌'}")


def process_user_message(user_text: str) -> None:
    st.session_state.history.append({"role": "User", "text": user_text})

    response_text, link = check_keywords_and_respond(user_text)
    sentiment = analyze_sentiment(user_text)
    audio_file = text_to_speech(response_text) if tts_ready else None

    st.session_state.history.append(
        {
            "role": "Bot",
            "text": response_text,
            "link": link,
            "audio": audio_file,
            "sentiment": sentiment,
        }
    )


tab_voice, tab_upload, tab_text = st.tabs(["🎤 Ghi âm", "📁 Tải file audio", "⌨️ Nhập văn bản"])

with tab_voice:
    if not speech_ready:
        st.warning("Chưa cài SpeechRecognition/PyAudio. Cài `requirements-voice.txt` để dùng ghi âm.")
    elif not mic_ready:
        st.warning("Micro chưa sẵn sàng trong môi trường này. Hãy dùng tab tải file audio hoặc nhập văn bản.")

    if st.button(
        "🎤 Bắt đầu ghi âm",
        type="primary",
        use_container_width=True,
        disabled=(not speech_ready or not mic_ready),
    ):
        with st.spinner("Đang lắng nghe... (Hãy nói vào mic)"):
            user_text = record_and_recognize()

        if user_text.startswith("[Lỗi"):
            st.error(user_text)
        else:
            process_user_message(user_text)
            st.success("Đã ghi nhận câu hỏi bằng giọng nói.")

with tab_upload:
    if not speech_ready:
        st.warning("Chưa cài SpeechRecognition. Cài `requirements-audio.txt` để nhận diện file audio.")

    st.caption("Hỗ trợ tốt nhất: WAV/AIFF/FLAC.")
    uploaded_audio = st.file_uploader("Tải file audio", type=["wav", "aiff", "aif", "flac"])
    if st.button("🔎 Nhận diện từ file", use_container_width=True, disabled=not speech_ready):
        if not uploaded_audio:
            st.warning("Vui lòng tải file audio trước.")
        else:
            with st.spinner("Đang nhận diện giọng nói từ file..."):
                user_text = transcribe_uploaded_audio(uploaded_audio.read())

            if user_text.startswith("[Lỗi"):
                st.error(user_text)
            else:
                process_user_message(user_text)
                st.success("Đã xử lý câu hỏi từ file audio.")

with tab_text:
    with st.form("text_question_form", clear_on_submit=True):
        typed_text = st.text_area("Nhập câu hỏi của bạn", placeholder="VD: Tuyển sinh PTIT năm nay thế nào?")
        submitted = st.form_submit_button("Gửi câu hỏi", use_container_width=True)

    if submitted:
        if not typed_text.strip():
            st.warning("Vui lòng nhập nội dung trước khi gửi.")
        else:
            process_user_message(typed_text.strip())
            st.success("Đã xử lý câu hỏi văn bản.")

if not tts_ready:
    st.info("TTS đang tắt vì chưa cài gTTS. Cài `requirements-audio.txt` để bật đọc giọng nói.")

st.divider()
st.caption("Lịch sử hội thoại")

for i, msg in enumerate(reversed(st.session_state.history)):
    if msg["role"] == "User":
        st.markdown(f'<div class="user-msg">🗣️ <b>Bạn:</b> {msg["text"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'''
        <div class="bot-msg">
            🤖 <b>Trợ lý:</b> {msg["text"]} <br>
            {f'🔗 <a href="{msg["link"]}" target="_blank">Nhấn vào đây để xem chi tiết</a>' if msg["link"] else ''}
            <br>
            <span style="font-size: 0.8em; color: gray;">[Cảm xúc: {msg["sentiment"]}]</span>
        </div>
        ''',
            unsafe_allow_html=True,
        )

        if i == 0 and msg.get("audio"):
            st.markdown(get_audio_html(msg["audio"]), unsafe_allow_html=True)

        if msg.get("audio"):
            st.audio(msg["audio"], format="audio/mp3")
