/**
 * Lektor Pro - Kontroler generowania wsadowego.
 * Obsługuje wybór języka wejściowego oraz sterowanie syntezą całej książki.
 */
import * as api from '../api.js?v=20261009-i18n';
import { t } from '../i18n.js?v=20261009-i18n';
import * as ui from '../ui.js?v=20261009-i18n';

const DEFAULT_SYNTHESIS_PARAMS = Object.freeze({
    temperature: 0.33,
    cfg_weight: 0.68,
    exaggeration: 0.25,
    repetition_penalty: 1.8
});
const DEFAULT_INPUT_LANGUAGE = "auto";
const INPUT_LANGUAGE_STORAGE_KEY = "lektor_input_language";
const LANGUAGE_CODE_PATTERN = /^[a-z]{2,3}(?:-[a-z]{2,4})?$/;

function readStoredInputLanguage() {
    try {
        return localStorage.getItem(INPUT_LANGUAGE_STORAGE_KEY) || DEFAULT_INPUT_LANGUAGE;
    } catch (_) {
        return DEFAULT_INPUT_LANGUAGE;
    }
}

function storeInputLanguage(language) {
    try {
        localStorage.setItem(INPUT_LANGUAGE_STORAGE_KEY, language);
    } catch (_) {
        // Brak pamięci lokalnej nie może zatrzymać generowania.
    }
}

function selectedInputLanguage(select, customInput) {
    const selected = select?.value || DEFAULT_INPUT_LANGUAGE;
    if (selected !== "__custom__") return selected;

    const customCode = customInput?.value.trim().toLowerCase() || "";
    return LANGUAGE_CODE_PATTERN.test(customCode) ? customCode : DEFAULT_INPUT_LANGUAGE;
}

function updateCustomLanguageVisibility(select, customInput) {
    if (!customInput) return;
    const isCustom = select?.value === "__custom__";
    customInput.hidden = !isCustom;
    customInput.required = isCustom;
}

async function loadInputLanguageOptions(select, customInput) {
    try {
        const data = await api.fetchLanguageOptions("omnivoice");
        const items = Array.isArray(data.items) ? data.items : [];
        if (!items.length) return;

        const savedLanguage = readStoredInputLanguage();
        select.replaceChildren();

        const automaticOption = document.createElement("option");
        automaticOption.value = DEFAULT_INPUT_LANGUAGE;
        automaticOption.textContent = t("converter.autoLanguage");
        select.appendChild(automaticOption);

        items.forEach(item => {
            const option = document.createElement("option");
            option.value = item.code;
            option.textContent = item.custom
                ? t("converter.customLanguage")
                : `${item.flag || "🌐"} ${item.name_pl || item.code}`;
            select.appendChild(option);
        });

        const available = Array.from(select.options).some(option => option.value === savedLanguage);
        if (available) {
            select.value = savedLanguage;
        } else if (LANGUAGE_CODE_PATTERN.test(savedLanguage)) {
            select.value = "__custom__";
            if (customInput) customInput.value = savedLanguage;
        } else {
            select.value = DEFAULT_INPUT_LANGUAGE;
        }
        updateCustomLanguageVisibility(select, customInput);
    } catch (error) {
        console.warn("Nie udało się pobrać listy języków wejściowych.", error);
    }
}

function initInputLanguageSelector() {
    const select = document.getElementById("batchInputLanguage");
    const customInput = document.getElementById("batchInputLanguageCustom");
    if (!select) return;

    const update = () => {
        updateCustomLanguageVisibility(select, customInput);
        const language = selectedInputLanguage(select, customInput);
        storeInputLanguage(language);
    };

    select.addEventListener("change", update);
    customInput?.addEventListener("input", update);
    const savedLanguage = readStoredInputLanguage();
    if (Array.from(select.options).some(option => option.value === savedLanguage)) {
        select.value = savedLanguage;
    } else if (LANGUAGE_CODE_PATTERN.test(savedLanguage) && customInput) {
        select.value = "__custom__";
        customInput.value = savedLanguage;
    }
    update();
    void loadInputLanguageOptions(select, customInput);
}

function buildSynthesisPayload(languageMode, inputLanguage) {
    return {
        ...DEFAULT_SYNTHESIS_PARAMS,
        language_mode: languageMode || "bilingual",
        input_language: inputLanguage || DEFAULT_INPUT_LANGUAGE
    };
}

export function initBatchController({ getCurrentLanguageMode = () => "bilingual", onFetchStatus }) {
    const startBtn = document.getElementById("btnStartBatch");
    const stopBtn = document.getElementById("btnStopBatch");
    const headerStartBtn = document.getElementById("btnHeaderBatchStart");
    const headerStopBtn = document.getElementById("btnHeaderBatchStop");
    const inputLanguageSelect = document.getElementById("batchInputLanguage");
    const customLanguageInput = document.getElementById("batchInputLanguageCustom");

    const executeStart = async () => {
        const payload = buildSynthesisPayload(
            getCurrentLanguageMode(),
            selectedInputLanguage(inputLanguageSelect, customLanguageInput)
        );

        try {
            if (startBtn) startBtn.style.display = "none";
            if (stopBtn) {
                stopBtn.style.display = "inline-flex";
                stopBtn.disabled = false;
                stopBtn.innerHTML = `<span>⏹</span> ${t("converter.stopSynthesis")}`;
            }
            await api.startBatch(payload);
            ui.showToast(t("messages.batchStarted"));
            if (typeof onFetchStatus === "function") onFetchStatus();
        } catch (e) {
            if (startBtn) startBtn.style.display = "inline-flex";
            if (stopBtn) stopBtn.style.display = "none";
            ui.showToast(t("messages.startError", { error: e.message }), "error");
        }
    };

    const executeStop = async () => {
        try {
            if (stopBtn) {
                stopBtn.disabled = true;
                stopBtn.innerHTML = `<span>⏳</span> ${t("converter.stoppingSynthesis")}`;
            }
            await api.stopBatch();
            ui.showToast(t("messages.stopRequested"));
            if (typeof onFetchStatus === "function") onFetchStatus();
        } catch (e) {
            ui.showToast(t("messages.stopError", { error: e.message }), "error");
        }
    };

    if (startBtn) startBtn.onclick = executeStart;
    if (stopBtn) stopBtn.onclick = executeStop;
    if (headerStartBtn) {
        headerStartBtn.onclick = () => {
            const modal = document.getElementById("audioGenModalBackdrop");
            if (modal) {
                modal.style.display = "flex";
                if (typeof onFetchStatus === "function") onFetchStatus();
            }
        };
    }
    if (headerStopBtn) headerStopBtn.onclick = executeStop;

    initInputLanguageSelector();
    ui.updateLanguageBadge(getCurrentLanguageMode());
}