/**
 * Lektor Pro - Converter & PDF OCR Modal Module
 * Zarządza importem PDF, renderowaniem skanów 300 DPI, procesem konwersji i telemetrią na żywo (SSE).
 * Obsługuje wybór dowolnego języka docelowego Markdown (140+ języków).
 */
import * as api from '../api.js?v=20261009-i18n';
import { t } from '../i18n.js?v=20261009-i18n';
import * as ui from '../ui.js?v=20261009-i18n';
import { initBookSelector } from './book_selector.js?v=20261009-i18n';

export function formatDurationSec(totalSec) {
    if (!totalSec || isNaN(totalSec) || totalSec <= 0) return "--:--";
    const s = Math.round(totalSec);
    const m = Math.floor(s / 60);
    const sec = s % 60;
    if (m >= 60) {
        const h = Math.floor(m / 60);
        const min = m % 60;
        return `${h}h ${min}m`;
    }
    return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
}

export function initConverterModal({ onReloadBooks, onConversionFinished }) {
    const btnOpen = document.getElementById("btnOpenConverterModal");
    const modalBackdrop = document.getElementById("converterModalBackdrop");
    const btnClose = document.getElementById("btnConvClose");
    const btnStart = document.getElementById("btnStartConversion");
    const btnStop = document.getElementById("btnConvStop");
    const btnFinish = document.getElementById("btnConvFinish");

    const telemetryPanel = document.getElementById("convTelemetryPanel");
    const convBookTitle = document.getElementById("convBookTitle");
    const convStatusPill = document.getElementById("convStatusPill");
    const convPdfPath = document.getElementById("convPdfPath");
    const convTotalPdfPages = document.getElementById("convTotalPdfPages");
    const convScansCount = document.getElementById("convScansCount");
    const convPagesCount = document.getElementById("convPagesCount");

    const convStartPage = document.getElementById("convStartPage");
    const convEndPage = document.getElementById("convEndPage");
    const convDpi = document.getElementById("convDpi");
    const convModelName = document.getElementById("convModelName");
    const convSkipExisting = document.getElementById("convSkipExisting");

    // Pola wielojęzyczności
    const convTargetLang = document.getElementById("convTargetLang");
    const convCustomTargetLang = document.getElementById("convCustomTargetLang");
    const convSourceLang = document.getElementById("convSourceLang");

    const convStateBadge = document.getElementById("convStateBadge");
    const convStateText = document.getElementById("convStateText");
    const convStepDesc = document.getElementById("convStepDesc");
    const convProgressPct = document.getElementById("convProgressPct");
    const convProgressFill = document.getElementById("convProgressFill");

    const convMetricSpeed = document.getElementById("convMetricSpeed");
    const convMetricSecPage = document.getElementById("convMetricSecPage");
    const convMetricEta = document.getElementById("convMetricEta");
    const convMetricElapsed = document.getElementById("convMetricElapsed");
    const convMetricVram = document.getElementById("convMetricVram");
    const convMetricGpu = document.getElementById("convMetricGpu");
    const convTerminal = document.getElementById("convTerminal");

    const btnSelectPdfFile = document.getElementById("btnSelectPdfFile");
    const convPdfFileInput = document.getElementById("convPdfFileInput");
    const convSelectedFileName = document.getElementById("convSelectedFileName");
    const convNewBookTitle = document.getElementById("convNewBookTitle");
    const btnUploadPdfToCurrent = document.getElementById("btnUploadPdfToCurrent");
    const btnUploadPdf = document.getElementById("btnUploadPdf");
    const btnChangePdfForCurrent = document.getElementById("btnChangePdfForCurrent");
    const convUploadStatus = document.getElementById("convUploadStatus");
    const btnRenderScans = document.getElementById("btnRenderScans");

    let currentBookInfo = null;
    let activeConversionTaskId = null;
    let activeConversionEventSource = null;
    let scanEventSource = null;
    let lastPageDurationSec = 0;
    let lastTokensPerSec = 0;
    let bookInfoRefreshTimer = null;
    let bookInfoRefreshInFlight = false;
    function polishConversionState(state) {
        return {
            TRANSLATING: t("converter.processing"),
            CANCELLING: t("converter.stopping"),
            CANCELLED: t("converter.stopped"),
            COMPLETED: t("common.success"),
            FAILED: t("common.error"),
            PAUSED: t("converter.paused"),
        }[state] || state;
    }
    // Obsługa przełączania na własny język
    if (convTargetLang && convCustomTargetLang) {
        convTargetLang.onchange = () => {
            convCustomTargetLang.style.display = (convTargetLang.value === "custom") ? "block" : "none";
            if (convTargetLang.value === "custom") {
                convCustomTargetLang.focus();
            }
        };
    }

    function appendLogLine(text, type = "info") {
        if (!convTerminal) return;
        const timeStr = new Date().toLocaleTimeString();
        const line = document.createElement("div");
        line.className = "conv-terminal-line";
        const typeClass = type === "ok" ? "t-ok" : (type === "err" ? "t-err" : "t-info");
        line.innerHTML = `<span class="t-time">[${timeStr}]</span> <span class="${typeClass}">${text}</span>`;
        convTerminal.appendChild(line);
        convTerminal.scrollTop = convTerminal.scrollHeight;
    }

    function conversionStorageKey(slug) {
        return `lektor_active_conversion_${slug}`;
    }

    function updateBookCounters(bookInfo) {
        if (!bookInfo) return;
        if (convTotalPdfPages) convTotalPdfPages.textContent = bookInfo.total_pages ?? "--";
        if (convScansCount) convScansCount.textContent = bookInfo.scans_count ?? 0;
        if (convPagesCount) convPagesCount.textContent = bookInfo.pages_count ?? 0;
    }

    async function refreshBookCounters(slug) {
        if (!slug || bookInfoRefreshInFlight) return;
        bookInfoRefreshInFlight = true;
        try {
            const refreshedInfo = await api.fetchConverterBookInfo(slug);
            if (currentBookInfo?.book_slug === slug) {
                currentBookInfo = refreshedInfo;
            }
            updateBookCounters(refreshedInfo);
        } catch (error) {
            console.warn("Nie udało się odświeżyć licznika stron Markdown.", error);
        } finally {
            bookInfoRefreshInFlight = false;
        }
    }

    function stopBookInfoRefresh() {
        if (bookInfoRefreshTimer !== null) {
            window.clearInterval(bookInfoRefreshTimer);
            bookInfoRefreshTimer = null;
        }
    }

    function startBookInfoRefresh(slug) {
        stopBookInfoRefresh();
        if (!slug) return;
        void refreshBookCounters(slug);
        bookInfoRefreshTimer = window.setInterval(() => {
            void refreshBookCounters(slug);
        }, 1000);
    }

    function finishBookInfoRefresh(slug) {
        stopBookInfoRefresh();
        void refreshBookCounters(slug);
    }
    function resumeConversion(taskId) {
        activeConversionTaskId = taskId;
        startBookInfoRefresh(currentBookInfo?.book_slug);
        if (telemetryPanel) telemetryPanel.style.display = "flex";
        if (btnStop) btnStop.style.display = "inline-flex";
        if (activeConversionEventSource) activeConversionEventSource.close();
        activeConversionEventSource = api.subscribeConversionProgress(taskId, (event) => {
            if (convStateText) convStateText.textContent = polishConversionState(event.state);
            if (convStepDesc) convStepDesc.textContent = event.current_step_description || t("converter.inProgress");
            const pct = (event.progress_pct || 0).toFixed(1);
            if (convProgressPct) convProgressPct.textContent = `${pct}%`;
            if (convProgressFill) convProgressFill.style.width = `${pct}%`;
            if (Number(event.tokens_per_sec || 0) > 0) lastTokensPerSec = Number(event.tokens_per_sec);
            if (Number(event.page_duration_sec || 0) > 0) lastPageDurationSec = Number(event.page_duration_sec);
            if (convMetricSpeed) convMetricSpeed.textContent = `${lastTokensPerSec.toFixed(1)} token\u00f3w/s`;
            if (convMetricSecPage) convMetricSecPage.textContent = lastPageDurationSec > 0 ? `${lastPageDurationSec.toFixed(1)} s / stron\u0119` : "-- s / stron\u0119";
            if (convMetricEta) convMetricEta.textContent = formatDurationSec(event.eta_sec);
            if (convMetricElapsed) convMetricElapsed.textContent = formatDurationSec(event.elapsed_sec);
            const totalVramGb = Number(event.vram_total_mb || 0) / 1024;
            if (convMetricVram) convMetricVram.textContent = totalVramGb > 0 ? `${(Number(event.vram_used_mb || 0) / 1024).toFixed(1)} / ${totalVramGb.toFixed(1)} GB` : "-- / -- GB";
            if (convMetricGpu) convMetricGpu.textContent = `${Number(event.gpu_utilization_pct || 0).toFixed(1)}%`;
            if (["COMPLETED", "CANCELLED", "FAILED"].includes(event.state)) {
                const slug = currentBookInfo?.book_slug;
                if (slug) localStorage.removeItem(conversionStorageKey(slug));
                finishBookInfoRefresh(slug);
                activeConversionTaskId = null;
                if (btnStop) btnStop.style.display = "none";
            }
        }, (err) => console.warn("[SSE] Wznowienie konwersji:", err));
    }

    async function openModal() {
        const bookSelect = document.getElementById("bookSelectDropdown");
        const currentSlug = bookSelect?.value;
        if (!currentSlug) {
            alert("Proszę najpierw wybrać aktywną książkę.");
            return;
        }

        if (modalBackdrop) modalBackdrop.style.display = "flex";

        try {
            if (convBookTitle) convBookTitle.textContent = "Wczytywanie informacji o pliku PDF...";
            currentBookInfo = await api.fetchConverterBookInfo(currentSlug);

            if (convBookTitle) convBookTitle.textContent = currentBookInfo.title || currentSlug;
            if (convStatusPill) {
                if (currentBookInfo.pdf_exists && currentBookInfo.pdf_path) {
                    convStatusPill.className = "conv-status-pill ready";
                    convStatusPill.textContent = t("converter.pdfReady");
                    if (convPdfPath) {
                        convPdfPath.textContent = currentBookInfo.pdf_path;
                        convPdfPath.style.color = "#94a3b8";
                    }
                    if (btnStart) btnStart.disabled = false;
                    if (btnRenderScans) btnRenderScans.disabled = false;
                } else {
                    convStatusPill.className = "conv-status-pill missing";
                    convStatusPill.textContent = t("converter.pdfMissing");
                    if (convPdfPath) {
                        convPdfPath.textContent = `Brak pliku PDF dla '${currentBookInfo.title || currentSlug}'. Użyj przycisku '📂 Wybierz plik PDF' i kliknij '📎 Przypisz do bieżącej'.`;
                        convPdfPath.style.color = "#f87171";
                    }
                    if (btnStart) btnStart.disabled = true;
                    if (btnRenderScans) btnRenderScans.disabled = true;
                }
            }

            updateBookCounters(currentBookInfo);
            if (convStartPage) convStartPage.value = 1;
            if (convEndPage) convEndPage.value = currentBookInfo.total_pages || "";

            const savedTaskId = localStorage.getItem(conversionStorageKey(currentBookInfo.book_slug || currentSlug));
            if (savedTaskId) resumeConversion(savedTaskId);

            // Ustaw domyślny język z metadanych książki, jeśli jest dostępny
            if (currentBookInfo.language && convTargetLang) {
                const langCode = currentBookInfo.language.toLowerCase();
                const optExists = Array.from(convTargetLang.options).some(o => o.value === langCode);
                if (optExists) {
                    convTargetLang.value = langCode;
                } else {
                    convTargetLang.value = "custom";
                    if (convCustomTargetLang) {
                        convCustomTargetLang.style.display = "block";
                        convCustomTargetLang.value = currentBookInfo.language;
                    }
                }
            }
        } catch (e) {
            console.error("Błąd pobierania informacji o PDF:", e);
        }
    }

    function closeModal() {
        if (modalBackdrop) modalBackdrop.style.display = "none";
    }

    if (btnOpen) btnOpen.onclick = openModal;
    if (btnClose) btnClose.onclick = closeModal;
    if (btnChangePdfForCurrent && convPdfFileInput) btnChangePdfForCurrent.onclick = () => convPdfFileInput.click();

    if (modalBackdrop) {
        modalBackdrop.onclick = (e) => {
            if (e.target === modalBackdrop && !activeConversionTaskId) closeModal();
        };
    }

    if (btnSelectPdfFile && convPdfFileInput) {
        btnSelectPdfFile.onclick = () => convPdfFileInput.click();
        convPdfFileInput.onchange = () => {
            const file = convPdfFileInput.files?.[0];
            if (file) {
                const mb = (file.size / (1024 * 1024)).toFixed(2);
                if (convSelectedFileName) convSelectedFileName.textContent = `${file.name} (${mb} MB)`;
                if (convNewBookTitle && !convNewBookTitle.value) {
                    convNewBookTitle.value = file.name.replace(/\.pdf$/i, "").replace(/[_-]+/g, " ");
                }
                if (btnUploadPdf) btnUploadPdf.disabled = false;
                if (btnUploadPdfToCurrent) btnUploadPdfToCurrent.disabled = false;
            }
        };
    }

    if (btnUploadPdfToCurrent) {
        btnUploadPdfToCurrent.onclick = async () => {
            const file = convPdfFileInput?.files?.[0];
            const currentSlug = document.getElementById("bookSelectDropdown")?.value;
            if (!file || !currentSlug) return;

            btnUploadPdfToCurrent.disabled = true;
            btnUploadPdfToCurrent.textContent = t("converter.assigning");
            try {
                const title = convNewBookTitle?.value?.trim() || currentBookInfo?.title || null;
                const res = await api.importPdfBook(file, title, null, currentSlug);
                ui.showToast(`✅ Przypisano plik PDF (${res.total_pages} stron) do książki: ${res.title}`);
                await openModal();
            } catch (err) {
                alert("Błąd przypisywania: " + err.message);
            } finally {
                btnUploadPdfToCurrent.disabled = false;
                btnUploadPdfToCurrent.innerHTML = `<span>📎</span> ${t("converter.assignCurrent")}`;
            }
        };
    }

    if (btnUploadPdf) {
        btnUploadPdf.onclick = async () => {
            const file = convPdfFileInput?.files?.[0];
            if (!file) return;

            btnUploadPdf.disabled = true;
            btnUploadPdf.textContent = t("converter.uploading");
            try {
                const title = convNewBookTitle?.value?.trim() || null;
                const res = await api.importPdfBook(file, title);
                ui.showToast(`✅ Zaimportowano nową książkę: ${res.title}`);
                await initBookSelector({ onBookChanged: onReloadBooks });
                const bookSelect = document.getElementById("bookSelectDropdown");
                if (bookSelect) {
                    bookSelect.value = res.book_slug;
                    await api.switchActiveBook(res.book_slug);
                    if (typeof onReloadBooks === "function") await onReloadBooks();
                }
                await openModal();
            } catch (err) {
                alert("Błąd importu: " + err.message);
            } finally {
                btnUploadPdf.disabled = false;
                btnUploadPdf.innerHTML = `<span>➕</span> ${t("converter.createBook")}`;
            }
        };
    }

    if (btnRenderScans) {
        btnRenderScans.onclick = async () => {
            const currentSlug = document.getElementById("bookSelectDropdown")?.value;
            if (!currentBookInfo?.pdf_path || !currentSlug) return;

            const dpi = parseInt(convDpi?.value || "300", 10);
            const startPage = convStartPage?.value ? parseInt(convStartPage.value, 10) : null;
            const endPage = convEndPage?.value ? parseInt(convEndPage.value, 10) : null;

            btnRenderScans.disabled = true;
            btnRenderScans.innerHTML = `<span>⏳</span> ${t("converter.renderingScans")}`;
            if (telemetryPanel) telemetryPanel.style.display = "flex";
            if (btnStop) btnStop.style.display = "inline-flex";
            if (btnFinish) btnFinish.style.display = "none";
            if (convTerminal) convTerminal.innerHTML = "";

            if (scanEventSource) {
                scanEventSource.close();
                scanEventSource = null;
            }

            scanEventSource = api.subscribeScanRenderingProgress(
                currentSlug,
                { dpi, start_page: startPage, end_page: endPage },
                (ev) => {
                    if (ev.status === "rendering") {
                        const pct = (ev.percent || 0).toFixed(1);
                        if (convProgressFill) convProgressFill.style.width = `${pct}%`;
                        if (convProgressPct) convProgressPct.textContent = `${pct}%`;
                        if (convStepDesc) convStepDesc.textContent = `Renderowanie strony ${ev.rendered_count} z ${ev.total_to_render}`;
                        appendLogLine(`Wyrenderowano stronę ${ev.current_page}/${ev.total_to_render} (${dpi} DPI)`, "ok");
                    } else if (ev.status === "completed") {
                        ui.showToast(`✅ Pomyślnie wyrenderowano skany JPG!`);
                        btnRenderScans.disabled = false;
                        btnRenderScans.innerHTML = `<span>🖼️</span> ${t("converter.renderScans")}`;
                        if (btnStop) btnStop.style.display = "none";
                        openModal();
                    }
                },
                () => {
                    btnRenderScans.disabled = false;
                    btnRenderScans.innerHTML = `<span>🖼️</span> ${t("converter.renderScans")}`;
                    if (btnStop) btnStop.style.display = "none";
                }
            );
        };
    }

    if (btnStart) {
        btnStart.onclick = async () => {
            const currentSlug = document.getElementById("bookSelectDropdown")?.value;
            if (!currentBookInfo?.pdf_path || !currentSlug) return;

            // Pobranie wybranego języka docelowego
            let targetLang = convTargetLang?.value || "pl";
            if (targetLang === "custom" && convCustomTargetLang?.value?.trim()) {
                targetLang = convCustomTargetLang.value.trim().toLowerCase();
            }

            const sourceLang = convSourceLang?.value?.trim() ? convSourceLang.value.trim().toLowerCase() : null;

            const payload = {
                pdf_path: currentBookInfo.pdf_path,
                book_slug: currentSlug,
                dpi: parseInt(convDpi?.value || "300", 10),
                target_language: targetLang,
                source_language: sourceLang,
                start_page: convStartPage?.value ? parseInt(convStartPage.value, 10) : null,
                end_page: convEndPage?.value ? parseInt(convEndPage.value, 10) : null,
                skip_existing: convSkipExisting ? convSkipExisting.checked : true,
                model_name: convModelName?.value ? convModelName.value.trim() : null,
            };

            if (telemetryPanel) telemetryPanel.style.display = "flex";
            if (btnStop) btnStop.style.display = "inline-flex";
            if (btnFinish) btnFinish.style.display = "none";
            if (convTerminal) convTerminal.innerHTML = "";

            try {
                const startRes = await api.startConversion(payload);
                localStorage.setItem(conversionStorageKey(currentSlug), startRes.task_id);
                activeConversionTaskId = startRes.task_id;
                startBookInfoRefresh(currentSlug);
                appendLogLine(`Zadanie konwersji uruchomione dla języka [${targetLang}]: ${activeConversionTaskId}`, "info");

                if (activeConversionEventSource) activeConversionEventSource.close();

                activeConversionEventSource = api.subscribeConversionProgress(
                    activeConversionTaskId,
                    (event) => {
                        if (convStateText) convStateText.textContent = polishConversionState(event.state);
                        if (convStepDesc) convStepDesc.textContent = event.current_step_description || t("converter.inProgress");

                        const pct = (event.progress_pct || 0).toFixed(1);
                        if (convProgressPct) convProgressPct.textContent = `${pct}%`;
                        if (convProgressFill) convProgressFill.style.width = `${pct}%`;

                        if (Number(event.tokens_per_sec || 0) > 0) lastTokensPerSec = Number(event.tokens_per_sec);
                        if (Number(event.page_duration_sec || 0) > 0) lastPageDurationSec = Number(event.page_duration_sec);
                        if (convMetricSpeed) convMetricSpeed.textContent = `${lastTokensPerSec.toFixed(1)} token\u00f3w/s`;
                        if (convMetricSecPage) convMetricSecPage.textContent = lastPageDurationSec > 0 ? `${lastPageDurationSec.toFixed(1)} s / stron\u0119` : "-- s / stron\u0119";
                        if (convMetricEta) convMetricEta.textContent = formatDurationSec(event.eta_sec);
                        if (convMetricElapsed) convMetricElapsed.textContent = formatDurationSec(event.elapsed_sec);

                        const usedVramGb = Number(event.vram_used_mb || 0) / 1024;
                        const totalVramGb = Number(event.vram_total_mb || 0) / 1024;
                        if (convMetricVram) {
                            convMetricVram.textContent = totalVramGb > 0
                                ? `${usedVramGb.toFixed(1)} / ${totalVramGb.toFixed(1)} GB`
                                : "-- / -- GB";
                        }
                        if (convMetricGpu) {
                            convMetricGpu.textContent = Number(event.gpu_utilization_pct || 0).toFixed(1) + "%";
                        }

                        if (["COMPLETED", "CANCELLED", "FAILED"].includes(event.state)) {
                            finishBookInfoRefresh(currentSlug);
                        }

                        if (event.state === "COMPLETED") {
                            ui.showToast(`✅ Konwersja książki na język [${targetLang}] ukończona!`);
                            if (btnStop) btnStop.style.display = "none";
                            if (btnFinish) btnFinish.style.display = "inline-flex";
                            if (typeof onConversionFinished === "function") onConversionFinished();
                        } else if (event.state === "CANCELLED") {
                            if (convStateText) convStateText.textContent = t("converter.stopped");
                            if (convStepDesc) convStepDesc.textContent = "Zadanie zatrzymane przez u\u017cytkownika.";
                            if (btnStop) {
                                btnStop.disabled = false;
                                btnStop.textContent = "\u25a0 Zatrzymaj konwersj\u0119";
                                btnStop.style.display = "none";
                            }
                        }
                    },
                    (err) => console.warn("[SSE] Zdarzenie błędu konwersji:", err)
                );
            } catch (e) {
                alert("Błąd rozpoczęcia konwersji: " + e.message);
            }
        };
    }

    if (btnStop) {
        btnStop.onclick = async () => {
            if (scanEventSource) {
                scanEventSource.close();
                scanEventSource = null;
                btnStop.style.display = "none";
                return;
            }
            if (!activeConversionTaskId) return;
            const taskId = activeConversionTaskId;
            if (convStateText) convStateText.textContent = t("converter.stopping");
            if (convStepDesc) convStepDesc.textContent = "Zatrzymywanie konwersji i zwalnianie zasob\u00f3w GPU/VRAM...";
            if (btnStop) {
                btnStop.disabled = true;
                btnStop.innerHTML = `<span>⏳</span> ${t("converter.stopping")}`;
            }
            appendLogLine("Za\u017c\u0105dano zatrzymania konwersji. Oczekiwanie na bezpieczne zako\u0144czenie bie\u017c\u0105cej strony...", "info");
            try {
                await api.cancelConversion(taskId);
            } catch (e) {
                if (convStateText) convStateText.textContent = "PRZETWARZANIE";
                if (convStepDesc) convStepDesc.textContent = "Nie uda\u0142o si\u0119 zatrzyma\u0107 konwersji.";
                if (btnStop) {
                    btnStop.disabled = false;
                    btnStop.textContent = "\u25a0 Zatrzymaj konwersj\u0119";
                }
                alert("B??d zatrzymywania: " + e.message);
            }
        };
    }

    if (btnFinish) {
        btnFinish.onclick = () => {
            closeModal();
            if (typeof onConversionFinished === "function") onConversionFinished();
        };
    }
}