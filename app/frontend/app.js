// app/frontend/app.js
// Phase 12: chat logic only. Phase 13+ will add video player + timestamp
// click handling, reading from `window.lastRetrieval` set below.

const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");

// Holds the most recent primary/related structure, for Phase 13+ to use.
window.lastRetrieval = null;

function addMessage(text, role) {
  const div = document.createElement("div");
  div.classList.add("message", role);

  if (role === "assistant") {
    div.innerHTML = marked.parse(text);
  } else {
    div.textContent = text;
  }

  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div;
}

async function sendQuery(query) {
  addMessage(query, "user");
  const thinkingDiv = addMessage("Soch raha hoon...", "assistant");

  try {
    const response = await fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    const data = await response.json();

    thinkingDiv.innerHTML = marked.parse(data.answer);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    window.lastRetrieval = {
      primary: data.primary,
      related: data.related,
    };

    // Phase 13 will hook in here to actually load the video player.
    if (window.onNewRetrieval) {
      window.onNewRetrieval(window.lastRetrieval);
    }
  } catch (err) {
    thinkingDiv.textContent = "Kuch gadbad ho gayi. Backend chal raha hai na? (" + err.message + ")";
  }
}

// Phase 13: whenever a new answer comes back, auto-load the primary
// video and seek to its timestamp.
window.onNewRetrieval = function (retrieval) {
  if (retrieval.primary && window.loadVideoAt) {
    window.loadVideoAt(retrieval.primary.video_id, retrieval.primary.start_seconds);
  }
  if (window.renderRelated) {
    window.renderRelated(retrieval);
  }
};

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const query = chatInput.value.trim();
  if (!query) return;
  chatInput.value = "";
  sendQuery(query);
});
