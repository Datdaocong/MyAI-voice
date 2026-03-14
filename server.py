# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional, Tuple
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


def fallback_answer(user_text: str) -> str:
    lower = user_text.lower()
    if any(k in lower for k in ["tuyen sinh", "xet tuyen", "ptit", "aiot"]):
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

            answer = ask_model(user_text, history)
            self._json(200, {"reply": answer})
        except Exception as e:
            self._json(500, {"error": str(e)})


if __name__ == "__main__":
    print(f"Server running at http://{HOST}:{PORT}")
    print(f"OpenAI wrapper enabled: {OPENAI_WRAPPER_ENABLED} | URL: {OPENAI_WRAPPER_URL}")
    print(f"Gemini configured: {'yes' if GEMINI_API_KEY else 'no'} | Model: {GEMINI_MODEL}")
    ThreadingHTTPServer((HOST, PORT), AppHandler).serve_forever()
