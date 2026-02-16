let socket = null;
let characterUuid = null;
let characterName = null;

const playersDiv = document.getElementById('players');
const playerCount = document.getElementById('playerCount');
const chatDiv = document.getElementById('chat');

function copyCode() {
    const code = campaignCode;

    // Fallback para navegadores que no soportan clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(code).then(() => {
            showToast('Código copiado al portapapeles');
        }).catch(() => {
            fallbackCopyCode(code);
        });
    } else {
        fallbackCopyCode(code);
    }
}

function fallbackCopyCode(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        showToast('Código copiado al portapapeles');
    } catch (err) {
        showToast('Error al copiar código', 'error');
    }

    document.body.removeChild(textArea);
}

function showToast(message, type = 'success') {
    // Remover toast anterior si existe
    const existingToast = document.getElementById('toast-notification');
    if (existingToast) {
        existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.id = 'toast-notification';
    toast.className = 'fixed top-24 right-4 z-50 animate-slide-in';

    const bgColor = type === 'success'
        ? 'from-green-600 to-green-500'
        : 'from-red-600 to-red-500';

    const icon = type === 'success'
        ? `<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
             <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
           </svg>`
        : `<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
             <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
           </svg>`;

    toast.innerHTML = `
        <div class="relative">
            <div class="absolute -inset-1 bg-gradient-to-r ${bgColor} rounded-xl blur opacity-50"></div>
            <div class="relative bg-gradient-to-r ${bgColor} rounded-xl px-6 py-4 shadow-xl flex items-center gap-3">
                ${icon}
                <span class="text-white font-semibold">${message}</span>
            </div>
        </div>
    `;

    document.body.appendChild(toast);

    // Animación de entrada
    setTimeout(() => {
        toast.style.animation = 'slide-in 0.3s ease-out';
    }, 10);

    // Remover después de 3 segundos
    setTimeout(() => {
        toast.style.animation = 'slide-out 0.3s ease-in';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}
function selectCharacter(uuid, name) {
    characterUuid = uuid;
    characterName = name;

    document.querySelectorAll('.character-btn').forEach(btn => {
        btn.classList.remove('border-purple-500');
        btn.querySelector('.character-check').classList.add('hidden');
    });

    const selectedBtn = document.querySelector(`[data-uuid="${uuid}"]`);
    if (selectedBtn) {
        selectedBtn.classList.add('border-purple-500');
        selectedBtn.querySelector('.character-check').classList.remove('hidden');
    }
    const readyBtn = document.getElementById('ready-btn');
    readyBtn.disabled = false;
    readyBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    readyBtn.classList.add('hover:shadow-xl', 'hover:shadow-purple-500/30', 'hover:scale-105', 'active:scale-95');
    console.log(`Selected character: ${name} (${uuid})`);

}

function readyUp() {
    if (!characterUuid) return;

    socket.emit('select_character', {
        code: campaignCode,
        character_uuid: characterUuid
    });
}

function startCampaign() {
    socket.emit('start_campaign', { code: campaignCode });
}

function updatePlayers(players) {
    playersDiv.innerHTML = '';
    playerCount.textContent = `(${players.length})`;

    if (players.length === 0) {
        playersDiv.innerHTML = `
                    <div class="text-center text-slate-500 py-8">
                        <svg class="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        Esperando jugadores...
                    </div>
                `;
        return;
    }

    players.forEach(p => {
        const el = document.createElement('div');
        el.className = 'bg-slate-700/30 border border-slate-600/50 rounded-xl px-4 py-3 flex items-center justify-between hover:bg-slate-700/50 transition-colors';

        const statusIcon = p.character_uuid
            ? `<svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                         <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                       </svg>`
            : `<svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                         <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                       </svg>`;

        el.innerHTML = `
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-lg flex items-center justify-center border border-purple-500/20">
                            <svg class="w-6 h-6 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                        </div>
                        <div>
                            <div class="font-semibold text-white">${p.username}</div>
                            <div class="text-xs text-slate-400">
    ${p.is_dm
                ? 'Dungeon Master'
                : p.character_uuid
                    ? `Listo — ${p.character_name}`
                    : 'Seleccionando personaje...'
            }
</div>
                        </div>
                    </div>
                    ${statusIcon}
                `;

        playersDiv.appendChild(el);
    });
}

function addChat(sender, text) {
    const firstMessage = chatDiv.querySelector('.text-center');
    if (firstMessage) firstMessage.remove();

    const el = document.createElement('div');
    el.className = 'bg-slate-800/50 rounded-lg p-3 border border-slate-700/50';
    el.innerHTML = `
                <div class="font-semibold text-sm text-purple-300 mb-1">${sender}</div>
                <div class="text-slate-200">${text}</div>
            `;
    chatDiv.appendChild(el);
    chatDiv.scrollTop = chatDiv.scrollHeight;
}

window.onload = () => {
    socket = io();

    socket.on('connect', () => {
        socket.emit('join_campaign', { code: campaignCode });
    });

    socket.on('player_joined', d => updatePlayers(d.players));
    socket.on('player_left', d => updatePlayers(d.players));
    socket.on('chat_message', d => addChat(d.sender, d.text));
    socket.on("campaign_started", d => {
        window.location.href = `/game?code=${d.code}`;
    });
};

document.getElementById('chat-form').addEventListener('submit', e => {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    if (!input.value.trim()) return;

    socket.emit('chat_message', {
        code: campaignCode,
        text: input.value
    });

    input.value = '';
});
