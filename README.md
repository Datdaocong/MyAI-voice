# MyAI Voice (HTML/CSS/JS + LLM Backend)

Bản này chạy bằng web tĩnh + backend Python nhẹ.
Backend hiện hỗ trợ 2 nguồn LLM theo thứ tự:
1. OpenAI Wrapper endpoint (`/api/v1/openai/chat`)  
2. Gemini API (fallback)  
3. Local rule-based fallback (nếu cả 2 lỗi/chưa cấu hình)

## 1) Update code
# MyAI Voice (HTML/CSS/JS + Gemini)

Bản này chạy bằng web tĩnh + backend Python nhẹ để gọi Gemini API ở phía server (không lộ key ra trình duyệt).
Bản này chạy bằng web tĩnh + 1 server Python nhẹ để gọi Gemini API ở phía backend (không lộ key ra trình duyệt).

## 1) Update code trên máy của bạn

```bash
git pull
```

## 2) Cấu hình môi trường

### Linux/macOS
```bash
# Wrapper API (ưu tiên gọi trước)
export OPENAI_WRAPPER_ENABLED="1"
export OPENAI_WRAPPER_URL="https://sl-form-ai.ript.vn/api/v1/openai/chat"

# Gemini fallback (tuỳ chọn)
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
export GEMINI_MODEL="gemini-1.5-flash"

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
$env:OPENAI_WRAPPER_ENABLED="1"
$env:OPENAI_WRAPPER_URL="https://sl-form-ai.ript.vn/api/v1/openai/chat"

$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
$env:GEMINI_MODEL="gemini-1.5-flash"
$env:MAX_HISTORY_TURNS="8"
```

> ⚠️ Nếu từng lộ API key công khai, hãy rotate/revoke key cũ và tạo key mới.
```

> ⚠️ Bạn vừa gửi API key công khai trong chat. Nên vào Google AI Studio để **rotate/revoke key cũ** và tạo key mới ngay.

## 3) Chạy app

```bash
python server.py
```

Mở trình duyệt tại `http://localhost:8080`.

## 4) Cách hoạt động

- Frontend: `index.html`, `styles.css`, `app.js`.
- Frontend gọi `POST /api/chat` và gửi cả lịch sử hội thoại gần nhất.
- Backend map dữ liệu sang wrapper format:
  - request: `{ "text": "...", "system_content": "..." }`
  - response đọc `result`
- Nếu wrapper lỗi/timeout, backend tự fallback qua Gemini, rồi fallback local.

## 5) Tính năng
- Chat text + ngữ cảnh nhiều lượt.
- Ghi âm bằng Web Speech API (nếu browser hỗ trợ).
- TTS bằng speechSynthesis (nếu browser hỗ trợ).
- Tự động failover giữa nhiều nguồn trả lời.


## 6) Troubleshooting (Windows SyntaxError)

Neu ban gap loi kieu:

```
SyntaxError: invalid syntax (server.py, line xx)
```

lam dung thu tu sau trong PowerShell:

```powershell
git fetch --all
git checkout origin/main -- server.py
python -m py_compile server.py
python server.py
```

Neu van loi, kiem tra dung Python 3.10+:

```powershell
python --version
```

Va gui output cua:

```powershell
Get-Content server.py -TotalCount 80
chcp
```

De doi ngu de dang xac dinh file local co bi hong encoding hay khong.
- Backend `server.py` gửi `systemInstruction` + ngữ cảnh cho Gemini để câu trả lời linh hoạt hơn kiểu LLM.
- Nếu chưa set key hoặc API lỗi, backend fallback trả lời an toàn.

## 5) Tính năng
- Chat text + ngữ cảnh nhiều lượt.
- Frontend gọi `POST /api/chat`.
- Backend `server.py` gọi Gemini API bằng `GEMINI_API_KEY` trong biến môi trường.
- Nếu chưa set key hoặc API lỗi, backend fallback trả lời theo rule tuyển sinh PTIT.

## 5) Tính năng
- Chat text.
- Ghi âm bằng Web Speech API (nếu browser hỗ trợ).
- TTS bằng speechSynthesis (nếu browser hỗ trợ).
- Trả lời bằng Gemini qua backend local.
