/**
 * Lektor Pro - Unified API Client Module
 * Obsługuje komunikację HTTP z backendem FastAPI dla wszystkich modułów aplikacji:
 * Audiobook Player & Generator, Studio TTS, Mission Control, Arena Treningowa, Notatnik.
 */

/* =========================================================================
   AUDIOBOOK PLAYER & BATCH GENERATOR
   ========================================================================= */

export async function fetchStatus() {
  const res = await fetch("/api/status");
  if (!res.ok) {
    throw new Error(`Błąd pobierania statusu: ${res.status}`);
  }
  return await res.json();
}

export async function fetchLanguageOptions(provider = "omnivoice") {
  const query = encodeURIComponent(provider);
  const res = await fetch(`/api/languages?provider=${query}`);
  if (!res.ok) {
    throw new Error(`Błąd pobierania listy języków: ${res.status}`);
  }
  return await res.json();
}
export async function fetchPageDetails(pageId, langMode = null) {
  const url = langMode ? `/api/page/${pageId}?lang_mode=${encodeURIComponent(langMode)}` : `/api/page/${pageId}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Błąd pobierania szczegółów strony ${pageId}: ${res.status}`);
  }
  return await res.json();
}

export async function sendRegenerateRequest(pageId, payload) {
  const res = await fetch(`/api/regenerate/${pageId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    throw new Error(`Błąd zlecenia regeneracji: ${res.status}`);
  }
  return await res.json();
}

export async function startBatch(payload) {
  const res = await fetch("/api/batch/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Błąd uruchomienia (${res.status})`);
  }
  return await res.json();
}

export async function stopBatch() {
  const res = await fetch("/api/batch/stop", {
    method: "POST"
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Błąd zatrzymania (${res.status})`);
  }
  return await res.json();
}

/* =========================================================================
   LEARNING NOTES
   ========================================================================= */

export async function fetchNote(noteId) {
  const res = await fetch(`/api/notes/${noteId}`);
  if (!res.ok) {
    throw new Error(`Błąd odczytu notatki: ${res.status}`);
  }
  return await res.json();
}

export async function saveNote(noteId, content) {
  const res = await fetch(`/api/notes/${noteId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content })
  });
  if (!res.ok) {
    throw new Error(`Błąd zapisu notatki: ${res.status}`);
  }
  return await res.json();
}

/* =========================================================================
   STUDIO TTS MARKDOWN
   ========================================================================= */

export async function fetchStudioHistory() {
  const res = await fetch("/api/studio/history");
  if (!res.ok) {
    throw new Error(`Błąd pobierania historii studio: ${res.status}`);
  }
  return await res.json();
}

export async function synthesizeStudioTTS(payload) {
  const res = await fetch("/api/studio/synthesize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Błąd syntezy studio (${res.status})`);
  }
  return await res.json();
}

export async function deleteStudioItem(id) {
  const res = await fetch(`/api/studio/item/${id}`, {
    method: "DELETE"
  });
  if (!res.ok) {
    throw new Error(`Błąd usuwania nagrania (${res.status})`);
  }
  return await res.json();
}

/* =========================================================================
   DYNAMIC BOOK MANAGEMENT & CONVERTER
   ========================================================================= */

export async function fetchBooksList() {
  const res = await fetch("/api/books");
  if (!res.ok) {
    throw new Error(`Błąd pobierania listy książek: ${res.status}`);
  }
  return await res.json();
}

export async function switchActiveBook(slug) {
  const res = await fetch("/api/active-book", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slug })
  });
  if (!res.ok) {
    throw new Error(`Błąd zmiany aktywnej książki: ${res.status}`);
  }
  return await res.json();
}

export async function fetchConverterBookInfo(slug) {
  const res = await fetch(`/api/converter/info/${encodeURIComponent(slug)}`);
  if (!res.ok) {
    throw new Error(`Błąd pobierania informacji o PDF książki: ${res.status}`);
  }
  return await res.json();
}

export async function startConversion(payload) {
  const res = await fetch("/api/converter/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Błąd uruchamiania konwersji: ${res.status}`);
  }
  return await res.json();
}

export async function cancelConversion(taskId) {
  const res = await fetch(`/api/converter/cancel/${encodeURIComponent(taskId)}`, {
    method: "POST"
  });
  if (!res.ok) {
    throw new Error(`Błąd anulowania konwersji: ${res.status}`);
  }
  return await res.json();
}

export function subscribeConversionProgress(taskId, onMessage, onError) {
  const evtSource = new EventSource(`/api/converter/progress/${encodeURIComponent(taskId)}`);
  evtSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (typeof onMessage === "function") {
        onMessage(data);
      }
    } catch (e) {
      console.error("[SSE] Błąd parsowania danych telemetrii:", e);
    }
  };
  evtSource.onerror = (err) => {
    if (typeof onError === "function") {
      onError(err);
    }
  };
  return evtSource;
}

export async function importPdfBook(file, title = null, author = null, slug = null) {
  const formData = new FormData();
  formData.append("file", file);
  if (title) formData.append("title", title);
  if (author) formData.append("author", author);
  if (slug) formData.append("slug", slug);

  const res = await fetch("/api/converter/import-pdf", {
    method: "POST",
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Błąd importu pliku PDF: ${res.status}`);
  }
  return await res.json();
}

export async function renderPdfScans(payload) {
  const res = await fetch("/api/converter/render-scans", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Błąd renderowania skanów: ${res.status}`);
  }
  return await res.json();
}

export function subscribeScanRenderingProgress(slug, options, onMessage, onError) {
  const { dpi = 300, start_page = null, end_page = null } = options || {};
  const params = new URLSearchParams({ slug: slug, dpi: dpi.toString() });
  if (start_page) params.set("start_page", start_page.toString());
  if (end_page) params.set("end_page", end_page.toString());

  const evtSource = new EventSource(`/api/converter/render-scans-stream?${params.toString()}`);
  evtSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (typeof onMessage === "function") {
        onMessage(data);
      }
    } catch (e) {
      console.error("[SSE] Błąd parsowania zdarzenia renderowania:", e);
    }
  };
  evtSource.onerror = (err) => {
    if (typeof onError === "function") {
      onError(err);
    }
  };
  return evtSource;
}


