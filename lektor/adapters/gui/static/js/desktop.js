/**
 * Lektor Pro — Desktop Window Workspace & Drag-and-Drop Manager
 * Obsługuje przesuwanie, zmianę rozmiaru, minimalizację, maksymalizację,
 * zapamiętywanie pozycji w localStorage oraz presety układu okien pulpitu.
 */

const STORAGE_KEY = "lektor_pro_desktop_state_v1";

const DEFAULT_PRESETS = {
  // Domyślny zbalansowany układ pulpitu
  default: {
    "win-progress": { x: 20, y: 15, w: 720, h: 260, isMin: false, isMax: false, z: 10 },
    "win-player": { x: 20, y: 290, w: 720, h: 240, isMin: false, isMax: false, z: 11 },
    "win-reader": { x: 760, y: 15, w: 780, h: 520, isMin: false, isMax: false, z: 12 },
    "win-notes": { x: 760, y: 550, w: 780, h: 320, isMin: false, isMax: false, z: 13 },
    "win-playlist": { x: 20, y: 545, w: 380, h: 325, isMin: false, isMax: false, z: 14 },
  },

  // Tryb nauki: Czytnik + Notatnik na pierwszym planie
  study: {
    "win-reader": { x: 20, y: 15, w: 760, h: 845, isMin: false, isMax: false, z: 22 },
    "win-player": { x: 800, y: 15, w: 740, h: 245, isMin: false, isMax: false, z: 20 },
    "win-notes": { x: 800, y: 275, w: 740, h: 585, isMin: false, isMax: false, z: 23 },
    "win-playlist": { x: 800, y: 810, w: 360, h: 180, isMin: true, isMax: false, z: 10 },
    "win-progress": { x: 20, y: 810, w: 400, h: 180, isMin: true, isMax: false, z: 10 }
  },

  // Tryb czytelnika: duży wyeksponowany czytnik Markdown, kompaktowy odtwarzacz i spis stron
  reading: {
    "win-reader": { x: 20, y: 15, w: 1020, h: 780, isMin: false, isMax: false, z: 20 },
    "win-player": { x: 1060, y: 15, w: 500, h: 250, isMin: false, isMax: false, z: 19 },
    "win-playlist": { x: 1060, y: 280, w: 500, h: 515, isMin: false, isMax: false, z: 18 },
    "win-notes": { x: 20, y: 810, w: 500, h: 180, isMin: true, isMax: false, z: 10 },
    "win-progress": { x: 540, y: 810, w: 500, h: 180, isMin: true, isMax: false, z: 10 },
  },

  // Dwie równe kolumny
  sideBySide: {
    "win-progress": { x: 20, y: 15, w: 740, h: 260, isMin: false, isMax: false, z: 11 },
    "win-player": { x: 20, y: 290, w: 740, h: 250, isMin: false, isMax: false, z: 12 },
    "win-reader": { x: 780, y: 15, w: 780, h: 420, isMin: false, isMax: false, z: 14 },
    "win-notes": { x: 780, y: 450, w: 780, h: 385, isMin: false, isMax: false, z: 15 },
    "win-playlist": { x: 20, y: 810, w: 400, h: 180, isMin: true, isMax: false, z: 10 }
  }
};

let currentMode = "desktop"; // Tryb pulpitu jest domyślny i aktywny
let highestZ = 100;
let windowStates = {};

/**
 * Zapisuje aktualny stan w localStorage
 */
