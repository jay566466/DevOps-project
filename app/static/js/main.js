// ─── Auto-dismiss flash messages ─────────────────────
document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        el.style.opacity = '0';
        el.style.transform = 'translateX(40px)';
        setTimeout(() => el.remove(), 500);
    }, 5000);
});

// ─── Password toggle visibility ──────────────────────
document.querySelectorAll('.toggle-pw').forEach(btn => {
    btn.addEventListener('click', () => {
        const targetId = btn.dataset.target;
        const input = document.getElementById(targetId);
        if (!input) return;
        const isText = input.type === 'text';
        input.type = isText ? 'password' : 'text';
        btn.style.opacity = isText ? '1' : '0.5';
    });
});

// ─── CSRF helpers for fetch ───────────────────────────
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

function csrfHeaders(extra = {}) {
    return {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
        ...extra,
    };
}
