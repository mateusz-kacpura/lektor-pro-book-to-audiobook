/**
 * Lektor Pro - Audio Player Controller Module
 * Zarządza odtwarzaniem audio, postępem, klawiaturą i prędkością.
 */
import { fmtTime } from './ui.js';

export class AudioPlayer {
  constructor({ onNext, onPrev }) {
    this.audio = document.getElementById("audioPlayer");
    this.playBtn = document.getElementById("btnPlay");
    this.prevBtn = document.getElementById("btnPrev");
    this.nextBtn = document.getElementById("btnNext");
    this.rewindBtn = document.getElementById("btnRewind");
    this.forwardBtn = document.getElementById("btnForward");
    this.progressFill = document.getElementById("progressFill");
    this.progressBar = document.getElementById("progressBar");
    this.currentTimeEl = document.getElementById("currentTime");
    this.totalDurationEl = document.getElementById("totalDuration");

    this.onNext = onNext;
    this.onPrev = onPrev;
    this.isPlaying = false;

    this.initEvents();
  }

  initEvents() {
    if (!this.audio) return;

    this.audio.ontimeupdate = () => {
      if (this.audio.duration) {
        const pct = (this.audio.currentTime / this.audio.duration) * 100;
        if (this.progressFill) this.progressFill.style.width = `${pct}%`;
        if (this.currentTimeEl) this.currentTimeEl.textContent = fmtTime(this.audio.currentTime);
        if (this.totalDurationEl) this.totalDurationEl.textContent = fmtTime(this.audio.duration);
      }
    };

    this.audio.onended = () => {
      this.setPlayState(false);
      const isSequential = document.getElementById("modeSequential")?.checked;
      if (isSequential && this.onNext) {
        this.onNext();
      }
    };

    if (this.playBtn) {
      this.playBtn.onclick = () => this.togglePlay();
    }

    if (this.progressBar) {
      this.progressBar.onclick = (e) => {
        if (!this.audio.duration) return;
        const rect = this.progressBar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        this.audio.currentTime = (clickX / rect.width) * this.audio.duration;
      };
    }

    if (this.prevBtn && this.onPrev) {
      this.prevBtn.onclick = () => this.onPrev();
    }

    if (this.nextBtn && this.onNext) {
      this.nextBtn.onclick = () => this.onNext();
    }

    if (this.rewindBtn) {
      this.rewindBtn.onclick = () => {
        this.audio.currentTime = Math.max(0, this.audio.currentTime - 10);
      };
    }

    if (this.forwardBtn) {
      this.forwardBtn.onclick = () => {
        if (this.audio.duration) {
          this.audio.currentTime = Math.min(this.audio.duration, this.audio.currentTime + 10);
        }
      };
    }

    // Wybór prędkości
    document.querySelectorAll(".speed-btn").forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll(".speed-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.audio.playbackRate = parseFloat(btn.dataset.speed);
      };
    });

    // Skróty klawiszowe
    window.addEventListener("keydown", (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
      if (e.code === "Space") {
        e.preventDefault();
        this.togglePlay();
      } else if (e.code === "ArrowRight" && e.ctrlKey) {
        if (this.onNext) this.onNext();
      } else if (e.code === "ArrowLeft" && e.ctrlKey) {
        if (this.onPrev) this.onPrev();
      } else if (e.code === "ArrowRight") {
        this.audio.currentTime += 5;
      } else if (e.code === "ArrowLeft") {
        this.audio.currentTime -= 5;
      }
    });
  }

  setPlayState(playing) {
    this.isPlaying = playing;
    if (this.playBtn) {
      this.playBtn.textContent = playing ? "⏸" : "▶";
    }
  }

  togglePlay() {
    if (!this.audio.src) return;
    if (this.audio.paused) {
      this.audio.play();
      this.setPlayState(true);
    } else {
      this.audio.pause();
      this.setPlayState(false);
    }
  }

  updateMediaSession(trackTitle = "") {
    if ("mediaSession" in navigator) {
      const bookTitle = document.getElementById("bookTitleSubtitle")?.textContent || "Lektor Pro";
      navigator.mediaSession.metadata = new MediaMetadata({
        title: trackTitle || "Audiobook",
        artist: "Lektor Pro AI",
        album: bookTitle
      });
      navigator.mediaSession.setActionHandler("play", () => this.togglePlay());
      navigator.mediaSession.setActionHandler("pause", () => this.togglePlay());
      if (this.onNext) navigator.mediaSession.setActionHandler("nexttrack", () => this.onNext());
      if (this.onPrev) navigator.mediaSession.setActionHandler("previoustrack", () => this.onPrev());
    }
  }

  loadTrack(url, autoStart = false, trackTitle = "") {
    if (url) {
      this.audio.src = url;
      this.updateMediaSession(trackTitle);
      if (autoStart) {
        this.audio.play()
          .then(() => this.setPlayState(true))
          .catch(() => console.log("Autoplay zablokowany przez przeglądarkę, kliknij Play."));
      } else {
        this.setPlayState(false);
      }
    } else {
      this.audio.removeAttribute("src");
      this.setPlayState(false);
      if (this.totalDurationEl) this.totalDurationEl.textContent = "--:--";
      if (this.progressFill) this.progressFill.style.width = "0%";
    }
  }
}
