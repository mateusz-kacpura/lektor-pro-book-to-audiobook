/**
 * STUDIO TTS MARKDOWN — Interaktywny pulpit syntezy mowy z Markdown
 * Lektor Pro (Q4 2026)
 */

document.addEventListener("DOMContentLoaded", async () => {
  if (window.lektorI18n?.ready) await window.lektorI18n.ready;
  const tr = (key, params = {}) => window.lektorI18n?.t(key, params) ?? key;
  // =========================================================================
  // STATE MANAGEMENT
  // =========================================================================
  const state = {
    activeItem: null,
    historyItems: [],
    isPlaying: false,
    isLooping: false,
    currentSpeed: 1.0,
    volume: 1.0,
    isMuted: false,
    primaryLanguage: "pl",
    secondaryLanguage: "en",
    baseSpeed: 1.0,
    isSynthesizing: false,
    synthesisStartedAt: 0,
    synthesisClockId: null,
    telemetryTimerId: null,
    telemetryRequestInFlight: false,
    lastSynthesisSeconds: null,
    averageSynthesisSeconds: null,
    pendingDeleteId: null
  };

  // Presets / Szablony
  const PRESETS = {
    cloud_native: {
      title: "Architektura Cloud Native & Kubernetes",
      markdown: `# Architektura Cloud Native w środowisku produkcyjnym

Nowoczesne aplikacje chmurowe projektowane są w oparciu o architekturę mikroserwisów i konteneryzację w Dockerze.

Główne filary odporności:
- **Zero-downtime deployments**: Wykorzystanie mechanizmu \`RollingUpdate\` w Kubernetes.
- **Graceful Shutdown**: Prawidłowa obsługa sygnałów \`SIGTERM\` w Go zapobiega ucinaniu aktywnych transakcji HTTP.
- **Circuit Breaker**: Ochrona serwisów nadrzędnych przed kaskadową awarią za pomocą biblioteki \`gobreaker\`.

\`\`\`go
func HandleGracefulShutdown(server *http.Server) {
    stop := make(chan os.Signal, 1)
    signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
    <-stop
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    server.Shutdown(ctx)
}
\`\`\`

Dzięki takiemu podejściu aplikacja osiąga dostępność na poziomie dziewięćdziesiąt dziewięć i dziewięćdziesiąt dziewięć setnych procent.`
    },
    go_concurrency: {
      title: "Współbieżność w Go: Goroutines i Channels",
      markdown: `# Współbieżność w języku Go

Współbieżność w Go bazuje na modelu CSP (Communicating Sequential Processes). Zamiast współdzielenia pamięci przez mutexy, komunikujemy się za pomocą kanałów.

Kluczowe właściwości:
- **Lekkie wątki**: Startowa pamięć \`Goroutine\` wynosi zaledwie 2 KB w porównaniu do 2 MB dla wątku systemowego POSIX.
- **Scheduler M:N**: Zarządza tysiącami goroutine na ograniczonej liczbie rdzeni CPU za pomocą mechanizmu work-stealing.
- **Select statement**: Umożliwia nieblokujący odczyt z wielu kanałów jednocześnie.

\`\`\`go
select {
case msg := <-chJob:
    process(msg)
case <-ctx.Done():
    return ctx.Err()
}
\`\`\`

Model ten pozwala na obsługę setek tysięcy równoległych połączeń WebSocket na pojedynczym serwerze.`
    },
    interview_pitch: {
      title: "Dlaczego jesteś właściwym kandydatem na stanowisko?",
      markdown: `# Dlaczego jestem idealnym kandydatem na to stanowisko?

Posiadam ponad siedem lat komercyjnego doświadczenia w projektowaniu skalowalnych systemów w języku Go oraz architekturze Cloud Native.

Trzy powody, dla których warto wybrać moją kandydaturę:
1. **Praktyczna znajomość systemów rozproszonych**: Wdrażałem mikroserwisy obsługujące ponad pięćdziesiąt tysięcy zapytań na sekundę przy zachowaniu opóźnień poniżej dziesięciu milisekund.
2. **Kultura Spec-First i czystego kodu**: Każde API definiuję w standardzie OpenAPI lub gRPC Protobuf przed rozpoczęciem implementacji, eliminując nieporozumienia w zespole.
3. **Optymalizacja kosztów i zasobów**: Zmniejszyłem zużycie pamięci RAM w klastrze Kubernetes o czterdzieści procent dzięki profilowaniu za pomocą \`pprof\` i alokacji bez zbędnych kopii.

Mój styl pracy to przewidywalność, wysoka dbałość o detale i pełna odpowiedzialność produkcyjna za wdrożone rozwiązania.`
    },
    distributed_cache: {
      title: "Distributed Caching i Strategie Redis",
      markdown: `# Distributed Caching i Strategie Redis

Pamięć podręczna w systemach wysokiej skali redukuje obciążenie głównej bazy danych PostgreSQL.

Stosowane strategie:
- **Cache-Aside (Lazy Loading)**: Aplikacja odpytuje Redis; w razie chybienia (Cache Miss) czyta z bazy i uzupełnia klucz.
- **Probabilistic Early Expiration (XFetch)**: Regeneruje klucz w tle tuż przed wygaśnięciem TTL, zapobiegając problemowi \`Thundering Herd\`.
- **Sliding Window Rate Limiter**: Ochrona endpointów za pomocą skryptów Lua w Redis.`
    },
    blank: {
      title: "",
      markdown: ""
    }
  };

  // =========================================================================
  // DOM ELEMENTS
  // =========================================================================
  const titleInput = document.getElementById("studioTitleInput");
  const btnAutoTitle = document.getElementById("btnAutoTitle");
  const presetSelector = document.getElementById("presetSelector");
  const markdownInput = document.getElementById("markdownInput");
  const markdownPreviewBox = document.getElementById("markdownPreviewBox");
  const speechPreviewBox = document.getElementById("speechPreviewBox");

  const tabEditor = document.getElementById("tabEditor");
  const tabPreview = document.getElementById("tabPreview");
  const tabSpeech = document.getElementById("tabSpeech");
  const paneEditor = document.getElementById("paneEditor");
  const panePreview = document.getElementById("panePreview");
  const paneSpeech = document.getElementById("paneSpeech");

  const metricChars = document.getElementById("metricChars");
  const metricWords = document.getElementById("metricWords");
  const metricEstTime = document.getElementById("metricEstTime");
  const btnClearText = document.getElementById("btnClearText");

  const langGroup = document.getElementById("langGroup");
  const baseSpeedGroup = document.getElementById("baseSpeedGroup");
  const paramTemp = document.getElementById("paramTemp");
  const paramCfg = document.getElementById("paramCfg");
  const paramExag = document.getElementById("paramExag");
  const valTemp = document.getElementById("valTemp");
  const valCfg = document.getElementById("valCfg");
  const valExag = document.getElementById("valExag");

  const btnSynthesize = document.getElementById("btnSynthesize");
  const btnSynthIcon = document.getElementById("btnSynthIcon");
  const btnSynthText = document.getElementById("btnSynthText");
  const statusDot = document.getElementById("statusDot");
  const statusMsg = document.getElementById("statusMsg");
  const synthStats = document.getElementById("synthStats");
  const synthStatsState = document.getElementById("synthStatsState");
  const statSynthElapsed = document.getElementById("statSynthElapsed");
  const statSynthAverage = document.getElementById("statSynthAverage");
  const statSynthVram = document.getElementById("statSynthVram");
  const statSynthGpu = document.getElementById("statSynthGpu");

  // Player Elements
  const audioElement = document.getElementById("audioElement");
  const playerCard = document.getElementById("playerCard");
  const playerTitle = document.getElementById("playerTitle");
  const metaLang = document.getElementById("metaLang");
  const metaDuration = document.getElementById("metaDuration");
  const metaSize = document.getElementById("metaSize");
  const metaDate = document.getElementById("metaDate");
  const visualizer = document.getElementById("visualizer");

  const playerCurTime = document.getElementById("playerCurTime");
  const playerTotalTime = document.getElementById("playerTotalTime");
  const timelineFill = document.getElementById("timelineFill");
  const timelineSlider = document.getElementById("timelineSlider");

  const btnPlayPause = document.getElementById("btnPlayPause");
  const playIcon = document.getElementById("playIcon");
  const btnSkipBack = document.getElementById("btnSkipBack");
  const btnSkipForward = document.getElementById("btnSkipForward");
  const btnLoop = document.getElementById("btnLoop");
  const playerSpeeds = document.getElementById("playerSpeeds");
  const btnMute = document.getElementById("btnMute");
  const volSlider = document.getElementById("volSlider");
  const btnDownload = document.getElementById("btnDownload");
  const btnRegenCurrent = document.getElementById("btnRegenCurrent");

  // History Elements
  const historyList = document.getElementById("historyList");
  const historyEmpty = document.getElementById("historyEmpty");
  const historyCount = document.getElementById("historyCount");
  const statDiskCount = document.getElementById("statDiskCount");
  const historySearchInput = document.getElementById("historySearchInput");
  const btnRefreshHistory = document.getElementById("btnRefreshHistory");

  // Modal Elements
  const deleteModalBackdrop = document.getElementById("deleteModalBackdrop");
  const deleteModalText = document.getElementById("deleteModalText");
  const btnCancelDelete = document.getElementById("btnCancelDelete");
  const btnConfirmDelete = document.getElementById("btnConfirmDelete");
  const toastContainer = document.getElementById("toastContainer");

  // =========================================================================
  // HELPER FUNCTIONS & TOASTS
  // =========================================================================
  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon = type === "success" ? "✅" : (type === "error" ? "❌" : "ℹ️");
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function formatTime(seconds) {
    if (isNaN(seconds) || seconds < 0) return "00:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }

  function formatSynthesisDuration(seconds) {
    const value = Number(seconds);
    if (!Number.isFinite(value) || value < 0) return "--";
    if (value < 60) return `${value.toFixed(1)} s`;
    return `${Math.floor(value / 60)} min ${Math.floor(value % 60)} s`;
  }
  function renderSynthesisStats() {
    if (!statSynthElapsed || !statSynthAverage) return;
    const elapsed = state.isSynthesizing && state.synthesisStartedAt > 0
      ? (performance.now() - state.synthesisStartedAt) / 1000
      : state.lastSynthesisSeconds;
    statSynthElapsed.textContent = formatSynthesisDuration(elapsed);
    statSynthAverage.textContent = formatSynthesisDuration(state.averageSynthesisSeconds);
  }

  function applyStudioStats(data) {
    const stats = data?.stats || {};
    const gpu = data?.gpu || {};
    if (Number.isFinite(Number(stats.average_synthesis_sec))) {
      state.averageSynthesisSeconds = Number(stats.average_synthesis_sec);
    }
    renderSynthesisStats();

    if (statSynthVram && data?.gpu) {
      const used = Number(gpu.used_vram_mb);
      const total = Number(gpu.total_vram_mb);
      statSynthVram.textContent = Number.isFinite(used) && Number.isFinite(total) && total > 0
        ? `${(used / 1024).toFixed(1)} / ${(total / 1024).toFixed(1)} GB`
        : "-- / -- GB";
    }
    if (statSynthGpu && data?.gpu) {
      const utilization = Number(gpu.utilization_pct);
      statSynthGpu.textContent = Number.isFinite(utilization) && Number(gpu.total_vram_mb) > 0
        ? `${utilization.toFixed(1)}%`
        : "--";
    }
  }
  async function fetchStudioStats() {
    if (!state.isSynthesizing || state.telemetryRequestInFlight) return;
    state.telemetryRequestInFlight = true;
    try {
      const response = await fetch("/api/studio/stats", { cache: "no-store" });
      if (!response.ok) return;
      applyStudioStats(await response.json());
    } catch (err) {
      console.debug("Nie udało się pobrać statystyk Studio", err);
    } finally {
      state.telemetryRequestInFlight = false;
    }
  }

  function startSynthesisStats() {
    state.synthesisStartedAt = performance.now();
    state.lastSynthesisSeconds = null;
    synthStats.hidden = false;
    synthStatsState.textContent = tr("studio.inProgress");
    renderSynthesisStats();
    state.synthesisClockId = window.setInterval(renderSynthesisStats, 250);
    state.telemetryTimerId = window.setInterval(() => { void fetchStudioStats(); }, 1000);
    void fetchStudioStats();
  }

  function stopSynthesisStats() {
    const elapsed = state.synthesisStartedAt > 0
      ? (performance.now() - state.synthesisStartedAt) / 1000
      : null;
    if (elapsed !== null && state.lastSynthesisSeconds === null) state.lastSynthesisSeconds = elapsed;
    state.synthesisStartedAt = 0;
    if (state.synthesisClockId !== null) window.clearInterval(state.synthesisClockId);
    if (state.telemetryTimerId !== null) window.clearInterval(state.telemetryTimerId);
    state.synthesisClockId = null;
    state.telemetryTimerId = null;
    synthStatsState.textContent = tr("studio.finished");
    renderSynthesisStats();
  }
  function autoExtractTitle(text) {
    if (!text) return "";
    const lines = text.split("\n");
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("#")) {
        return trimmed.replace(/^#+\s*/, "").trim().substring(0, 80);
      }
    }
    const clean = text.replace(/[`*#_\-\[\]()]/g, "").trim();
    if (clean) {
      return clean.split(".")[0].trim().substring(0, 50);
    }
    return "";
  }

  // =========================================================================
  // METRICS & PREVIEW LOGIC
  // =========================================================================
  function updateMetrics() {
    const text = markdownInput.value;
    const chars = text.length;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    
    // Szacowany czas mówienia: ~130 słów na minutę
    const estSec = Math.round((words / 130) * 60);
    
    metricChars.textContent = chars.toLocaleString();
    metricWords.textContent = words.toLocaleString();
    metricEstTime.textContent = formatTime(estSec);

    // Renderowanie podglądów
    renderMarkdownPreview();
    renderSpeechPreview();
  }

  function renderMarkdownPreview() {
    const md = markdownInput.value.trim();
    if (!md) {
      markdownPreviewBox.innerHTML = `<p class="preview-placeholder">${tr("studio.previewPlaceholder")}</p>`;
      return;
    }
    if (window.marked && typeof window.marked.parse === "function") {
      markdownPreviewBox.innerHTML = window.marked.parse(md);
    } else {
      markdownPreviewBox.innerHTML = `<pre>${escapeHtml(md)}</pre>`;
    }
  }
  function renderSpeechPreview() {
    const md = markdownInput.value.trim();
    if (!md) {
      speechPreviewBox.innerHTML = `<p class="preview-placeholder">${tr("studio.speechPlaceholder")}</p>`;
      return;
    }

    // Prosta symulacja segmentacji po stronie przeglądarki
    const lines = md.split(/\n\n+/);
    let html = "";
    let idx = 1;

    for (const block of lines) {
      const trimmed = block.trim();
      if (!trimmed) continue;

      if (trimmed.startsWith("```")) {
        html += `
          <div class="segment-card">
            <span class="seg-idx">#${idx++}</span>
            <span class="seg-lang">KOD IT</span>
            <div class="seg-text"><em>[Czytanie kodu blokowego z opisem struktury i słów kluczowych]</em></div>
            <span class="seg-pause">Pauza: 650ms</span>
          </div>`;
      } else {
        const isHeader = trimmed.startsWith("#");
        const clean = trimmed.replace(/^#+\s*/, "").replace(/[`*_\[\]]/g, "");
        const lang = /^[a-zA-Z0-9\s\-\.,:;?!'"()]+$/.test(clean) && !/[ąćęłńóśźż]/i.test(clean) ? "EN" : "PL";
        const pause = isHeader ? "800ms" : "350ms";

        html += `
          <div class="segment-card">
            <span class="seg-idx">#${idx++}</span>
            <span class="seg-lang">${lang}</span>
            <div class="seg-text">${isHeader ? '<strong>' + clean + '</strong>' : clean}</div>
            <span class="seg-pause">Pauza: ${pause}</span>
          </div>`;
      }
    }
      speechPreviewBox.innerHTML = `<p class="preview-placeholder">${tr("studio.speechPlaceholder")}</p>`;
  }

  // Markdown Editor Tabs
  function switchTab(tabName) {
    [tabEditor, tabPreview, tabSpeech].forEach(b => b.classList.remove("active"));
    [paneEditor, panePreview, paneSpeech].forEach(p => p.classList.remove("active"));

    if (tabName === "editor") {
      tabEditor.classList.add("active");
      paneEditor.classList.add("active");
      markdownInput.focus();
    } else if (tabName === "preview") {
      tabPreview.classList.add("active");
      panePreview.classList.add("active");
      renderMarkdownPreview();
    } else if (tabName === "speech") {
      tabSpeech.classList.add("active");
      paneSpeech.classList.add("active");
      renderSpeechPreview();
    }
  }

  tabEditor.addEventListener("click", () => switchTab("editor"));
  tabPreview.addEventListener("click", () => switchTab("preview"));
  tabSpeech.addEventListener("click", () => switchTab("speech"));

  // Toolbar Actions
  document.querySelectorAll(".tool-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const action = btn.dataset.action;
      insertMarkdownSyntax(action);
    });
  });

  function insertMarkdownSyntax(action) {
    const start = markdownInput.selectionStart;
    const end = markdownInput.selectionEnd;
    const text = markdownInput.value;
    const selected = text.substring(start, end);
    let replacement = "";
    let cursorOffset = 0;

    switch (action) {
      case "h1":
        replacement = `# ${selected || "Nagłówek 1"}\n`;
        cursorOffset = replacement.length;
        break;
      case "h2":
        replacement = `## ${selected || "Nagłówek 2"}\n`;
        cursorOffset = replacement.length;
        break;
      case "bold":
        replacement = `**${selected || "pogrubiony tekst"}**`;
        cursorOffset = replacement.length;
        break;
      case "italic":
        replacement = `*${selected || "kursywa"}*`;
        cursorOffset = replacement.length;
        break;
      case "inline-code":
        replacement = `\`${selected || "kod"}\``;
        cursorOffset = replacement.length;
        break;
      case "code-block":
        replacement = `\n\`\`\`go\n${selected || "// kod źródłowy w Go\nfunc main() {\n\n}"}\n\`\`\`\n`;
        cursorOffset = replacement.length;
        break;
      case "list":
        replacement = `\n- ${selected || "Punkt listy"}\n- Drugi punkt\n`;
        cursorOffset = replacement.length;
        break;
      case "quote":
        replacement = `\n> ${selected || "Ważny cytat lub uwaga architektoniczna"}\n`;
        cursorOffset = replacement.length;
        break;
    }

    markdownInput.value = text.substring(0, start) + replacement + text.substring(end);
    markdownInput.focus();
    markdownInput.setSelectionRange(start + cursorOffset, start + cursorOffset);
    updateMetrics();
  }

  // Auto-Title
  btnAutoTitle.addEventListener("click", () => {
    const title = autoExtractTitle(markdownInput.value);
    if (title) {
      titleInput.value = title;
      showToast(tr("studio.titleGenerated", { title }), "success");
    } else {
      showToast(tr("studio.enterHeading"), "info");
    }
  });

  // Presets
  presetSelector.addEventListener("change", (e) => {
    const key = e.target.value;
    if (!key) return;
    const preset = PRESETS[key];
    if (preset) {
      if (markdownInput.value.trim() && !confirm("Czy chcesz zastąpić aktualną treść wybranym szablonem?")) {
        presetSelector.value = "";
        return;
      }
      titleInput.value = preset.title;
      markdownInput.value = preset.markdown;
      updateMetrics();
      showToast(tr("studio.presetLoaded", { title: preset.title || tr("studio.blankTemplate") }), "info");
    }
  });

  btnClearText.addEventListener("click", () => {
    if (confirm("Czy na pewno wyczyścić pole edytora?")) {
      markdownInput.value = "";
      titleInput.value = "";
      updateMetrics();
    }
  });

  markdownInput.addEventListener("input", updateMetrics);

  // Wybór języka głównego i dodatkowego
  const primaryLanguage = document.getElementById("primaryLanguage");
  const secondaryLanguage = document.getElementById("secondaryLanguage");
  const primaryLanguageCustom = document.getElementById("primaryLanguageCustom");
  const secondaryLanguageCustom = document.getElementById("secondaryLanguageCustom");
  const languageHint = document.getElementById("languageSelectionHint");
  const languageBadge = document.getElementById("langBadgeDesc");

  const readLanguage = (select, customInput, fallback) => {
    if (!select || select.value === "__custom__") {
      if (customInput) customInput.hidden = false;
      return customInput?.value.trim() || fallback;
    }
    if (customInput) {
      customInput.hidden = true;
      customInput.value = "";
    }
    return select.value || fallback;
  };

  const selectedLanguageLabel = (select, customInput, fallback) => {
    if (!select || select.value === "__custom__") {
      return customInput?.value.trim() || fallback;
    }
    return select.selectedOptions[0]?.textContent?.trim() || fallback;
  };

  const updateLanguageSelection = () => {
    state.primaryLanguage = readLanguage(primaryLanguage, primaryLanguageCustom, "pl");
    state.secondaryLanguage = secondaryLanguage?.value === "none"
      ? null
      : readLanguage(secondaryLanguage, secondaryLanguageCustom, "en");
    if (secondaryLanguage?.value === "none" && secondaryLanguageCustom) {
      secondaryLanguageCustom.hidden = true;
      secondaryLanguageCustom.value = "";
    }

    const primaryName = selectedLanguageLabel(primaryLanguage, primaryLanguageCustom, state.primaryLanguage);
    const secondaryName = secondaryLanguage?.value === "none"
      ? "bez j\u0119zyka dodatkowego"
      : selectedLanguageLabel(secondaryLanguage, secondaryLanguageCustom, state.secondaryLanguage || "en");

    if (languageBadge) languageBadge.textContent = primaryName + " + " + secondaryName;
    if (languageHint) languageHint.textContent = state.secondaryLanguage
      ? "Tekst g\u0142\u00F3wny b\u0119dzie czytany po " + primaryName.toLowerCase()
        + ", a rozpoznane fragmenty po " + secondaryName.toLowerCase() + "."
      : "Ca\u0142y tekst b\u0119dzie czytany po " + primaryName.toLowerCase() + ".";
  };

  primaryLanguage?.addEventListener("change", updateLanguageSelection);
  secondaryLanguage?.addEventListener("change", updateLanguageSelection);
  primaryLanguageCustom?.addEventListener("input", updateLanguageSelection);
  secondaryLanguageCustom?.addEventListener("input", updateLanguageSelection);

  const loadLanguageOptions = async () => {
    try {
      const response = await fetch("/api/languages");
      const data = await response.json();
      const items = Array.isArray(data.items) ? data.items : [];
      if (items.length && primaryLanguage && secondaryLanguage) {
        const currentPrimary = state.primaryLanguage;
        const currentSecondary = state.secondaryLanguage || "none";
        const options = items.map(item => (
          '<option value="' + item.code + '">' + item.name + '</option>'
        )).join("");
        primaryLanguage.innerHTML = options;
        secondaryLanguage.innerHTML = '<option value="none">Bez j\u0119zyka dodatkowego</option>' + options;
        primaryLanguage.value = items.some(item => item.code === currentPrimary) ? currentPrimary : "pl";
        secondaryLanguage.value = currentSecondary === "none" || items.some(item => item.code === currentSecondary)
          ? currentSecondary
          : "en";
      }
    } catch (error) {
      console.warn("Nie uda\u0142o si\u0119 pobra\u0107 rejestru j\u0119zyk\u00F3w", error);
    }
    updateLanguageSelection();
  };

  updateLanguageSelection();
  loadLanguageOptions();

  // Base Speed Selector
  document.querySelectorAll(".speed-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      document.querySelectorAll(".speed-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      state.baseSpeed = parseFloat(pill.dataset.speed);
      setAudioSpeed(state.baseSpeed);
    });
  });

  // Advanced Sliders
  paramTemp.addEventListener("input", (e) => valTemp.textContent = parseFloat(e.target.value).toFixed(2));
  paramCfg.addEventListener("input", (e) => valCfg.textContent = parseFloat(e.target.value).toFixed(2));
  paramExag.addEventListener("input", (e) => valExag.textContent = parseFloat(e.target.value).toFixed(2));

  // =========================================================================
  // AUDIO PLAYER CONTROLLER
  // =========================================================================
  function loadTrack(item, autoPlay = true) {
    state.activeItem = item;

    playerTitle.textContent = item.title || "Nagranie bez tytułu";
    metaLang.textContent = item.lang === "bilingual" ? "🌐 PL+EN" : (item.lang === "pl" ? "🇵🇱 PL" : "🇬🇧 EN");
    metaDuration.textContent = `⏱️ ${formatTime(item.duration_sec || 0)}`;
    metaSize.textContent = `💾 ${item.file_size_kb || 0} KB`;
    metaDate.textContent = `📅 ${item.created_at || tr("studio.today")}`;

    audioElement.src = item.audio_url;
    audioElement.playbackRate = state.currentSpeed;
    btnDownload.href = item.audio_url;
    btnDownload.download = item.filename || `${item.id}.wav`;

    highlightActiveHistoryItem(item.id);

    if (autoPlay) {
      playAudio();
    } else {
      pauseAudio();
    }
  }

  function playAudio() {
    if (!audioElement.src) return;
    audioElement.play().then(() => {
      state.isPlaying = true;
      playIcon.textContent = "⏸️";
      btnPlayPause.title = "Wstrzymaj (Spacja)";
      playerCard.classList.add("playing");
    }).catch(err => {
      console.warn("Autoplay zablokowany lub błąd odtwarzacza:", err);
    });
  }

  function pauseAudio() {
    audioElement.pause();
    state.isPlaying = false;
    playIcon.textContent = "▶️";
    btnPlayPause.title = "Odtwórz (Spacja)";
    playerCard.classList.remove("playing");
  }

  function togglePlayPause() {
    if (state.isPlaying) {
      pauseAudio();
    } else {
      playAudio();
    }
  }

  btnPlayPause.addEventListener("click", togglePlayPause);

  btnSkipBack.addEventListener("click", () => {
    audioElement.currentTime = Math.max(0, audioElement.currentTime - 5);
  });

  btnSkipForward.addEventListener("click", () => {
    audioElement.currentTime = Math.min(audioElement.duration || 0, audioElement.currentTime + 5);
  });

  btnLoop.addEventListener("click", () => {
    state.isLooping = !state.isLooping;
    audioElement.loop = state.isLooping;
    btnLoop.classList.toggle("active", state.isLooping);
    showToast(state.isLooping ? tr("studio.loopOn") : tr("studio.loopOff"), "info");
  });

  // Audio Events
  audioElement.addEventListener("timeupdate", () => {
    const cur = audioElement.currentTime;
    const dur = audioElement.duration || 1;
    playerCurTime.textContent = formatTime(cur);
    if (!isNaN(dur) && dur > 0) {
      playerTotalTime.textContent = formatTime(dur);
      const pct = (cur / dur) * 100;
      timelineFill.style.width = `${pct}%`;
      timelineSlider.value = pct;
    }
  });

  audioElement.addEventListener("ended", () => {
    if (!state.isLooping) {
      pauseAudio();
      timelineFill.style.width = "0%";
      timelineSlider.value = 0;
      audioElement.currentTime = 0;
    }
  });

  // Timeline Scrubbing
  timelineSlider.addEventListener("input", (e) => {
    const pct = parseFloat(e.target.value);
    timelineFill.style.width = `${pct}%`;
    if (audioElement.duration) {
      audioElement.currentTime = (pct / 100) * audioElement.duration;
    }
  });

  // Speed controls
  function setAudioSpeed(speed) {
    state.currentSpeed = speed;
    audioElement.playbackRate = speed;
    document.querySelectorAll(".p-speed-btn").forEach(btn => {
      btn.classList.toggle("active", parseFloat(btn.dataset.speed) === speed);
    });
  }

  document.querySelectorAll(".p-speed-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const spd = parseFloat(btn.dataset.speed);
      setAudioSpeed(spd);
    });
  });

  // Volume
  volSlider.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    audioElement.volume = val;
    state.volume = val;
    btnMute.textContent = val === 0 ? "🔇" : (val < 0.5 ? "🔉" : "🔊");
  });

  btnMute.addEventListener("click", () => {
    state.isMuted = !state.isMuted;
    audioElement.muted = state.isMuted;
    btnMute.textContent = state.isMuted ? "🔇" : "🔊";
  });

  // Regenerate current
  btnRegenCurrent.addEventListener("click", () => {
    if (!state.activeItem) {
      showToast(tr("messages.noRecordingRegenerate"), "info");
      return;
    }
    synthesizeSpeech(state.activeItem.id, true);
  });

  // =========================================================================
  // SYNTHESIS API (GENERUJ MOWĘ AI)
  // =========================================================================
  async function synthesizeSpeech(overrideId = null, force = false) {
    const md = markdownInput.value.trim();
    if (!md) {
      showToast(tr("messages.emptyMarkdown"), "error");
      markdownInput.focus();
      return;
    }

    let title = titleInput.value.trim();
    if (!title) {
      title = autoExtractTitle(md) || "Nagranie Studio TTS";
      titleInput.value = title;
    }

    const payload = {
      id: overrideId || null,
      title: title,
      markdown: md,
      lang: state.secondaryLanguage ? "bilingual" : state.primaryLanguage,
      primary_language: state.primaryLanguage,
      secondary_language: state.secondaryLanguage,
      speed: state.baseSpeed,
      force: force,
      temperature: parseFloat(paramTemp.value),
      cfg_weight: parseFloat(paramCfg.value),
      exaggeration: parseFloat(paramExag.value)
    };

    setSynthesizingState(true, "Przygotowywanie i normalizacja tekstu Markdown...");

    try {
      // Symulacja etapów w interfejsie
      setTimeout(() => {
        if (state.isSynthesizing) setSynthesizingState(true, "Synteza segmentów mowy przez uniwersalny model OmniVoice AI...");
      }, 1200);

      const response = await fetch("/api/studio/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Błąd serwera (${response.status})`);
      }

      const res = await response.json();
      const item = res.item;

      if (Number.isFinite(Number(item.synth_time_sec))) {
        state.lastSynthesisSeconds = Number(item.synth_time_sec);
      }

      showToast(tr("studio.generatedSuccess", { duration: item.duration_sec }), "success");
      setSynthesizingState(false, "Generowanie zakończone sukcesem!");

      // Załaduj do odtwarzacza
      loadTrack(item, true);

      // Odśwież historię nagrań
      await fetchHistory();

    } catch (err) {
      console.error("[Synthesis Error]", err);
      showToast(tr("messages.synthesisError", { error: err.message }), "error");
      setSynthesizingState(false, "Wystąpił błąd podczas syntezy.");
      statusDot.className = "status-indicator error";
    }
  }

  function setSynthesizingState(isWorking, message) {
    const wasWorking = state.isSynthesizing;
    state.isSynthesizing = isWorking;
    btnSynthesize.disabled = isWorking;

    if (isWorking) {
      if (!wasWorking) startSynthesisStats();
      btnSynthIcon.textContent = "⏳";
      btnSynthText.textContent = tr("studio.working");
      statusDot.className = "status-indicator working";
      statusMsg.textContent = message;
    } else {
      if (wasWorking) stopSynthesisStats();
      btnSynthIcon.textContent = "⚡";
      btnSynthText.textContent = tr("studio.generate");
      statusDot.className = "status-indicator ready";
      statusMsg.textContent = message;
    }
  }

  btnSynthesize.addEventListener("click", () => synthesizeSpeech(null, true));

  // =========================================================================
  // HISTORY / LIBRARY ON DISK
  // =========================================================================
  async function fetchHistory() {
    try {
      const response = await fetch("/api/studio/history");
      if (!response.ok) throw new Error("Błąd pobierania historii");
      const data = await response.json();
      state.historyItems = data.items || [];
      applyStudioStats({ stats: data.stats || {} });
      renderHistoryList();
    } catch (err) {
      console.error("[History Fetch Error]", err);
      showToast(tr("messages.historyError"), "error");
    }
  }

  function renderHistoryList() {
    const filter = historySearchInput.value.toLowerCase().trim();
    const filtered = state.historyItems.filter(item => {
      const matchTitle = (item.title || "").toLowerCase().includes(filter);
      const matchText = (item.markdown || "").toLowerCase().includes(filter);
      return matchTitle || matchText;
    });

    historyCount.textContent = state.historyItems.length;
    statDiskCount.textContent = `${state.historyItems.length} ${tr("studio.savedCount")}`;

    if (filtered.length === 0) {
      const isEmpty = state.historyItems.length === 0;
      historyList.innerHTML = `
        <div class="history-empty">
          <span class="empty-icon">${isEmpty ? "📁" : "🔍"}</span>
          <p>${isEmpty ? tr("studio.historyEmpty") : tr("studio.noResults")}</p>
          <small>${isEmpty ? tr("studio.historyEmptyHint") : tr("studio.noResultsHint")}</small>
        </div>`;
      return;
    }

    let html = "";
    for (const item of filtered) {
      const isCurrent = state.activeItem && state.activeItem.id === item.id;
      const langBadge = item.lang === "bilingual" ? "🌐 PL+EN" : (item.lang === "pl" ? "🇵🇱 PL" : "🇬🇧 EN");
      const snippet = (item.markdown || "").substring(0, 140).replace(/\n/g, " ");
      const playLabel = isCurrent && state.isPlaying ? tr("studio.pause") : tr("studio.play");

      html += `
        <div class="history-item ${isCurrent ? "playing" : ""}" id="histItem_${item.id}" data-id="${item.id}">
          <div class="history-item-top">
            <div class="item-title-box">
              <h4 class="item-title">${escapeHtml(item.title || tr("studio.recording"))}</h4>
              <div class="item-meta-row">
                <span class="meta-tag">${langBadge}</span>
                <span class="meta-tag">⏱️ ${formatTime(item.duration_sec || 0)}</span>
                <span class="meta-tag">💾 ${item.file_size_kb || 0} KB</span>
                <span class="item-date">${item.created_at || ""}</span>
              </div>
            </div>
          </div>
          <div class="item-snippet" title="${escapeHtml(item.markdown || "")}">${escapeHtml(snippet)}</div>
          <div class="history-item-actions">
            <button type="button" class="btn-item-play" onclick="window.StudioApp.playItem('${item.id}')" title="${tr("studio.playTitle")}">
              <span>${playLabel}</span>
            </button>
            <div class="item-btn-group">
              <button type="button" class="btn-item-sub" onclick="window.StudioApp.loadIntoEditor('${item.id}')" title="${tr("studio.loadTitle")}">
                <span>${tr("studio.edit")}</span>
              </button>
              <button type="button" class="btn-item-sub" onclick="window.StudioApp.regenerateItem('${item.id}')" title="${tr("studio.regenerateTitle")}">
                <span>${tr("studio.regenerate")}</span>
              </button>
              <button type="button" class="btn-item-sub btn-item-delete" onclick="window.StudioApp.promptDelete('${item.id}')" title="${tr("studio.deleteItemTitle")}">
                <span>${tr("studio.delete")}</span>
              </button>
            </div>
          </div>
        </div>`;
    }
    historyList.innerHTML = html;
  }
  function highlightActiveHistoryItem(itemId) {
    document.querySelectorAll(".history-item").forEach(card => {
      card.classList.toggle("playing", card.dataset.id === itemId);
    });
  }

  historySearchInput.addEventListener("input", renderHistoryList);
  btnRefreshHistory.addEventListener("click", () => {
    fetchHistory();
    showToast(tr("messages.historyRefreshed"), "info");
  });

  // =========================================================================
  // GLOBAL WINDOW APP METHODS (FOR ONCLICK ACTIONS)
  // =========================================================================
  window.StudioApp = {
    playItem(id) {
      const it = state.historyItems.find(x => x.id === id);
      if (!it) return;
      if (state.activeItem && state.activeItem.id === id) {
        togglePlayPause();
      } else {
        loadTrack(it, true);
      }
      renderHistoryList();
    },

    loadIntoEditor(id) {
      const it = state.historyItems.find(x => x.id === id);
      if (!it) return;
      if (markdownInput.value.trim() && !confirm("Czy chcesz załadować to nagranie i zastąpić obecną treść w edytorze?")) {
        return;
      }
      titleInput.value = it.title || "";
      markdownInput.value = it.markdown || "";
      if (it.lang) {
        const [primary, secondary] = String(it.lang).split("+");
        if (primaryLanguage) primaryLanguage.value = primary || "pl";
        if (secondaryLanguage) secondaryLanguage.value = secondary || "none";
        updateLanguageSelection();
      }
      switchTab("editor");
      updateMetrics();
      showToast(tr("studio.loadSuccess", { title: it.title }), "info");
      window.scrollTo({ top: 0, behavior: "smooth" });
    },

    regenerateItem(id) {
      const it = state.historyItems.find(x => x.id === id);
      if (!it) return;
      titleInput.value = it.title || "";
      markdownInput.value = it.markdown || "";
      updateMetrics();
      synthesizeSpeech(it.id, true);
    },

    promptDelete(id) {
      const it = state.historyItems.find(x => x.id === id);
      if (!it) return;
      state.pendingDeleteId = id;
      deleteModalText.innerHTML = tr("studio.confirmDelete", { title: escapeHtml(it.title), filename: it.filename });
      deleteModalBackdrop.classList.add("open");
    }
  };

  btnCancelDelete.addEventListener("click", () => {
    deleteModalBackdrop.classList.remove("open");
    state.pendingDeleteId = null;
  });

  btnConfirmDelete.addEventListener("click", async () => {
    const id = state.pendingDeleteId;
    if (!id) return;
    deleteModalBackdrop.classList.remove("open");

    try {
      const resp = await fetch(`/api/studio/item/${id}`, { method: "DELETE" });
      if (!resp.ok) throw new Error("Błąd usuwania pliku z dysku");

      showToast(tr("studio.deletedSuccess"), "success");

      // Jeśli usunięto aktualnie odtwarzany utwór
      if (state.activeItem && state.activeItem.id === id) {
        pauseAudio();
        state.activeItem = null;
        playerTitle.textContent = tr("studio.noRecording");
        audioElement.src = "";
      }

      await fetchHistory();
    } catch (err) {
      console.error("[Delete Error]", err);
      showToast(tr("messages.deleteError", { error: err.message }), "error");
    } finally {
      state.pendingDeleteId = null;
    }
  });

  function escapeHtml(text) {
    if (!text) return "";
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // =========================================================================
  // KEYBOARD SHORTCUTS
  // =========================================================================
  document.addEventListener("keydown", (e) => {
    const tag = (e.target.tagName || "").toUpperCase();
    const isEditing = tag === "INPUT" || tag === "TEXTAREA" || e.target.isContentEditable;

    // Ctrl + Enter: Synteza
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      synthesizeSpeech(null, true);
      return;
    }

    // Space: Play/Pause (jeśli nie piszemy w edytorze)
    if (e.code === "Space" && !isEditing) {
      e.preventDefault();
      togglePlayPause();
      return;
    }

    // Strzałki lewo/prawo: Skip 5s
    if (e.code === "ArrowLeft" && !isEditing) {
      e.preventDefault();
      btnSkipBack.click();
      return;
    }
    if (e.code === "ArrowRight" && !isEditing) {
      e.preventDefault();
      btnSkipForward.click();
      return;
    }
  });

  // =========================================================================
  // INITIALIZATION
  // =========================================================================
  // Załaduj domyślny przykładowy szablon na start, jeśli edytor jest pusty
  if (!markdownInput.value.trim()) {
    const initialPreset = PRESETS.cloud_native;
    titleInput.value = initialPreset.title;
    markdownInput.value = initialPreset.markdown;
  }

  updateMetrics();
  fetchHistory();
});
