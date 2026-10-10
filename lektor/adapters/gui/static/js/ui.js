import { t } from './i18n.js?v=20261009-i18n';

export function updateLanguageBadge(langMode) {
  const badge = document.getElementById("readerLangBadge");
  if (!badge) return;
  if (langMode === "pl") {
    badge.innerHTML = t("player.languagePl");
    badge.title = t("player.languagePlTitle");
  } else if (langMode === "en") {
    badge.innerHTML = t("player.languageEn");
    badge.title = t("player.languageEnTitle");
  } else {
    badge.innerHTML = t("player.languageBi");
    badge.title = t("player.languageBiTitle");
  }
}
/**
 * Lektor Pro - UI & DOM Rendering Module
 * Odpowiada za renderowanie widoków, powiadomienia toast, formatowanie czasu oraz zakładki i suwaki.
 */

export function fmtTime(s) {
  if (isNaN(s) || s === Infinity) return "00:00";
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
}

export function showToast(message, type = "success") {
  let container = document.getElementById("toastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "toastContainer";
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast toast-${type} ${type}`;
  const icon = type === "error" ? "⚠️" : (type === "info" ? "ℹ️" : "🎉");
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.4s ease";
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

export function renderPlaylist(allPages, currentPageId, searchQuery, onSelectPage) {
  const pagesListEl = document.getElementById("pagesList");
  if (!pagesListEl) return;

  if (!allPages || allPages.length === 0) {
    pagesListEl.innerHTML = `
      <div class="playlist-empty-state">
        <span class="empty-icon">📖</span>
        <h4>${t("playlist.emptyTitle")}</h4>
        <p>${t("playlist.emptyText")}</p>
        <button class="btn-converter-trigger" onclick="document.getElementById('btnOpenConverterModal')?.click()" style="margin-top: 12px; cursor: pointer;">
          ${t("playlist.openConverter")}
        </button>
      </div>
    `;
    return;
  }

  const q = (searchQuery || "").toLowerCase().trim();
  const filtered = allPages.filter(page =>
    page.id.toLowerCase().includes(q) || (page.title && page.title.toLowerCase().includes(q))
  );

  pagesListEl.innerHTML = "";
  if (filtered.length === 0) {
    pagesListEl.innerHTML = `
      <div class="playlist-empty-state">
        <span class="empty-icon">🔍</span>
        <h4>${t("playlist.noResults")}</h4>
        <p>${t("playlist.noResultsText", { query: searchQuery || "" })}</p>
      </div>
    `;
    return;
  }

  filtered.forEach(page => {
    const item = document.createElement("div");
    const isGenerating = page.status === "generating";
    item.className = `page-item ${page.id === currentPageId ? "active" : ""} ${isGenerating ? "is-generating" : ""}`;

    let badgeHtml = "";
    if (page.has_wav) {
      badgeHtml = `<span class="badge-ready">🔊 ${page.duration_str}</span>`;
    } else if (isGenerating) {
      badgeHtml = `<span class="badge-generating">${t("playlist.generating")}</span>`;
    } else {
      badgeHtml = `<span class="badge-pending">${t("playlist.queue")}</span>`;
    }

    const cleanNum = page.id.replace(/^page_/, "").replace(/^rozdzial_/, "R.");
    const title = page.title || page.id;
    item.innerHTML = `
      <div class="page-item-info">
        <span class="page-item-num">${cleanNum}</span>
        <span class="page-item-name" title="${title}">${title}</span>
      </div>
      ${badgeHtml}
    `;
    item.onclick = () => onSelectPage(page.id, page.has_wav);
    pagesListEl.appendChild(item);
  });
}
export function updateProgressUI(data) {
  const readyCountEl = document.getElementById("readyCount");
  const totalCountEl = document.getElementById("totalCount");
  const headerPercentEl = document.getElementById("headerPercent");
  const genBarFill = document.getElementById("genBarFill");
  const genPercent = document.getElementById("genPercent");
  const statPagesReady = document.getElementById("statPagesReady");
  const statTotalAudio = document.getElementById("statTotalAudio");
  const statEta = document.getElementById("statEta");
  const statLastPageTime = document.getElementById("statLastPageTime");
  const statAveragePageTime = document.getElementById("statAveragePageTime");
  const statVram = document.getElementById("statVram");
  const statGpu = document.getElementById("statGpu");
  const statVoiceName = document.getElementById("statVoiceName");
  const genStatusText = document.getElementById("genStatusText");
  const genActiveTask = document.getElementById("genActiveTask");
  const genPulse = document.getElementById("genPulse");
  const genStageBox = document.getElementById("genStageBox");
  const stagePageName = document.getElementById("stagePageName");
  const stageSegInfo = document.getElementById("stageSegInfo");
  const stageBarFill = document.getElementById("stageBarFill");
  const stageSentence = document.getElementById("stageSentence");
  const stageStatusNote = document.getElementById("stageStatusNote");
  const tabPlaylistBtn = document.getElementById("tabPlaylistBtn");

  if (readyCountEl) readyCountEl.textContent = data.ready_count;
  if (totalCountEl) totalCountEl.textContent = data.total_pages;
  if (tabPlaylistBtn) tabPlaylistBtn.textContent = t("playlist.tabWithCount", { count: data.total_pages });

  if (statVoiceName && data.current_params?.voice_path) {
    const rawVoice = data.current_params.voice_path;
    const voiceFileName = rawVoice.split(/[/\\\\]/).pop() || "audio.wav";
    statVoiceName.textContent = voiceFileName;
  }

  if (!data.progress) return;
  const progress = data.progress;
  if (genBarFill) genBarFill.style.width = `${progress.percent}%`;
  if (genPercent) genPercent.textContent = `${progress.percent}%`;
  if (headerPercentEl) headerPercentEl.textContent = `${progress.percent}%`;
  if (statPagesReady) statPagesReady.textContent = `${progress.ready_count} / ${progress.total_count}`;
  if (statTotalAudio) statTotalAudio.textContent = progress.total_audio_str;
  if (statEta) statEta.textContent = progress.eta_str;
  if (statLastPageTime) statLastPageTime.textContent = progress.last_page_duration_sec > 0 ? `${Number(progress.last_page_duration_sec).toFixed(1)} s` : "-- s";
  if (statAveragePageTime) statAveragePageTime.textContent = progress.average_page_duration_sec > 0 ? `${Number(progress.average_page_duration_sec).toFixed(1)} s` : "-- s";

  const usedVramGb = Number(progress.vram_used_mb || 0) / 1024;
  const totalVramGb = Number(progress.vram_total_mb || 0) / 1024;
  if (statVram) statVram.textContent = totalVramGb > 0 ? `${usedVramGb.toFixed(1)} / ${totalVramGb.toFixed(1)} GB` : "-- / -- GB";
  if (statGpu) statGpu.textContent = `${Number(progress.gpu_utilization_pct || 0).toFixed(1)}%`;

  if (progress.is_active && progress.active_page) {
    if (genPulse) genPulse.classList.remove("idle");
    if (genStatusText) {
      genStatusText.textContent = t("audiobook.statusActive");
      genStatusText.style.color = "#38bdf8";
    }
    if (genActiveTask) {
      genActiveTask.innerHTML = t("audiobook.activePage", {
        page: progress.active_page.title || progress.active_page.id,
        number: progress.active_page.page_num,
      });
    }
    if (genStageBox) genStageBox.classList.remove("idle");
    if (stagePageName) stagePageName.textContent = t("audiobook.stagePage", {
      number: progress.active_page.page_num,
      title: progress.active_page.title || progress.active_page.id,
    });
    const segmentPercent = progress.active_page.segment_percent || 0;
    if (stageSegInfo) stageSegInfo.textContent = t("audiobook.segment", {
      current: progress.active_page.current_segment,
      total: progress.active_page.total_segments,
      percent: segmentPercent,
    });
    if (stageBarFill) stageBarFill.style.width = `${segmentPercent}%`;
    if (stageSentence) stageSentence.textContent = progress.active_page.current_sentence
      ? `"${progress.active_page.current_sentence}"`
      : t("audiobook.nextSegment");
    if (stageStatusNote) stageStatusNote.textContent = t("audiobook.stageSegment", {
      current: progress.active_page.current_segment,
      total: progress.active_page.total_segments,
    });
  } else if (progress.total_count > 0 && progress.ready_count >= progress.total_count) {
    if (genPulse) genPulse.classList.add("idle");
    if (genStatusText) {
      genStatusText.textContent = t("audiobook.allComplete");
      genStatusText.style.color = "#10b981";
    }
    if (genActiveTask) genActiveTask.innerHTML = t("audiobook.allPagesGenerated", { count: progress.total_count });
    if (genStageBox) genStageBox.classList.add("idle");
    if (stagePageName) stagePageName.textContent = t("audiobook.allPagesComplete");
    if (stageSegInfo) stageSegInfo.textContent = "100%";
    if (stageBarFill) stageBarFill.style.width = "100%";
    if (stageSentence) stageSentence.textContent = t("audiobook.audioComplete");
    if (stageStatusNote) stageStatusNote.textContent = t("audiobook.readyStatus");
  } else {
    if (genPulse) genPulse.classList.add("idle");
    if (genStatusText) {
      genStatusText.textContent = t("audiobook.idleStatus");
      genStatusText.style.color = "#94a3b8";
    }
    if (genActiveTask) genActiveTask.innerHTML = t("audiobook.lastGenerated", {
      page: data.latest_ready_page || t("common.noActiveRecording"),
    });
    if (genStageBox) genStageBox.classList.add("idle");
    if (stagePageName) stagePageName.textContent = data.latest_ready_page
      ? t("audiobook.lastGenerated", { page: data.latest_ready_page })
      : t("audiobook.waiting");
    if (stageSegInfo) stageSegInfo.textContent = t("audiobook.waiting");
    if (stageBarFill) stageBarFill.style.width = "0%";
    if (stageSentence) stageSentence.textContent = t("audiobook.noActiveSynthesis");
    if (stageStatusNote) stageStatusNote.textContent = t("audiobook.idleStatus");
  }
}
export function updateTranscript(segments, rawText) {
  const transcriptContainer = document.getElementById("transcriptContainer");
  if (!transcriptContainer) return;

  transcriptContainer.innerHTML = "";
  if (segments && segments.length > 0) {
    segments.forEach(seg => {
      const el = document.createElement("div");
      el.className = "transcript-item";
      el.textContent = seg;
      transcriptContainer.appendChild(el);
    });
  } else {
    transcriptContainer.innerHTML = `<p style="color: var(--text-dim);">${rawText ? rawText.substring(0, 300) + "..." : t("reader.transcriptPlaceholder")}</p>`;
  }
}

export function initTabs() {
  const tabPlaylistBtn = document.getElementById("tabPlaylistBtn");
  const tabNotesBtn = document.getElementById("tabNotesBtn");
  const winPlaylist = document.getElementById("win-playlist") || document.getElementById("playlistTab");
  const winNotes = document.getElementById("win-notes") || document.getElementById("notesTab");

  function switchTab(activeBtn, activeWin) {
    [tabPlaylistBtn, tabNotesBtn].forEach(b => b?.classList.remove("active"));
    activeBtn?.classList.add("active");

    if (!document.body.classList.contains("desktop-mode")) {
      [winPlaylist, winNotes].forEach(w => {
        if (w) w.style.display = "none";
      });
      if (activeWin) activeWin.style.display = "flex";
    }
  }

  if (tabPlaylistBtn) tabPlaylistBtn.onclick = () => switchTab(tabPlaylistBtn, winPlaylist);
  if (tabNotesBtn) tabNotesBtn.onclick = () => switchTab(tabNotesBtn, winNotes);
}

let onConfirmCallback = null;

export function openConfirmModal({ icon, iconClass, title, desc, infoHtml, confirmText, isDanger, onConfirm }) {
  const backdrop = document.getElementById("confirmModalBackdrop");
  const iconWrap = document.getElementById("modalIconWrap");
  const titleEl = document.getElementById("modalTitle");
  const descEl = document.getElementById("modalDesc");
  const infoBox = document.getElementById("modalInfoBox");
  const confirmBtn = document.getElementById("btnModalConfirm");

  if (!backdrop) return;

  if (iconWrap) {
    iconWrap.textContent = icon || "🚀";
    iconWrap.className = `modal-icon-wrap ${iconClass || "start"}`;
  }
  if (titleEl) titleEl.textContent = title;
  if (descEl) descEl.textContent = desc;
  if (infoBox && infoHtml) infoBox.innerHTML = infoHtml;

  if (confirmBtn) {
    confirmBtn.textContent = confirmText || "Potwierdź";
    if (isDanger) {
      confirmBtn.classList.add("danger");
    } else {
      confirmBtn.classList.remove("danger");
    }
  }

  onConfirmCallback = onConfirm;
  backdrop.style.display = "flex";
}

export function closeConfirmModal() {
  const backdrop = document.getElementById("confirmModalBackdrop");
  if (backdrop) backdrop.style.display = "none";
  onConfirmCallback = null;
}

export function initModalListeners() {
  const backdrop = document.getElementById("confirmModalBackdrop");
  const cancelBtn = document.getElementById("btnModalCancel");
  const confirmBtn = document.getElementById("btnModalConfirm");

  if (cancelBtn) cancelBtn.onclick = closeConfirmModal;
  if (confirmBtn) {
    confirmBtn.onclick = () => {
      if (onConfirmCallback) onConfirmCallback();
      closeConfirmModal();
    };
  }

  if (backdrop) {
    backdrop.onclick = (e) => {
      if (e.target === backdrop) closeConfirmModal();
    };
  }

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && backdrop && backdrop.style.display !== "none") {
      closeConfirmModal();
    }
  });
}

export function updateBatchButtonsUI(isBatchRunning, isStopping) {
  const startBtn = document.getElementById("btnStartBatch");
  const stopBtn = document.getElementById("btnStopBatch");
  const headerStartBtn = document.getElementById("btnHeaderBatchStart");
  const headerStopBtn = document.getElementById("btnHeaderBatchStop");

  if (isBatchRunning) {
    if (startBtn) startBtn.style.display = "none";
    if (stopBtn) {
      stopBtn.style.display = "inline-flex";
      stopBtn.innerHTML = isStopping ? `<span class="batch-icon">⏳</span><span>${t("converter.stopping")}</span>` : `<span class="batch-icon">⏹</span><span>${t("converter.stop")}</span>`;
      stopBtn.disabled = isStopping;
    }
    if (headerStartBtn) headerStartBtn.style.display = "none";
    if (headerStopBtn) {
      headerStopBtn.style.display = "inline-flex";
      headerStopBtn.disabled = isStopping;
    }
  } else {
    if (startBtn) startBtn.style.display = "inline-flex";
    if (stopBtn) stopBtn.style.display = "none";
    if (headerStartBtn) headerStartBtn.style.display = "inline-flex";
    if (headerStopBtn) headerStopBtn.style.display = "none";
  }
}


export function renderMarkdown(rawMd) {
  const container = document.getElementById("markdownContainer");
  if (!container) return;

  if (!rawMd || !rawMd.trim()) {
    container.innerHTML = `<p style="color: var(--text-dim);">${t("reader.markdownPlaceholder")}</p>`;
    return;
  }

  // Wytnij YAML frontmatter (--- ... ---) oraz nagłówek komentarza HTML <!-- { ... } -->
  let cleanMd = rawMd.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, '');
  cleanMd = cleanMd.replace(/^\s*<!--[\s\S]*?-->\s*/, '');
  cleanMd = cleanMd.replaceAll('../images/', '/images/').replaceAll('../pdf_pages_jpg/', '/pdf_pages_jpg/');

  if (window.marked && typeof window.marked.parse === 'function') {
    container.innerHTML = window.marked.parse(cleanMd);
  } else {
    container.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${cleanMd}</pre>`;
  }
}

