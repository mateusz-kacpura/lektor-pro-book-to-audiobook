/**
 * Lektor Pro - Book Selector Module
 * Zarządza dynamiczną listą książek, zmianą aktywnej publikacji i aktualizacją UI.
 */
import * as api from '../api.js?v=20261009-i18n';
import { t } from '../i18n.js?v=20261009-i18n';
import * as ui from '../ui.js?v=20261009-i18n';

export async function initBookSelector({ onBookChanged }) {
    const bookSelect = document.getElementById("bookSelectDropdown");
    if (!bookSelect) return;

    try {
        const books = await api.fetchBooksList();
        bookSelect.innerHTML = "";
        books.forEach(b => {
            const opt = document.createElement("option");
            opt.value = b.slug;
            opt.textContent = `${b.title} (${b.total_pages} str.)`;
            if (b.is_active) opt.selected = true;
            bookSelect.appendChild(opt);
        });

        bookSelect.onchange = async () => {
            const chosenSlug = bookSelect.value;
            if (!chosenSlug) return;
            try {
                ui.showToast(t("messages.bookSwitching", { book: chosenSlug }));
                await api.switchActiveBook(chosenSlug);
                if (typeof onBookChanged === "function") {
                    await onBookChanged(chosenSlug);
                }
                ui.showToast(t("messages.bookChanged", { book: chosenSlug }));
            } catch (err) {
                alert(t("messages.bookChangeError", { error: err.message }));
            }
        };
    } catch (e) {
        console.error("Błąd ładowania listy książek:", e);
    }
}