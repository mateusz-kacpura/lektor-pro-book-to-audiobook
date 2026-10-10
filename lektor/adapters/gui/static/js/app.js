/**
 * Lektor Pro - Main Application Orchestrator
 * Spina odtwarzacz, widok czytnika, notatnik, zarządzanie oknami pulpitu oraz moduły konwertera i syntezy.
 */
let currentLanguageMode = localStorage.getItem("lektor_language_mode") || "bilingual";

import * as notes from './notes.js?v=20261009-i18n';
import * as desktop from './desktop.js?v=20261009-i18n';
import * as mobile from './mobile.js?v=20261009-i18n';
import * as api from './api.js?v=20261009-i18n';
import * as ui from './ui.js?v=20261009-i18n';
import { AudioPlayer } from './player.js?v=20261009-i18n';
import { ready as i18nReady, t } from './i18n.js?v=20261009-i18n';

import { initBookSelector } from './modules/book_selector.js?v=20261009-i18n';
import { initAudioGenModal } from './modules/audiogen_modal.js?v=20261009-i18n';
import { initBatchController } from './modules/batch_controller.js?v=20261009-i18n';
import { initConverterModal } from './modules/converter_modal.js?v=20261009-i18n';

let allPages = [];
let currentPageId = "page_000";
let latestReadyPageId = null;
let prevReadyCount = 0;
let pollInterval = null;
let player = null;

async function loadPage(pageId, autoStart = false) {
  currentPageId = pageId;
  const searchInput = document.getElementById("searchPages");
  notes.onPageChanged(pageId);
  ui.renderPlaylist(allPages, currentPageId, searchInput?.value, (id, hasWav) => loadPage(id, hasWav));

  const pageNumStr = pageId.replace("page_", "");
  const playerBadge = document.getElementById("playerPageBadge");
  const playerTitle = document.getElementById("playerPageTitle");
  if (playerBadge) playerBadge.textContent = t("player.page", { page: pageNumStr });

  try {
    const data = await api.fetchPageDetails(pageId, currentLanguageMode);
    if (playerTitle) playerTitle.textContent = data.title || t("common.page") + ` ${pageNumStr}`;
    ui.updateReaderView(data);
    player.loadTrack(data.wav_url, autoStart, data.title || t("common.page") + ` ${pageNumStr}`);
  } catch (e) {
    console.error("Błąd wczytywania strony:", e);
  }
}

function skipNext() {
  const idx = allPages.findIndex(p => p.id === currentPageId);
  if (idx !== -1 && idx + 1 < allPages.length) {
    loadPage(allPages[idx + 1].id, allPages[idx + 1].has_wav);
  }
}

function skipPrev() {
  const idx = allPages.findIndex(p => p.id === currentPageId);
  if (idx > 0) {
    loadPage(allPages[idx - 1].id, allPages[idx - 1].has_wav);
  }
}

async function fetchStatus() {
  try {
    const data = await api.fetchStatus();
    allPages = data.pages || [];

    const bookTitle = allPages.length > 0 ? (allPages[0].title || t("nav.audiobook")) : t("nav.audiobook");
    const brandSubtitle = document.getElementById("bookTitleSubtitle");
    const navBadge = document.getElementById("navBrandBadge");

    if (brandSubtitle) {
      brandSubtitle.textContent = allPages.length > 0
        ? t("audiobook.bookSummary", { title: bookTitle, pages: data.total_pages })
        : t("audiobook.emptyBookSummary");
    }
    if (navBadge) navBadge.textContent = t("audiobook.progress", { ready: data.ready_count, total: data.total_pages, percent: data.progress?.percent || 0 });
    document.title = t("meta.titleAudiobook");

    if (prevReadyCount > 0 && data.ready_count > prevReadyCount) {
      ui.showToast(t("audiobook.completedSynthesis", { page: data.latest_ready_page }), "success");
    }
    prevReadyCount = data.ready_count;

    ui.updateProgressUI(data);
    ui.updateBatchButtonsUI(data.is_batch_running, data.is_stopping);

    const oldLatest = latestReadyPageId;
    latestReadyPageId = data.latest_ready_page;
    if (document.getElementById("modeLive")?.checked && oldLatest && latestReadyPageId !== oldLatest) {
      loadPage(latestReadyPageId, true);
    }

    const searchInput = document.getElementById("searchPages");
    ui.renderPlaylist(allPages, currentPageId, searchInput?.value, (id, hasWav) => loadPage(id, hasWav));
  } catch (e) {
    console.error("Błąd pobierania statusu:", e);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await i18nReady;
  player = new AudioPlayer({ onNext: skipNext, onPrev: skipPrev });

  ui.initTabs();
  desktop.initDesktopWorkspace();
  mobile.initMobileNavigation();
  mobile.initMobileMiniPlayer(player);
  notes.initNotes();

  window.lektorNotes = notes;
  window.lektorDesktop = desktop;

  ui.initReaderTabs();
  ui.initReaderExpansion();
  ui.initModalListeners();

  initBookSelector({
    onBookChanged: async () => {
      await fetchStatus();
      if (allPages.length > 0) loadPage(allPages[0].id, false);
    }
  });

  initAudioGenModal({ onFetchStatus: fetchStatus });

  initBatchController({
    getCurrentLanguageMode: () => currentLanguageMode,
    onFetchStatus: fetchStatus
  });

  initConverterModal({
    onReloadBooks: fetchStatus,
    onConversionFinished: async () => {
      await fetchStatus();
      if (allPages.length > 0) loadPage(allPages[0].id, false);
    }
  });

  const jumpLatestBtn = document.getElementById("btnJumpLatest");
  if (jumpLatestBtn) {
    jumpLatestBtn.onclick = () => {
      if (latestReadyPageId) loadPage(latestReadyPageId, true);
    };
  }

  const searchInput = document.getElementById("searchPages");
  if (searchInput) {
    searchInput.oninput = () => {
      ui.renderPlaylist(allPages, currentPageId, searchInput.value, (id, hasWav) => loadPage(id, hasWav));
    };
  }

  fetchStatus().then(() => {
    const initial = latestReadyPageId || (allPages.length > 0 ? allPages[0].id : null);
    if (initial) loadPage(initial, false);
  });

  document.addEventListener("lektor:locale-changed", () => {
    void fetchStatus();
  });

  pollInterval = setInterval(fetchStatus, 2000);
});