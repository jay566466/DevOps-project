// ─── Password strength indicator ─────────────────────
(function () {
    const pwInput = document.getElementById('password');
    const strengthBar = document.getElementById('pw-strength');
    const form = pwInput ? pwInput.closest('form') : null;

    if (!pwInput || !strengthBar) return;

    function calcStrength(pw) {
        let score = 0;
        if (pw.length >= 8)  score++;
        if (pw.length >= 12) score++;
        if (/[A-Z]/.test(pw)) score++;
        if (/[a-z]/.test(pw)) score++;
        if (/\d/.test(pw))    score++;
        if (/[!@#$%^&*(),.?":{}|<>]/.test(pw)) score++;
        if (pw.length >= 16) score++;
        return score;
    }

    function getLabel(score) {
        if (score <= 2) return { cls: 'pw-weak',   label: 'Weak' };
        if (score <= 3) return { cls: 'pw-fair',   label: 'Fair' };
        if (score <= 5) return { cls: 'pw-good',   label: 'Good' };
        return              { cls: 'pw-strong', label: 'Strong' };
    }

    pwInput.addEventListener('input', () => {
        const pw = pwInput.value;
        if (!pw) {
            form && form.classList.remove('pw-weak','pw-fair','pw-good','pw-strong');
            strengthBar.title = '';
            return;
        }
        const score = calcStrength(pw);
        const { cls, label } = getLabel(score);
        form && form.classList.remove('pw-weak','pw-fair','pw-good','pw-strong');
        form && form.classList.add(cls);
        strengthBar.title = label;
    });

    // Confirm match indicator
    const confirmInput = document.getElementById('confirm_password');
    if (confirmInput) {
        function checkMatch() {
            const match = pwInput.value === confirmInput.value;
            confirmInput.style.borderColor = confirmInput.value
                ? (match ? 'var(--success)' : 'var(--danger)') : '';
        }
        confirmInput.addEventListener('input', checkMatch);
        pwInput.addEventListener('input', () => confirmInput.value && checkMatch());
    }
})();
