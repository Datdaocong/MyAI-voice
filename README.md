# MyAI Voice (HTML/CSS/JS + Gemini)

Bản này chạy bằng web tĩnh + 1 server Python nhẹ để gọi Gemini API ở phía backend (không lộ key ra trình duyệt).

## 1) Update code trên máy của bạn

```bash
git pull
```

## 2) Cấu hình Gemini API key

### Linux/macOS
```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
export GEMINI_MODEL="gemini-1.5-flash"
```

### Windows PowerShell
```powershell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
$env:GEMINI_MODEL="gemini-1.5-flash"
```

> ⚠️ Bạn vừa gửi API key công khai trong chat. Nên vào Google AI Studio để **rotate/revoke key cũ** và tạo key mới ngay.

## 3) Chạy app

```bash
python server.py
```

Mở trình duyệt tại `http://localhost:8080`.

## 4) Cách hoạt động

- Frontend: `index.html`, `styles.css`, `app.js`.
- Frontend gọi `POST /api/chat`.
- Backend `server.py` gọi Gemini API bằng `GEMINI_API_KEY` trong biến môi trường.
- Nếu chưa set key hoặc API lỗi, backend fallback trả lời theo rule tuyển sinh PTIT.

## 5) Tính năng
- Chat text.
- Ghi âm bằng Web Speech API (nếu browser hỗ trợ).
- TTS bằng speechSynthesis (nếu browser hỗ trợ).
- Trả lời bằng Gemini qua backend local.
