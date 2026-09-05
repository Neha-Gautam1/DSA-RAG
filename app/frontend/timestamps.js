// app/frontend/timestamps.js
// Phase 15: renders the primary + related timestamp list, and handles
// clicks -- seeking the existing player if it's the same video, or
// loading a new video if the clicked timestamp belongs to a different one.

function formatTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60);
  const s = Math.floor(totalSeconds % 60);
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

function truncateLabel(text, maxLen = 60) {
  text = text.trim();
  if (text.length <= maxLen) return text;
  const cut = text.slice(0, maxLen);
  const lastSpace = cut.lastIndexOf(" ");
  return (lastSpace > 0 ? cut.slice(0, lastSpace) : cut) + "...";
}

function setActiveItem(el) {
  document.querySelectorAll(".related-item").forEach((e) => e.classList.remove("active"));
  el.classList.add("active");
}

function handleTimestampClick(item, el) {
  const currentVideoId = window.getCurrentVideoId ? window.getCurrentVideoId() : null;

  if (item.video_id === currentVideoId) {
    // Same video: just seek the existing player.
    window.seekTo(item.start_seconds);
  } else {
    // Different video: load it fresh and seek.
    window.loadVideoAt(item.video_id, item.start_seconds);
  }

  setActiveItem(el);
}

function renderRelated(retrieval) {
  const container = document.getElementById("related-container");
  container.innerHTML = "";

  if (!retrieval.primary) return;

  const heading = document.createElement("div");
  heading.className = "related-heading";
  heading.textContent = "Related timestamps";
  container.appendChild(heading);

  // Primary shown first (marked active/now playing), then related suggestions.
  const items = [
    {
      video_id: retrieval.primary.video_id,
      title: retrieval.primary.title,
      start_seconds: retrieval.primary.start_seconds,
      label: truncateLabel(retrieval.primary.text),
      isPrimary: true,
    },
    ...retrieval.related.map((r) => ({ ...r, isPrimary: false })),
  ];

  items.forEach((item) => {
    const el = document.createElement("div");
    el.className = "related-item" + (item.isPrimary ? " active" : "");

    const timeSpan = document.createElement("span");
    timeSpan.className = "related-time";
    timeSpan.textContent = (item.isPrimary ? "▶ " : "") + formatTime(item.start_seconds);

    const textWrap = document.createElement("div");
    textWrap.className = "related-text";

    const labelSpan = document.createElement("span");
    labelSpan.className = "related-label";
    labelSpan.textContent = item.label;

    const titleSpan = document.createElement("span");
    titleSpan.className = "related-video-title";
    titleSpan.textContent = item.title || "";

    textWrap.appendChild(labelSpan);
    textWrap.appendChild(titleSpan);

    el.appendChild(timeSpan);
    el.appendChild(textWrap);

    el.addEventListener("click", () => handleTimestampClick(item, el));

    container.appendChild(el);
  });
}

window.renderRelated = renderRelated;
