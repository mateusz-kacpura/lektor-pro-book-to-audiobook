import { t } from './i18n.js?v=20261009-i18n';

/**
 * Lektor Pro - Learning Notebook & Scratchpad Module
 * Obsługuje sporządzanie notatek podczas nauki, automatyczny zapis (lokalny i na serwerze),
 * cytowanie fragmentów książki, formatowanie kodu Go oraz eksport do pliku Markdown.
 */

let currentNoteMode = "global"; // "global" lub "page"
let activePageId = "page_000";
let autoSaveTimer = null;
let isPreviewMode = false;

function getActiveNoteId() {
  return currentNoteMode === "page" ? activePageId : "global";
}

export async function loadNote() {
  const noteId = getActiveNoteId();
  const textarea = document.getElementById("notesInput");
  const statusEl = document.getElementById("notesStatusText");
  const noteScopeBadge = document.getElementById("noteScopeBadge");

  if (noteScopeBadge) {
    noteScopeBadge.textContent = currentNoteMode === "page" ? `${activePageId}.md` : t("notes.global");
  }

  if (statusEl) statusEl.textContent = t("common.loading");

  try {
    const res = await fetch(`/api/notes/${noteId}`);
    if (res.ok) {
      const data = await res.json();
      if (textarea) {
        textarea.value = data.content || "";
        updateStats();
        if (isPreviewMode) renderPreview();
      }
      if (statusEl) statusEl.textContent = t("notes.synchronized");
    }
  } catch (e) {
    const local = localStorage.getItem(`lektor_note_${noteId}`) || "";
    if (textarea) {
      textarea.value = local;
      updateStats();
    }
    if (statusEl) statusEl.textContent = t("notes.offline");
  }
}

export async function saveNote(showToastFeedback = false) {
  const noteId = getActiveNoteId();
  const textarea = document.getElementById("notesInput");
  const statusEl = document.getElementById("notesStatusText");
  const saveBtn = document.getElementById("btnSaveNotes");

  if (!textarea) return;
  const content = textarea.value;

  localStorage.setItem(`lektor_note_${noteId}`, content);

  if (statusEl) statusEl.textContent = t("notes.saving");
  if (saveBtn) saveBtn.classList.add("saving");

  try {
    const res = await fetch("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note_id: noteId, content })
    });

    if (res.ok) {
      const timeStr = new Date().toLocaleTimeString();
      if (statusEl) statusEl.textContent = t("notes.saved", { time: timeStr });
      if (showToastFeedback && window.ui?.showToast) {
        window.ui.showToast(`💾 Notatka (${noteId}) została zapisana na dysku!`);
      }
    } else {
      if (statusEl) statusEl.textContent = t("notes.serverError");
    }
  } catch (e) {
    if (statusEl) statusEl.textContent = t("notes.local");
  } finally {
    if (saveBtn) saveBtn.classList.remove("saving");
  }
}

function handleInput() {
  updateStats();
  const statusEl = document.getElementById("notesStatusText");
  if (statusEl) statusEl.textContent = t("notes.unsaved");

  clearTimeout(autoSaveTimer);
  autoSaveTimer = setTimeout(() => {
    saveNote(false);
  }, 700);
}

function updateStats() {
  const textarea = document.getElementById("notesInput");
  const statsEl = document.getElementById("notesStatsCount");
  if (!textarea || !statsEl) return;

  const text = textarea.value.trim();
  const chars = text.length;
  const words = text ? text.split(/\s+/).length : 0;
  statsEl.textContent = t("notes.wordsChars", { words, chars });
}

function insertAtCursor(before, after = "") {
  const textarea = document.getElementById("notesInput");
  if (!textarea) return;

  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const val = textarea.value;
  const selected = val.substring(start, end);

  const replacement = before + selected + after;
  textarea.value = val.substring(0, start) + replacement + val.substring(end);
  textarea.selectionStart = start + before.length;
  textarea.selectionEnd = start + before.length + selected.length;
  textarea.focus();
  handleInput();
}

