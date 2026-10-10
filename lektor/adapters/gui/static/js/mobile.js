/**
 * Lektor Pro - Mobile Controller Module
 * Zarządza dolnym paskiem nawigacji, mini-odtwarzaczem oraz widokami mobilnymi.
 */

let currentMobileView = "player";

export function initMobileNavigation() {
  const nav = document.getElementById("mobileBottomNav");
  if (!nav) return;

  const items = nav.querySelectorAll(".mobile-nav-item");

  function setMobileView(viewName) {
    currentMobileView = viewName;
    document.body.setAttribute("data-mobile-view", viewName);

    items.forEach(item => {
      const match = item.getAttribute("data-view") === viewName;
      item.classList.toggle("active", match);
    });

    // Pokaż/ukryj mini-odtwarzacz w zależności od widoku
    updateMiniPlayerVisibility();

    // Przewiń na górę ekranu po zmianie widoku
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  items.forEach(item => {
    item.addEventListener("click", () => {
      const view = item.getAttribute("data-view");
      if (view) setMobileView(view);
    });
  });

  // Ustaw domyślny widok przy starcie
  if (window.innerWidth <= 768) {
    setMobileView("player");
  }

  window.addEventListener("resize", () => {
    if (window.innerWidth <= 768 && !document.body.getAttribute("data-mobile-view")) {
      setMobileView("player");
    } else if (window.innerWidth > 768) {
      document.body.removeAttribute("data-mobile-view");
    }
  });

  initMobileNotesToggle();
}

export function initMobileMiniPlayer(audioPlayer) {
  const miniPlayer = document.getElementById("mobileMiniPlayer");
  const miniPlayBtn = document.getElementById("mobMiniPlayBtn");
  const miniTitle = document.getElementById("mobMiniTitle");
  const miniBadge = document.getElementById("mobMiniBadge");
  const miniTime = document.getElementById("mobMiniTime");
  const miniProgress = document.getElementById("mobMiniProgressFill");

  if (!miniPlayer) return;

  // Kliknięcie w play/pause w mini odtwarzaczu
  if (miniPlayBtn) {
    miniPlayBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (audioPlayer && typeof audioPlayer.togglePlay === "function") {
        audioPlayer.togglePlay();
      }
    });
  }

  // Kliknięcie w resztę mini odtwarzacza przełącza na pełny widok "player"
  miniPlayer.addEventListener("click", () => {
    const mobNavPlayer = document.getElementById("mobNavPlayer");
    if (mobNavPlayer) mobNavPlayer.click();
  });

  // Obserwator zmian tytułu strony w głównym odtwarzaczu
  const mainTitleEl = document.getElementById("playerPageTitle");
  const mainBadgeEl = document.getElementById("playerPageBadge");
  const currentTimeEl = document.getElementById("currentTime");
  const totalDurationEl = document.getElementById("totalDuration");
  const progressFill = document.getElementById("progressFill");

  function syncMiniPlayer() {
    if (miniTitle && mainTitleEl) {
      miniTitle.textContent = mainTitleEl.textContent || "Brak wybranego audio";
    }
    if (miniBadge && mainBadgeEl) {
      miniBadge.textContent = mainBadgeEl.textContent || "";
    }
    if (miniTime && currentTimeEl && totalDurationEl) {
      miniTime.textContent = `${currentTimeEl.textContent} / ${totalDurationEl.textContent}`;
    }
    if (miniProgress && progressFill) {
      miniProgress.style.width = progressFill.style.width || "0%";
    }
    if (miniPlayBtn) {
      const isPlaying = audioPlayer && audioPlayer.isPlaying;
      miniPlayBtn.textContent = isPlaying ? "⏸" : "▶";
    }
    updateMiniPlayerVisibility();
  }

  // Nasłuchuj zdarzeń audio
  const audio = document.getElementById("audioPlayer");
  if (audio) {
    audio.addEventListener("timeupdate", syncMiniPlayer);
    audio.addEventListener("play", () => {
      if (miniPlayBtn) miniPlayBtn.textContent = "⏸";
      updateMiniPlayerVisibility();
    });
    audio.addEventListener("pause", () => {
      if (miniPlayBtn) miniPlayBtn.textContent = "▶";
    });
  }

  // Aktualizuj przy ładowaniu nowej strony
  const observer = new MutationObserver(syncMiniPlayer);
  if (mainTitleEl) {
    observer.observe(mainTitleEl, { childList: true, characterData: true, subtree: true });
  }

  syncMiniPlayer();
}

function updateMiniPlayerVisibility() {
  const miniPlayer = document.getElementById("mobileMiniPlayer");
  if (!miniPlayer) return;

  const audio = document.getElementById("audioPlayer");
  const hasAudio = audio && audio.src && audio.src.trim() !== "";
  const isMobile = window.innerWidth <= 768;
  const isNotPlayerTab = currentMobileView !== "player";

  if (isMobile && hasAudio && isNotPlayerTab) {
    miniPlayer.style.display = "flex";
  } else {
    miniPlayer.style.display = "none";
  }
}

function initMobileNotesToggle() {
  const btnEditor = document.getElementById("btnNotesMobEditor");
  const btnPreview = document.getElementById("btnNotesMobPreview");

  if (!btnEditor || !btnPreview) return;

  btnEditor.addEventListener("click", () => {
    document.body.classList.remove("notes-mob-preview-active");
    btnEditor.classList.add("active");
    btnPreview.classList.remove("active");
  });

  btnPreview.addEventListener("click", () => {
    document.body.classList.add("notes-mob-preview-active");
    btnPreview.classList.add("active");
    btnEditor.classList.remove("active");
  });
}
