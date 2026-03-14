import streamlit as st
import time

from speech_handler import record_and_recognize
from logic_processor import check_keywords_and_respond, analyze_sentiment
from audio_handler import text_to_speech, get_audio_html

st.set_page_config(page_title="AI Voice Assistant", page_icon="🎙️", layout="centered")

# --- UI Styling ---
st.markdown("""
<style>
    .user-msg { background-color: #2b313e; padding: 10px; border-radius: 10px; margin-bottom: 10px;}
    .bot-msg { background-color: #1e2430; padding: 10px; border-radius: 10px; border: 1px solid #4CAF50; margin-bottom: 20px;}
    .keyword { color: #4CAF50; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🎙️ Trợ lý ảo AI Cá Nhân")
st.markdown("Nhấn **Bắt đầu Ghi Âm** và nói câu hỏi của bạn.")

# --- Session State ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- Main Interaction ---
col1, col2 = st.columns([1, 4])

with col1:
    if st.button("🎤 Bắt đầu Ghi Âm", type="primary"):
        with st.spinner("Đang lắng nghe... (Hãy nói vào mic)"):
            user_text = record_and_recognize()
            
            if user_text.startswith("[Lỗi"):
                st.error(user_text)
            else:
                # 1. Hiển thị câu hỏi của người dùng
                st.session_state.history.append({"role": "User", "text": user_text})
                
                # 2. Xử lý logic 
                response_text, link = check_keywords_and_respond(user_text)
                sentiment = analyze_sentiment(user_text)
                
                # 3. Chuyển văn bản thành gTTS Audio
                audio_file = text_to_speech(response_text)
                
                st.session_state.history.append({
                    "role": "Bot", 
                    "text": response_text, 
                    "link": link,
                    "audio": audio_file,
                    "sentiment": sentiment
                })

with col2:
    st.caption("Lịch sử cuộc hội thoại sẽ hiện ở bên dưới.")

st.divider()

# --- Hiển thị Lịch sử ---
for i, msg in enumerate(reversed(st.session_state.history)):
    if msg["role"] == "User":
        st.markdown(f'<div class="user-msg">🗣️ <b>Bạn:</b> {msg["text"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'''
        <div class="bot-msg">
            🤖 <b>Trợ lý:</b> {msg["text"]} <br>
            {f'🔗 <a href="{msg["link"]}" target="_blank">Nhấn vào đây để xem chi tiết</a>' if msg["link"] else ''}
            <br>
            <span style="font-size: 0.8em; color: gray;">[Cảm xúc: {msg["sentiment"]}]</span>
        </div>
        ''', unsafe_allow_html=True)
        
        # Chỉ tự động phát âm thanh cho câu trả lời mới nhất
        if i == 0 and msg.get("audio"):
            st.markdown(get_audio_html(msg["audio"]), unsafe_allow_html=True)
            
        # Hiển thị trình phát Media player để nghe lại
        if msg.get("audio"):
            st.audio(msg["audio"], format="audio/mp3")

