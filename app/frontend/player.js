// app/frontend/player.js
// Phase 13: manages the embedded YouTube player -- loading videos and
// seeking to timestamps. Exposes window.loadVideoAt(videoId, seconds)
// for Phase 15 (clickable related timestamps) to reuse.

let ytPlayer = null;
let playerReady = false;
let pendingLoad = null; // { videoId, seconds } if a load was requested before player was ready

const placeholderEl = document.getElementById("video-placeholder");

// Called automatically by the YouTube IFrame API once it has loaded.
function onYouTubeIframeAPIReady() {
  console.log("[player] YouTube IFrame API is ready");
  ytPlayer = new YT.Player("youtube-player", {
    height: "100%",
    width: "100%",
    playerVars: { rel: 0 },
    events: {
      onReady: () => {
        playerReady = true;
        if (pendingLoad) {
          loadVideoAt(pendingLoad.videoId, pendingLoad.seconds);
          pendingLoad = null;
        }
      },
      onError: (event) => {
        // Common cause: embedding disabled by the video owner.
        placeholderEl.style.display = "flex";
        placeholderEl.textContent =
          "Ye video embed nahi ho pa raha. Isse seedha YouTube par dekho.";
      },
    },
  });
}

window.onYouTubeIframeAPIReady = onYouTubeIframeAPIReady;

function loadVideoAt(videoId, seconds) {
  console.log("[player] loadVideoAt called with:", videoId, seconds, "playerReady =", playerReady);
  if (!playerReady) {
    // API script might still be loading -- queue this request.
    pendingLoad = { videoId, seconds };
    return;
  }

  placeholderEl.style.display = "none";
  ytPlayer.loadVideoById({ videoId, startSeconds: seconds });
  ytPlayer.playVideo();
}

function seekTo(seconds) {
  if (!playerReady) return;
  ytPlayer.seekTo(seconds, true);
  ytPlayer.playVideo();
}

// Expose globally so Phase 14/15 code can call these.
window.loadVideoAt = loadVideoAt;
window.seekTo = seekTo;
window.getCurrentVideoId = () => (ytPlayer ? ytPlayer.getVideoData().video_id : null);