export function initReaderTabs() {
  const btnMarkdown = document.getElementById("btnTabMarkdown");
  const btnTranscript = document.getElementById("btnTabTranscript");
  const mdContainer = document.getElementById("markdownContainer");
  const tsContainer = document.getElementById("transcriptContainer");

  if (!btnMarkdown || !btnTranscript || !mdContainer || !tsContainer) return;

  btnMarkdown.onclick = () => {
    btnMarkdown.classList.add("active");
    btnTranscript.classList.remove("active");
    mdContainer.style.display = "block";
    tsContainer.style.display = "none";
  };

  btnTranscript.onclick = () => {
    btnTranscript.classList.add("active");
    btnMarkdown.classList.remove("active");
    mdContainer.style.display = "none";
    tsContainer.style.display = "flex";
  };
}

export function updateReaderView(data) {
  const fileNameEl = document.getElementById("readerFileName");
  if (fileNameEl) {
    fileNameEl.textContent = `${data.id}.md`;
  }
  updateLanguageBadge(data.language_mode || "bilingual");
  renderMarkdown(data.raw_text);
  updateTranscript(data.segments, data.raw_text);
}


let currentFontSize = 0.95;

export function changeReaderFontSize(delta) {
  const mdContainer = document.getElementById("markdownContainer");
  const tsContainer = document.getElementById("transcriptContainer");

  currentFontSize = Math.min(1.4, Math.max(0.8, currentFontSize + delta));
  const sizeStr = `${currentFontSize.toFixed(2)}rem`;

  if (mdContainer) mdContainer.style.fontSize = sizeStr;
  if (tsContainer) tsContainer.style.fontSize = sizeStr;
}