export function insertQuoteFromPage() {
  const sentenceEl = document.getElementById("stageSentence");
  const pageTitleEl = document.getElementById("playerPageTitle");
  const quoteText = sentenceEl?.textContent?.replace(/^"|"$/g, "").trim() || "";
  const title = pageTitleEl?.textContent || activePageId;
  const quoteLabel = t("notes.quoteFromPage", { page: activePageId, title });
  const quoteBlock = `\n> ${quoteLabel}:\n> "${quoteText}"\n\n`;
  insertAtCursor(quoteBlock);
}
export function togglePreview() {
  const textarea = document.getElementById("notesInput");
  const preview = document.getElementById("notesPreview");
  const toggleBtn = document.getElementById("btnTogglePreview");

  if (!textarea || !preview) return;
  isPreviewMode = !isPreviewMode;

  if (isPreviewMode) {
    renderPreview();
    textarea.style.display = "none";
    preview.style.display = "block";
    if (toggleBtn) {
      toggleBtn.innerHTML = `<span>✏️</span> ${t("notes.editor")}`;
      toggleBtn.classList.add("active");
    }
  } else {
    preview.style.display = "none";
    textarea.style.display = "block";
    textarea.focus();
    if (toggleBtn) {
      toggleBtn.innerHTML = `<span>👁️</span> ${t("notes.preview")}`;
      toggleBtn.classList.remove("active");
    }
  }
}
function renderPreview() {
  const textarea = document.getElementById("notesInput");
  const preview = document.getElementById("notesPreview");
  if (!textarea || !preview) return;

  const md = textarea.value.trim();
  if (!md) {
    preview.innerHTML = `<p style="color: var(--text-dim); padding: 20px;">${t("notes.empty")}</p>`;
    return;
  }

  if (window.marked && typeof window.marked.parse === "function") {
    preview.innerHTML = window.marked.parse(md);
  } else {
    preview.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${md}</pre>`;
  }
}

export function exportNote() {
  const textarea = document.getElementById("notesInput");
  if (!textarea) return;

  const noteId = getActiveNoteId();
  const content = textarea.value;
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `notatki_${noteId}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function onPageChanged(pageId) {
  activePageId = pageId;
  const btnScopePage = document.getElementById("btnScopePage");
  if (btnScopePage) {
    btnScopePage.innerHTML = `<span>📌</span> ${pageId}`;
  }
  if (currentNoteMode === "page") {
    loadNote();
  }
}

export function initNotes() {
  const textarea = document.getElementById("notesInput");
  if (textarea) {
    textarea.addEventListener("input", handleInput);
    textarea.addEventListener("keydown", (e) => {
      if (e.key === "Tab") {
        e.preventDefault();
        insertAtCursor("  ");
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        saveNote(true);
      }
    });
  }

  const btnScopeGlobal = document.getElementById("btnScopeGlobal");
  const btnScopePage = document.getElementById("btnScopePage");

  if (btnScopeGlobal) {
    btnScopeGlobal.onclick = () => {
      if (currentNoteMode === "global") return;
      currentNoteMode = "global";
      btnScopeGlobal.classList.add("active");
      if (btnScopePage) btnScopePage.classList.remove("active");
      loadNote();
    };
  }

  if (btnScopePage) {
    btnScopePage.onclick = () => {
      if (currentNoteMode === "page") return;
      currentNoteMode = "page";
      btnScopePage.classList.add("active");
      if (btnScopeGlobal) btnScopeGlobal.classList.remove("active");
      loadNote();
    };
  }

  const btnQuote = document.getElementById("btnNoteQuote");
  const btnCode = document.getElementById("btnNoteCode");
  const btnList = document.getElementById("btnNoteList");
  const btnTask = document.getElementById("btnNoteTask");
  const btnSave = document.getElementById("btnSaveNotes");
  const btnToggle = document.getElementById("btnTogglePreview");
  const btnExport = document.getElementById("btnExportNote");

  if (btnQuote) btnQuote.onclick = insertQuoteFromPage;
  if (btnCode) btnCode.onclick = () => insertAtCursor("\n```go\n", "\n```\n");
  if (btnList) btnList.onclick = () => insertAtCursor("\n- ");
  if (btnTask) btnTask.onclick = () => insertAtCursor("\n- [ ] ");
  if (btnSave) btnSave.onclick = () => saveNote(true);
  if (btnToggle) btnToggle.onclick = togglePreview;
  if (btnExport) btnExport.onclick = exportNote;

  loadNote();
}
