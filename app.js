const chat = document.getElementById("chat");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const voiceBtn = document.getElementById("voiceBtn");
const stopBtn = document.getElementById("stopBtn");
const speechStatus = document.getElementById("speechStatus");
const ttsStatus = document.getElementById("ttsStatus");

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const speechAvailable = Boolean(SpeechRecognition);
const ttsAvailable = "speechSynthesis" in window;
const conversationHistory = [];

speechStatus.textContent = `Speech-to-Text: ${speechAvailable ? "✅ Sẵn sàng" : "❌ Không hỗ trợ trên trình duyệt này"}`;
ttsStatus.textContent = `Text-to-Speech: ${ttsAvailable ? "✅ Sẵn sàng" : "❌ Không hỗ trợ trên trình duyệt này"}`;

let recognition = null;
if (speechAvailable) {
  recognition = new SpeechRecognition();
  recognition.lang = "vi-VN";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    processUserMessage(text);
  };

  recognition.onerror = (event) => {
    addMessage("bot", `Lỗi ghi âm: ${event.error}`);
  };
}

voiceBtn.disabled = !speechAvailable;
stopBtn.disabled = !speechAvailable;

function analyzeSentiment() {
  return "Neutral";
}

function speakText(text) {
  if (!ttsAvailable) return;
  const clean = text.replace(/<[^>]+>/g, "");
  const utter = new SpeechSynthesisUtterance(clean);
  utter.lang = "vi-VN";
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utter);
}

function addMessage(role, text, sentiment = null) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  const who = role === "user" ? "🗣️ Bạn" : "🤖 Trợ lý";
  div.innerHTML = `<strong>${who}:</strong> ${text}`;

  if (sentiment) {
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `[Cảm xúc: ${sentiment}]`;
    div.appendChild(meta);
  }

  chat.prepend(div);
}

function pushHistory(role, text) {
  conversationHistory.push({ role, text });
  if (conversationHistory.length > 20) {
    conversationHistory.shift();
  }
}

async function getBotReply(message) {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history: conversationHistory }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    return `Lỗi backend (${res.status}): ${errorText}`;
  }

  const data = await res.json();
  return data.reply || "Mình chưa có phản hồi.";
}

async function processUserMessage(text) {
  const cleaned = text.trim();
  if (!cleaned) return;

  addMessage("user", cleaned);
  pushHistory("user", cleaned);

  addMessage("bot", "Đang suy nghĩ để trả lời tự nhiên hơn...");

  try {
    const response = await getBotReply(cleaned);
    chat.removeChild(chat.firstChild);
    pushHistory("model", response);

    const sentiment = analyzeSentiment(cleaned);
    addMessage("bot", response, sentiment);
    speakText(response);
  } catch (err) {
    chat.removeChild(chat.firstChild);
    addMessage("bot", `Không kết nối được tới server local: ${err}`);
  }
}

sendBtn.addEventListener("click", async () => {
  await processUserMessage(userInput.value);
  userInput.value = "";
});

userInput.addEventListener("keydown", async (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    await processUserMessage(userInput.value);
    userInput.value = "";
  }
});

voiceBtn.addEventListener("click", () => {
  if (!recognition) return;
  recognition.start();
  addMessage("bot", "Đang lắng nghe... Hãy nói vào micro.");
});

stopBtn.addEventListener("click", () => {
  if (!recognition) return;
  recognition.stop();
  addMessage("bot", "Đã dừng ghi âm.");
});
