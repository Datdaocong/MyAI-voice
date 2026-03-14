# MyAI Voice (HTML/CSS/JS + Gemini)

Bản này chạy bằng web tĩnh + backend Python nhẹ để gọi Gemini API ở phía server (không lộ key ra trình duyệt).

## 1) Update code trên máy của bạn

```bash
git pull
```

## 2) Cấu hình Gemini API key

### Linux/macOS
```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
export GEMINI_MODEL="gemini-1.5-flash"
# Tuỳ chọn: số lượt hội thoại gửi kèm ngữ cảnh
export MAX_HISTORY_TURNS="8"
```

### Windows PowerShell
```powershell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
$env:GEMINI_MODEL="gemini-1.5-flash"
$env:MAX_HISTORY_TURNS="8"
```

> ⚠️ Nếu từng lộ API key công khai, hãy rotate/revoke key cũ và tạo key mới.

## 3) Chạy app

```bash
python server.py
```

Mở trình duyệt tại `http://localhost:8080`.

## 4) Cách hoạt động

- Frontend: `index.html`, `styles.css`, `app.js`.
- Frontend gọi `POST /api/chat` và gửi cả lịch sử hội thoại gần nhất.
- Backend `server.py` gửi `systemInstruction` + ngữ cảnh cho Gemini để câu trả lời linh hoạt hơn kiểu LLM.
- Nếu chưa set key hoặc API lỗi, backend fallback trả lời an toàn.

## 5) Tính năng
- Chat text + ngữ cảnh nhiều lượt.
- Ghi âm bằng Web Speech API (nếu browser hỗ trợ).
- TTS bằng speechSynthesis (nếu browser hỗ trợ).
- Trả lời bằng Gemini qua backend local.