function saveState() {
  try {
    const data = {
      mode: "desktop",
      windows: windowStates
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (e) {
    console.warn("Błąd zapisu stanu pulpitu:", e);
  }
}

/**
 * Wczytuje stan z localStorage
 */
function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

/**
 * Wynosi okno na sam wierzch (najwyższy z-index)
 */
export function bringToFront(winEl) {
  if (!winEl) return;
  highestZ += 2;
  winEl.style.zIndex = highestZ;

  document.querySelectorAll(".desktop-window").forEach(w => w.classList.remove("is-focused"));
  winEl.classList.add("is-focused");

  const winId = winEl.id;
  if (!windowStates[winId]) windowStates[winId] = {};
  windowStates[winId].z = highestZ;

  updateDock();
}

/**
 * Ustawia geometrię okna (pozycja, rozmiar)
 */
function applyWindowGeometry(winEl, geom) {
  if (!winEl || !geom) return;

  const winId = winEl.id;

  if (typeof geom.x === "number") winEl.style.left = `${Math.max(0, geom.x)}px`;
  if (typeof geom.y === "number") winEl.style.top = `${Math.max(0, geom.y)}px`;
  if (typeof geom.w === "number") winEl.style.width = `${Math.max(280, geom.w)}px`;
  if (typeof geom.h === "number") winEl.style.height = `${Math.max(160, geom.h)}px`;

  if (geom.isMin) {
    winEl.classList.add("is-minimized");
  } else {
    winEl.classList.remove("is-minimized");
  }

  if (geom.isMax) {
    winEl.classList.add("is-maximized");
  } else {
    winEl.classList.remove("is-maximized");
  }

  // Zaktualizuj stan wewnętrzny
  windowStates[winId] = {
    x: (geom.x !== undefined) ? geom.x : (parseInt(winEl.style.left) || 20),
    y: (geom.y !== undefined) ? geom.y : (parseInt(winEl.style.top) || 20),
    w: (geom.w !== undefined) ? geom.w : (winEl.offsetWidth || 500),
    h: (geom.h !== undefined) ? geom.h : (winEl.offsetHeight || 350),
    isMin: Boolean(geom.isMin),
    isMax: Boolean(geom.isMax),
    z: (geom.z !== undefined) ? geom.z : 10
  };
}

/**
 * Aktywuje i odświeża tryb pulpitu
 */
export function setMode(mode = "desktop") {
  currentMode = "desktop";
  const body = document.body;
  const btnDesktop = document.getElementById("btnLayoutDesktop");

  body.classList.add("desktop-mode");
  if (btnDesktop) btnDesktop.classList.add("active");

  // Zastosuj pozycje okien
  const windows = document.querySelectorAll(".desktop-window");
  windows.forEach(win => {
    const id = win.id;
    const savedGeom = windowStates[id] || DEFAULT_PRESETS.default[id] || { x: 30, y: 30, w: 500, h: 350 };
    applyWindowGeometry(win, savedGeom);
  });

  // Upewnij się, że wszystkie okna pulpitu są widoczne
  const winPlaylist = document.getElementById("win-playlist") || document.getElementById("playlistTab");
  const winNotes = document.getElementById("win-notes") || document.getElementById("notesTab");
  if (winPlaylist) winPlaylist.style.display = "flex";
  if (winNotes) winNotes.style.display = "flex";

  updateDock();
  saveState();
}

/**
 * Zastosowanie wybranego presetu ułożenia okien
 */
export function applyPreset(presetName) {
  if (presetName === "cascade") {
    const windows = Array.from(document.querySelectorAll(".desktop-window"));
    let startX = 40;
    let startY = 30;
    const offset = 40;
    const w = Math.min(850, window.innerWidth - 120);
    const h = Math.min(520, window.innerHeight - 180);

    windows.forEach((win, idx) => {
      const geom = {
        x: startX + idx * offset,
        y: startY + idx * offset,
        w: w,
        h: h,
        isMin: false,
        isMax: false,
        z: highestZ + idx
      };
      applyWindowGeometry(win, geom);
    });
    highestZ += windows.length + 2;
    saveState();
    updateDock();
    return;
  }

  if (presetName === "reset") {
    localStorage.removeItem(STORAGE_KEY);
    windowStates = {};
    const preset = DEFAULT_PRESETS.default;
    Object.keys(preset).forEach(id => {
      const win = document.getElementById(id);
      if (win) applyWindowGeometry(win, preset[id]);
    });
    setMode("desktop");
    return;
  }

  const preset = DEFAULT_PRESETS[presetName] || DEFAULT_PRESETS.default;
  Object.keys(preset).forEach(id => {
    const win = document.getElementById(id);
    if (win) applyWindowGeometry(win, preset[id]);
  });

  saveState();
  updateDock();
}

/**
 * Inicjalizuje mechanizm przeciągania okna (Drag-and-Drop)
 */
function initWindowDrag(winEl) {
  const titlebar = winEl.querySelector(".window-titlebar");
  if (!titlebar) return;

  let isDragging = false;
  let startX = 0;
  let startY = 0;
  let initialLeft = 0;
  let initialTop = 0;

  titlebar.addEventListener("pointerdown", (e) => {
    if (e.target.closest(".window-controls")) return;
    if (winEl.classList.contains("is-maximized")) return;

    isDragging = true;
    titlebar.setPointerCapture(e.pointerId);

    bringToFront(winEl);

    startX = e.clientX;
    startY = e.clientY;
    initialLeft = winEl.offsetLeft;
    initialTop = winEl.offsetTop;

    e.preventDefault();
  });

  titlebar.addEventListener("pointermove", (e) => {
    if (!isDragging) return;

    const dx = e.clientX - startX;
    const dy = e.clientY - startY;

    let newX = initialLeft + dx;
    let newY = initialTop + dy;

    // Granice ekranu
    const maxW = window.innerWidth - 60;
    const maxH = window.innerHeight - 80;

    newX = Math.max(-winEl.offsetWidth + 80, Math.min(maxW, newX));
    newY = Math.max(0, Math.min(maxH, newY));

    // Magnetyczne przyciąganie do krawędzi (12px)
    if (Math.abs(newX) < 14) newX = 0;
    if (Math.abs(newY) < 14) newY = 0;

    winEl.style.left = `${newX}px`;
    winEl.style.top = `${newY}px`;

    const winId = winEl.id;
    if (!windowStates[winId]) windowStates[winId] = {};
    windowStates[winId].x = newX;
    windowStates[winId].y = newY;
  });

  const stopDrag = (e) => {
    if (!isDragging) return;
    isDragging = false;
    try {
      titlebar.releasePointerCapture(e.pointerId);
    } catch (_) { }
    saveState();
  };

  titlebar.addEventListener("pointerup", stopDrag);
  titlebar.addEventListener("pointercancel", stopDrag);

  // Podwójne kliknięcie na pasek tytułowy przełącza maksymalizację
  titlebar.addEventListener("dblclick", (e) => {
    if (e.target.closest(".window-controls")) return;
    toggleMaximize(winEl);
  });
}

/**
 * Inicjalizuje uchwyty do zmiany rozmiaru okna (Resize)
 */
function initWindowResize(winEl) {
  const handles = winEl.querySelectorAll(".win-resize-handle");
  handles.forEach(handle => {
    let isResizing = false;
    let startX = 0;
    let startY = 0;
    let startW = 0;
    let startH = 0;
    const isSE = handle.classList.contains("handle-se");
    const isE = handle.classList.contains("handle-e");
    const isS = handle.classList.contains("handle-s");

    handle.addEventListener("pointerdown", (e) => {
      if (winEl.classList.contains("is-minimized") || winEl.classList.contains("is-maximized")) return;

      isResizing = true;
      handle.setPointerCapture(e.pointerId);
      bringToFront(winEl);

      startX = e.clientX;
      startY = e.clientY;
      startW = winEl.offsetWidth;
      startH = winEl.offsetHeight;

      e.preventDefault();
      e.stopPropagation();
    });

    handle.addEventListener("pointermove", (e) => {
      if (!isResizing) return;

      const dx = e.clientX - startX;
      const dy = e.clientY - startY;

      if (isSE || isE) {
        const newW = Math.max(280, Math.min(window.innerWidth - winEl.offsetLeft - 10, startW + dx));
        winEl.style.width = `${newW}px`;
        if (windowStates[winEl.id]) windowStates[winEl.id].w = newW;
      }

      if (isSE || isS) {
        const newH = Math.max(160, Math.min(window.innerHeight - winEl.offsetTop - 30, startH + dy));
        winEl.style.height = `${newH}px`;
        if (windowStates[winEl.id]) windowStates[winEl.id].h = newH;
      }
    });

    const stopResize = (e) => {
      if (!isResizing) return;
      isResizing = false;
      try {
        handle.releasePointerCapture(e.pointerId);
      } catch (_) { }
      saveState();
    };

    handle.addEventListener("pointerup", stopResize);
    handle.addEventListener("pointercancel", stopResize);
  });
}

/**
 * Przełącza stan minimalizacji okna
 */
export function toggleMinimize(winEl) {
  if (!winEl) return;
  const isMin = winEl.classList.toggle("is-minimized");
  const winId = winEl.id;

  if (isMin) {
    winEl.classList.remove("is-maximized");
  }

  if (!windowStates[winId]) windowStates[winId] = {};
  windowStates[winId].isMin = isMin;
  if (isMin) windowStates[winId].isMax = false;

  updateDock();
  saveState();
}

/**
 * Przełącza stan maksymalizacji okna
 */
export function toggleMaximize(winEl) {
  if (!winEl) return;
  const isMax = winEl.classList.toggle("is-maximized");
  const winId = winEl.id;

  if (isMax) {
    winEl.classList.remove("is-minimized");
    bringToFront(winEl);
  }

  if (!windowStates[winId]) windowStates[winId] = {};
  windowStates[winId].isMax = isMax;
  if (isMax) windowStates[winId].isMin = false;

  updateDock();
  saveState();
}

/**
 * Aktualizuje stan przycisków w dolnym pasku zadań (Dock)
 */
function updateDock() {
  const dock = document.getElementById("desktopDock");
  if (!dock) return;

  const buttons = dock.querySelectorAll(".dock-item-btn");
  buttons.forEach(btn => {
    const targetId = btn.getAttribute("data-target");
    const win = document.getElementById(targetId);
    if (win) {
      const isMin = win.classList.contains("is-minimized");
      const isFocused = win.classList.contains("is-focused");

      btn.classList.toggle("is-minimized", isMin);
      btn.classList.toggle("is-active", isFocused && !isMin);
    }
  });
}

/**
 * Inicjalizacja całego systemu Desktop Workspace
 */
export function initDesktopWorkspace() {
  const windows = document.querySelectorAll(".desktop-window");

  // Dodaj nasłuchiwacze do każdego okna
  windows.forEach(win => {
    win.addEventListener("pointerdown", () => {
      bringToFront(win);
    });

    initWindowDrag(win);
    initWindowResize(win);

    const minBtn = win.querySelector(".win-btn-minimize");
    const maxBtn = win.querySelector(".win-btn-maximize");

    if (minBtn) {
      minBtn.onclick = (e) => {
        e.stopPropagation();
        toggleMinimize(win);
      };
    }

    if (maxBtn) {
      maxBtn.onclick = (e) => {
        e.stopPropagation();
        toggleMaximize(win);
      };
    }
  });

  // Przełącznik Pulpitu w nagłówku
  const btnDesktop = document.getElementById("btnLayoutDesktop");
  if (btnDesktop) {
    btnDesktop.onclick = () => {
      setMode("desktop");
      const player = document.getElementById("win-player");
      if (player) bringToFront(player);
    };
  }

  // Obsługa paska zadań / docka na dole
  const dock = document.getElementById("desktopDock");
  if (dock) {
    dock.querySelectorAll(".dock-item-btn").forEach(btn => {
      btn.onclick = () => {
        const targetId = btn.getAttribute("data-target");
        const win = document.getElementById(targetId);
        if (!win) return;

        if (win.classList.contains("is-minimized")) {
          toggleMinimize(win);
          bringToFront(win);
        } else if (win.classList.contains("is-focused")) {
          toggleMinimize(win);
        } else {
          bringToFront(win);
        }
      };
    });
  }

  // Wczytaj zapisany stan lub zastosuj domyślny pulpit
  const savedState = loadState();
  if (savedState && savedState.windows) {
    windowStates = savedState.windows;
  }

  if (window.innerWidth > 768) {
    setMode("desktop");
  }
}