export function toggleReaderExpansion() {
  const card = document.getElementById("readerCard");
  const backdrop = document.getElementById("readerBackdrop");
  const expandIcon = document.getElementById("expandIcon");
  const expandText = document.getElementById("expandText");

  if (!card) return;

  const isExpanded = card.classList.toggle("is-expanded");

  if (backdrop) {
    backdrop.style.display = isExpanded ? "block" : "none";
  }

  if (expandIcon && expandText) {
    if (isExpanded) {
      expandIcon.textContent = "🗗";
      expandText.textContent = t("reader.collapse");
    } else {
      expandIcon.textContent = "⛶";
      expandText.textContent = t("reader.expand");
    }
  }
}

export function initReaderExpansion() {
  const btnExpand = document.getElementById("btnExpandReader");
  const btnFontDec = document.getElementById("btnFontDecrease");
  const btnFontInc = document.getElementById("btnFontIncrease");
  const backdrop = document.getElementById("readerBackdrop");

  if (btnExpand) btnExpand.onclick = toggleReaderExpansion;
  if (btnFontDec) btnFontDec.onclick = () => changeReaderFontSize(-0.08);
  if (btnFontInc) btnFontInc.onclick = () => changeReaderFontSize(0.08);

  if (backdrop) {
    backdrop.onclick = () => {
      const card = document.getElementById("readerCard");
      if (card && card.classList.contains("is-expanded")) {
        toggleReaderExpansion();
      }
    };
  }

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const card = document.getElementById("readerCard");
      if (card && card.classList.contains("is-expanded")) {
        toggleReaderExpansion();
      }
    }
  });
}
