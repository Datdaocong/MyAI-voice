from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib import error, request

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8080"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

SYSTEM_PROMPT = (
    "Bạn là trợ lý tư vấn tuyển sinh PTIT. "
    "Trả lời ngắn gọn, rõ ràng, dùng tiếng Việt tự nhiên. "
    "Nếu không chắc, hãy nói rõ và gợi ý link chính thức."
)


def fallback_answer(user_text: str) -> str:
    lower = user_text.lower()
    if any(k in lower for k in ["tuyển sinh", "xét tuyển", "ptit", "aiot"]):
        return "Bạn có thể xem thông tin chính thức tại: https://tuyensinh.ptit.edu.vn/"
    return "Mình đã ghi nhận câu hỏi của bạn. Bạn có thể hỏi cụ thể hơn về tuyển sinh PTIT để mình hỗ trợ tốt hơn."


def ask_gemini(user_text: str) -> str:
    if not GEMINI_API_KEY:
        return fallback_answer(user_text)

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        f"?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\nCâu hỏi: {user_text}"}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 512},
    }

    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "Mình chưa nhận được phản hồi từ Gemini.")
        )
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
            if not user_text:
                self._json(400, {"error": "message is required"})
                return

            answer = ask_gemini(user_text)
            self._json(200, {"reply": answer})
        except Exception as e:
            self._json(500, {"error": str(e)})


if __name__ == "__main__":
    print(f"Server running at http://{HOST}:{PORT}")
    print("Tip: set GEMINI_API_KEY and GEMINI_MODEL before start.")
    ThreadingHTTPServer((HOST, PORT), AppHandler).serve_forever()
