from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib import error, request

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8080"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", "8"))

SYSTEM_PROMPT = (
    "Bạn là trợ lý AI tiếng Việt, trả lời linh hoạt như các LLM hiện đại. "
    "Ưu tiên giọng điệu tự nhiên, rõ ràng, có cấu trúc, đi thẳng vào nhu cầu người dùng. "
    "Khi phù hợp, đưa ví dụ ngắn hoặc checklist dễ làm theo. "
    "Nếu câu hỏi liên quan tuyển sinh/PTIT, cung cấp thông tin thực tế và nhắc nguồn chính thức: "
    "https://tuyensinh.ptit.edu.vn/. "
    "Nếu chưa chắc chắn, nói rõ mức độ chắc chắn thay vì bịa."
)


def fallback_answer(user_text: str) -> str:
    lower = user_text.lower()
    if any(k in lower for k in ["tuyển sinh", "xét tuyển", "ptit", "aiot"]):
        return (
            "Mình gợi ý bạn xem nguồn chính thức tại https://tuyensinh.ptit.edu.vn/. "
            "Nếu bạn cho mình biết ngành/điểm/khu vực, mình sẽ tư vấn chi tiết hơn theo từng bước."
        )
    return (
        "Mình đã nhận câu hỏi. Bạn có thể nói rõ mục tiêu hơn (ví dụ: muốn lộ trình học, "
        "tư vấn ngành, hay so sánh lựa chọn) để mình trả lời sát như trợ lý AI cá nhân."
    )


def _build_contents(user_text: str, history: list[dict]) -> list[dict]:
    contents: list[dict] = []

    compact_history = history[-MAX_HISTORY_TURNS:]
    for turn in compact_history:
        role = turn.get("role")
        text = str(turn.get("text", "")).strip()
        if not text:
            continue
        if role not in {"user", "model"}:
            continue
        contents.append({"role": role, "parts": [{"text": text}]})

    contents.append({"role": "user", "parts": [{"text": user_text}]})
    return contents


def ask_gemini(user_text: str, history: list[dict] | None = None) -> str:
    if not GEMINI_API_KEY:
        return fallback_answer(user_text)

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        f"?key={GEMINI_API_KEY}"
    )

    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": _build_contents(user_text, history or []),
        "generationConfig": {
            "temperature": 0.8,
            "topP": 0.95,
            "topK": 40,
            "maxOutputTokens": 1024,
        },
    }

    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        candidate = data.get("candidates", [{}])[0]
        parts = candidate.get("content", {}).get("parts", [])
        text = "\n".join(part.get("text", "") for part in parts).strip()
        return text or "Mình chưa nhận được phản hồi đầy đủ từ Gemini."
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        return f"Gemini API lỗi HTTP {e.code}. Chi tiết: {detail[:300]}"
    except Exception as e:
        return f"Không gọi được Gemini API: {e}"


class AppHandler(SimpleHTTPRequestHandler):
    def _json(self, status: int, body: dict) -> None:
        content = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if self.path != "/api/chat":
            self._json(404, {"error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            body = json.loads(raw.decode("utf-8") or "{}")

            user_text = str(body.get("message", "")).strip()
            history = body.get("history", [])
            if not isinstance(history, list):
                history = []

            if not user_text:
                self._json(400, {"error": "message is required"})
                return

            answer = ask_gemini(user_text, history)
            self._json(200, {"reply": answer})
        except Exception as e:
            self._json(500, {"error": str(e)})


if __name__ == "__main__":
    print(f"Server running at http://{HOST}:{PORT}")
    print("Tip: set GEMINI_API_KEY and GEMINI_MODEL before start.")
    ThreadingHTTPServer((HOST, PORT), AppHandler).serve_forever()
