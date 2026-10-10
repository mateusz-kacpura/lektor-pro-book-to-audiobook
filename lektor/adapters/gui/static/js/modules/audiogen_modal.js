/**
 * Lektor Pro - Audio Generation Modal Module
 * Zarządza oknem modala syntezy audio, podglądem postępu i skrótami klawiatury.
 */

export function initAudioGenModal({ onFetchStatus }) {
    const modalBackdrop = document.getElementById("audioGenModalBackdrop");
    const btnOpenHeader = document.getElementById("btnOpenAudioModal");
    const btnOpenDock = document.getElementById("btnDockAudioGen");
    const btnClose = document.getElementById("btnAudioGenClose");
    const btnDismiss = document.getElementById("btnAudioGenDismiss");
    const headerPercent = document.getElementById("headerPercent");

    function openAudioModal() {
        if (modalBackdrop) {
            modalBackdrop.style.display = "flex";
            if (typeof onFetchStatus === "function") onFetchStatus();
        }
    }

    function closeAudioModal() {
        if (modalBackdrop) {
            modalBackdrop.style.display = "none";
        }
    }

    if (btnOpenHeader) btnOpenHeader.onclick = openAudioModal;
    if (btnOpenDock) btnOpenDock.onclick = openAudioModal;
    if (btnClose) btnClose.onclick = closeAudioModal;
    if (btnDismiss) btnDismiss.onclick = closeAudioModal;
    if (headerPercent) {
        headerPercent.style.cursor = "pointer";
        headerPercent.title = "Otwórz panel generowania audio";
        headerPercent.onclick = openAudioModal;
    }

    if (modalBackdrop) {
        modalBackdrop.addEventListener("click", (e) => {
            if (e.target === modalBackdrop) closeAudioModal();
        });
    }

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && modalBackdrop && modalBackdrop.style.display === "flex") {
            closeAudioModal();
        }
    });
}