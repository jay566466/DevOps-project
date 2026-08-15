/**
 * Visual Grid CAPTCHA — image-selection widget
 * Works for login, register, and forgot-password pages.
 */
(function () {
    "use strict";

    // ── State ────────────────────────────────────────
    let selected = new Set();
    let gridImages = [];

    // ── DOM refs ─────────────────────────────────────
    const grid        = document.getElementById("captcha-grid");
    const promptEl    = document.getElementById("captcha-prompt");
    const hiddenInput = document.querySelector(".captcha-hidden-input");
    const refreshBtn  = document.getElementById("refresh-captcha");
    const statusEl    = document.getElementById("captcha-status");

    if (!grid || !hiddenInput) return;

    // ── Fetch and render a fresh grid ────────────────
    async function loadGrid() {
        grid.innerHTML = '<div class="captcha-loading"><span class="captcha-spinner"></span>Loading…</div>';
        promptEl.innerHTML = "";
        hiddenInput.value  = "";
        selected.clear();

        try {
            const res  = await fetch("/auth/captcha", {
                headers: { "X-CSRFToken": getCsrfToken() }
            });
            const data = await res.json();
            gridImages = data.images;
            promptEl.innerHTML = data.prompt;
            renderGrid(data.images);
            updateStatus();
        } catch (e) {
            grid.innerHTML = '<p class="captcha-error">Failed to load. <a href="#" id="retry-link">Retry</a></p>';
            document.getElementById("retry-link")?.addEventListener("click", (e) => {
                e.preventDefault(); loadGrid();
            });
        }
    }

    // ── Render 3×3 tile grid ─────────────────────────
    function renderGrid(images) {
        grid.innerHTML = "";
        images.forEach((src, idx) => {
            const tile = document.createElement("div");
            tile.className    = "captcha-tile";
            tile.dataset.idx  = idx;
            tile.setAttribute("role", "checkbox");
            tile.setAttribute("aria-checked", "false");
            tile.setAttribute("tabindex", "0");

            const img  = document.createElement("img");
            img.src    = src;
            img.alt    = `Image ${idx + 1}`;
            img.draggable = false;

            const check = document.createElement("div");
            check.className = "captcha-check";
            check.innerHTML = "✓";

            tile.appendChild(img);
            tile.appendChild(check);
            grid.appendChild(tile);

            tile.addEventListener("click",    () => toggleTile(tile, idx));
            tile.addEventListener("keydown",  (e) => {
                if (e.key === " " || e.key === "Enter") {
                    e.preventDefault(); toggleTile(tile, idx);
                }
            });
        });
    }

    // ── Toggle tile selection ─────────────────────────
    function toggleTile(tile, idx) {
        if (selected.has(idx)) {
            selected.delete(idx);
            tile.classList.remove("selected");
            tile.setAttribute("aria-checked", "false");
        } else {
            selected.add(idx);
            tile.classList.add("selected");
            tile.setAttribute("aria-checked", "true");
        }
        // Update hidden input
        hiddenInput.value = [...selected].sort((a,b)=>a-b).join(",");
        updateStatus();
    }

    // ── Status text ───────────────────────────────────
    function updateStatus() {
        if (!statusEl) return;
        const n = selected.size;
        statusEl.textContent = n === 0
            ? "Click to select matching images"
            : `${n} image${n > 1 ? "s" : ""} selected`;
        statusEl.className = n > 0 ? "captcha-status has-selection" : "captcha-status";
    }

    // ── Refresh button ────────────────────────────────
    if (refreshBtn) {
        refreshBtn.addEventListener("click", (e) => {
            e.preventDefault();
            refreshBtn.classList.add("spinning");
            loadGrid().finally(() => {
                setTimeout(() => refreshBtn.classList.remove("spinning"), 500);
            });
        });
    }

    // ── Initial load ─────────────────────────────────
    loadGrid();

})();

// ── Spinner CSS (injected once) ───────────────────────
(function() {
    if (document.getElementById("captcha-anim-style")) return;
    const s = document.createElement("style");
    s.id = "captcha-anim-style";
    s.textContent = `
        .spinning svg { animation: captcha-spin 0.5s linear; }
        @keyframes captcha-spin { to { transform: rotate(360deg); } }
        .captcha-spinner {
            display: inline-block;
            width: 20px; height: 20px;
            border: 2px solid rgba(255,255,255,0.2);
            border-top-color: #6366f1;
            border-radius: 50%;
            animation: captcha-spin 0.8s linear infinite;
            vertical-align: middle;
            margin-right: 8px;
        }
    `;
    document.head.appendChild(s);
})();
