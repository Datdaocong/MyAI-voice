# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional, Tuple
from typing import Dict, List, Optional
from urllib import error, request

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8080"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", "8"))

# OpenAI wrapper integration (from provided method)
OPENAI_WRAPPER_URL = os.getenv("OPENAI_WRAPPER_URL", "https://sl-form-ai.ript.vn/api/v1/openai/chat")
OPENAI_WRAPPER_ENABLED = os.getenv("OPENAI_WRAPPER_ENABLED", "1") == "1"

# IMPORTANT:
# - Keep prompt strictly ASCII to avoid Windows terminal/editor corruption.
# - Build with explicit join(list) (no implicit adjacent-string concatenation).
SYSTEM_PROMPT_LINES = [
    "Ban la tro ly AI tieng Viet, tra loi linh hoat nhu cac LLM hien dai.",
    "Uu tien giong dieu tu nhien, ro rang, co cau truc, di thang vao nhu cau nguoi dung.",
    "Khi phu hop, dua vi du ngan hoac checklist de lam theo.",
    "Neu cau hoi lien quan tuyen sinh/PTIT, hay nhac nguon chinh thuc: https://tuyensinh.ptit.edu.vn/.",
    "Neu chua chac chan, hay noi ro muc do chac chan thay vi bia thong tin.",
]
SYSTEM_PROMPT = " ".join(SYSTEM_PROMPT_LINES)
# Keep prompt ASCII-only to avoid any Windows encoding/editor corruption issues.
SYSTEM_PROMPT = (
    "Ban la tro ly AI tieng Viet, tra loi linh hoat nhu cac LLM hien dai. "
    "Uu tien giong dieu tu nhien, ro rang, co cau truc, di thang vao nhu cau nguoi dung. "
    "Khi phu hop, dua vi du ngan hoac checklist de lam theo. "
    "Neu cau hoi lien quan tuyen sinh/PTIT, hay nhac nguon chinh thuc: "
    "https://tuyensinh.ptit.edu.vn/. "
    "Neu chua chac chan, hay noi ro muc do chac chan thay vi bia thong tin."
SYSTEM_PROMPT = (
    "Bạn là trợ lý AI tiếng Việt, trả lời linh hoạt như các LLM hiện đại. "
    "Ưu tiên giọng điệu tự nhiên, rõ ràng, có cấu trúc, đi thẳng vào nhu cầu người dùng. "
    "Khi phù hợp, đưa ví dụ ngắn hoặc checklist dễ làm theo. "
    "Nếu câu hỏi liên quan tuyển sinh/PTIT, cung cấp thông tin thực tế và nhắc nguồn chính thức: "
    "https://tuyensinh.ptit.edu.vn/. "
    "Nếu chưa chắc chắn, nói rõ mức độ chắc chắn thay vì bịa."

SYSTEM_PROMPT = (
    "Bạn là trợ lý tư vấn tuyển sinh PTIT. "
    "Trả lời ngắn gọn, rõ ràng, dùng tiếng Việt tự nhiên. "
    "Nếu không chắc, hãy nói rõ và gợi ý link chính thức."
)


def fallback_answer(user_text: str) -> str:
    lower = user_text.lower()
    if any(k in lower for k in ["tuyen sinh", "xet tuyen", "ptit", "aiot"]):
    if any(k in lower for k in ["tuyen sinh", "xet tuyen", "ptit", "aiot", "tuyển sinh", "xét tuyển"]):
        return (
            "Ban co the xem nguon chinh thuc tai https://tuyensinh.ptit.edu.vn/. "
            "Neu ban cho minh biet nganh/diem/khu vuc, minh se tu van chi tiet hon theo tung buoc."
        )
    return (
        "Minh da nhan cau hoi. Ban co the noi ro muc tieu hon (vi du: lo trinh hoc, "
        "tu van nganh, hay so sanh lua chon) de minh tra loi sat hon."
    )


def _build_contents(user_text: str, history: List[Dict]) -> List[Dict]:
    contents: List[Dict] = []
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


def _build_wrapper_text(user_text: str, history: Optional[List[Dict]] = None) -> str:
    lines: List[str] = []
    for turn in (history or [])[-MAX_HISTORY_TURNS:]:
        role = turn.get("role")
        text = str(turn.get("text", "")).strip()
        if not text or role not in {"user", "model"}:
            continue
        who = "Nguoi dung" if role == "user" else "Tro ly"
        lines.append(f"{who}: {text}")
    lines.append(f"Nguoi dung: {user_text}")
    return "\n".join(lines)


def ask_openai_wrapper(user_text: str, history: Optional[List[Dict]] = None) -> Tuple[bool, str]:
    """Call wrapper endpoint that expects: {text, system_content} and returns {result}."""
    if not OPENAI_WRAPPER_ENABLED:
        return False, "wrapper disabled"

    payload = {
        "text": _build_wrapper_text(user_text, history),
        "system_content": SYSTEM_PROMPT,
    }

    req = request.Request(
        OPENAI_WRAPPER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = str(data.get("result", "")).strip()
        if not text:
            return False, "wrapper empty result"
        return True, text
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        return False, f"wrapper http {e.code}: {detail[:180]}"
    except Exception as e:
        return False, f"wrapper call failed: {e}"


def ask_gemini(user_text: str, history: Optional[List[Dict]] = None) -> Tuple[bool, str]:
    if not GEMINI_API_KEY:
        return False, "gemini key missing"
def ask_gemini(user_text: str, history: Optional[List[Dict]] = None) -> str:
def ask_gemini(user_text: str, history: list[dict] | None = None) -> str:
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
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": _build_contents(user_text, history or []),
        "generationConfig": {
            "temperature": 0.8,
            "topP": 0.95,
            "topK": 40,
            "maxOutputTokens": 1024,
        },
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
        with request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        candidate = data.get("candidates", [{}])[0]
        parts = candidate.get("content", {}).get("parts", [])
        text = "\n".join(part.get("text", "") for part in parts).strip()
        if not text:
            return False, "gemini empty response"
        return True, text
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        return False, f"gemini http {e.code}: {detail[:180]}"
    except Exception as e:
        return False, f"gemini call failed: {e}"


def ask_model(user_text: str, history: Optional[List[Dict]] = None) -> str:
    # 1) Try OpenAI wrapper endpoint first (as requested integration)
    ok, out = ask_openai_wrapper(user_text, history)
    if ok:
        return out

    # 2) Fallback Gemini if configured
    ok2, out2 = ask_gemini(user_text, history)
    if ok2:
        return out2

    # 3) Local safe fallback
    return fallback_answer(user_text)


class AppHandler(SimpleHTTPRequestHandler):
    def _json(self, status: int, body: Dict) -> None:
        return text or "Minh chua nhan duoc phan hoi day du tu Gemini."
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        return f"Gemini API loi HTTP {e.code}. Chi tiet: {detail[:300]}"
    except Exception as e:
        return f"Khong goi duoc Gemini API: {e}"


class AppHandler(SimpleHTTPRequestHandler):
    def _json(self, status: int, body: Dict) -> None:
        return text or "Mình chưa nhận được phản hồi đầy đủ từ Gemini."
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
            history = body.get("history", [])
            if not isinstance(history, list):
                history = []

            user_text = str(body.get("message", "")).strip()
            if not user_text:
                self._json(400, {"error": "message is required"})
                return

            answer = ask_model(user_text, history)
            answer = ask_gemini(user_text, history)
            answer = ask_gemini(user_text)
            self._json(200, {"reply": answer})
        except Exception as e:
            self._json(500, {"error": str(e)})


if __name__ == "__main__":
    print(f"Server running at http://{HOST}:{PORT}")
    print(f"OpenAI wrapper enabled: {OPENAI_WRAPPER_ENABLED} | URL: {OPENAI_WRAPPER_URL}")
    print(f"Gemini configured: {'yes' if GEMINI_API_KEY else 'no'} | Model: {GEMINI_MODEL}")
    print("Tip: set GEMINI_API_KEY and GEMINI_MODEL before start.")
    ThreadingHTTPServer((HOST, PORT), AppHandler).serve_forever()
