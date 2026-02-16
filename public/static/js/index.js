
// Parallax effect for background blobs
let scrollY = 0;
window.addEventListener('scroll', () => {
    scrollY = window.scrollY;
    const blob1 = document.getElementById('blob1');
    const blob2 = document.getElementById('blob2');
    if (blob1) blob1.style.transform = `translateY(${scrollY * 0.3}px)`;
    if (blob2) blob2.style.transform = `translateY(${-scrollY * 0.2}px)`;
});

// Smooth scroll function
function scrollToSection(id) {
    const element = document.getElementById(id);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

// Error display
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    errorText.textContent = message;
    errorDiv.classList.remove('hidden');
    setTimeout(() => {
        errorDiv.classList.add('hidden');
    }, 5000);
}



// Join campaign let joinMode = false;

function renderJoinButton() {
    const container = document.getElementById('join-container');
    container.innerHTML = `
        <button
            id="join-toggle-btn"
            class="w-full py-4 px-6 bg-slate-700 text-white border border-slate-600 rounded-xl font-semibold text-lg hover:bg-slate-600 hover:border-slate-500 transition-all duration-300 ease-out hover:scale-105 active:scale-95"
        >
            Unirse con código
        </button>
    `;

    document
        .getElementById('join-toggle-btn')
        .addEventListener('click', enableJoinMode);
}

function enableJoinMode() {
    joinMode = true;
    const container = document.getElementById('join-container');

    container.innerHTML = `
        <form id="join-form" class="space-y-3">
            <div class="flex gap-2">
                <input
                    type="text"
                    id="campaign-code"
                    placeholder="Código de campaña"
                    maxlength="8"
                    class="flex-1 px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl font-mono text-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition-all uppercase tracking-wider"
                    autofocus
                />
                <button
                    type="submit"
                    id="join-submit-btn"
                    class="px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-500 text-white rounded-xl font-semibold hover:from-purple-500 hover:to-purple-400 transition-all duration-300 ease-out flex items-center justify-center min-w-[60px]"
                >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M13 7l5 5m0 0l-5 5m5-5H6"/>
                    </svg>
                </button>
            </div>

            <button
                type="button"
                id="cancel-join-btn"
                class="text-sm text-slate-500 hover:text-slate-400 transition-colors"
            >
                Cancelar
            </button>
        </form>
    `;

    document
        .getElementById('join-form')
        .addEventListener('submit', submitJoinForm);

    document
        .getElementById('cancel-join-btn')
        .addEventListener('click', () => {
            joinMode = false;
            renderJoinButton();
        });
}

function submitJoinForm(e) {
    e.preventDefault();

    const input = document.getElementById('campaign-code');
    const code = input.value.trim().toUpperCase();

    if (!code) {
        alert('Ingresa un código válido');
        return;
    }

    const btn = document.getElementById('join-submit-btn');
    btn.disabled = true;

    btn.innerHTML = `
        <svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10"
                    stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
    `;

    // Redirección directa al endpoint REAL
    window.location.href = `/join/${code}`;
}

// init
renderJoinButton();