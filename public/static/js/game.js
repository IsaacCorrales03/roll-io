let socket;
let MAP_WIDTH;
let MAP_HEIGHT;
let TILE_SIZE;
let current_section_offset_x;
let current_section_offset_y;
let mapImage;

let isDM;
let myCharacterId;
let dm_player_list = [];
let dm_enemies_list = [];
let selectedCombatants = new Set();
let selectedToken = null;

/* ================================
   SOCKET.IO - CONEXIÓN
================================ */
window.onload = () => {
    socket = io();

    socket.on('connect', () => {
        console.log('✅ Socket conectado');
        socket.emit('join_campaign', { code: campaignCode });
        socket.emit("load_game_resources", { code: campaignCode });
    });

    socket.on('player_joined', d => {
        console.log('👋 Jugador se unió:', d);
    });

    socket.on('items_result', data => {
        const items = Array.isArray(data.items) ? data.items : Array.isArray(data) ? data : [];
        const container = document.getElementById('dm-item-list');
        container.innerHTML = '';

        if (items.length === 0) {
            container.innerHTML = '<div style="color:#888;font-family:\'IM Fell English\',serif;font-style:italic;">Sin items disponibles</div>';
            return;
        }

        items.forEach(item => {
            const type = item.meta.item_type?.toLowerCase() || '';
            const li = document.createElement('div');
            li.className = 'item-card feature-item';
            li.dataset.itemId = item.item_id || item.instance_id;

            li.innerHTML = `
                <div class="item-header">
                    <div class="feature-name">${item.meta.name}</div>
                    <div class="item-type-badge type-${type}">${item.meta.item_type}</div>
                </div>
                <div class="feature-desc">${item.meta.description}</div>
                <div class="item-meta">
                    ${item.meta.weight ? `<span>Peso: <strong>${item.meta.weight} lb</strong></span>` : ''}
                    ${item.equipped ? `<span class="equipped-badge">Equipado</span>` : ''}
                </div>
                <div class="item-actions">
                    <button class="item-btn btn-use" onclick="giveItemToPlayer('${item.item_id || item.instance_id}', '${item.meta.name}')">
                        Dar Item
                    </button>
                </div>
            `;
            container.appendChild(li);
        });
    });

    socket.on('game_resources_loaded', d => {
        isDM = d.is_dm;
        myCharacterId = d.my_character_id;
        MAP_WIDTH = d.current_section.width_px;
        MAP_HEIGHT = d.current_section.height_px;
        TILE_SIZE = d.current_section.tile_size;
        current_section_offset_x = d.current_section.offset_x;
        current_section_offset_y = d.current_section.offset_y;

        document.body.classList.toggle("dm-mode", isDM);

        // ── CORREGIDO: usar showPanel() para mostrar los paneles correctamente
        if (isDM) {
            showPanel('dm-panel', 'toggle-dm-panel');
        } else {
            showPanel('player-panel', 'toggle-player-panel');
            // El panel de combate es opcional para jugadores; mostrarlo siempre

        }

        const mapInfoEl = document.getElementById('map-info');
        if (mapInfoEl) mapInfoEl.style.display = 'block';

        document.getElementById('map-scene-name').textContent = d.current_scene.name;
        document.getElementById('map-grid-info').textContent =
            `Grid: ${TILE_SIZE}px · ${MAP_WIDTH / TILE_SIZE}×${MAP_HEIGHT / TILE_SIZE} tiles`;

        mapImage = new Image();
        mapImage.onload = initializeGame;
        mapImage.src = `/storage${d.current_scene.map_url}`.replace("uploads/", "");
    });

    socket.on('player_left', d => {
        console.log('👋 Jugador salió:', d);
    });

    socket.on('item_equipped_toggled', d => {
        socket.emit("get_character_data", { character_id: myCharacterId, campaign_code: campaignCode });
    });

    socket.on('chat_message', data => {
        const el = document.createElement('div');
        el.className = 'chat-message';
        el.innerHTML = `<strong>${escapeHtml(data.sender)}</strong>${escapeHtml(data.text)}`;
        chatMessages.appendChild(el);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        if (!chatOpen) {
            unreadMessages++;
            const badge = document.getElementById('chat-badge');
            badge.textContent = unreadMessages;
            badge.style.display = 'flex';
        }
    });

    socket.on('token_moved', d => {
        const token = document.querySelector(`[data-token-id="${d.token_id}"]`);
        if (!token) return;

        token.style.left = `${d.x * TILE_SIZE + TILE_SIZE / 2}px`;
        token.style.top = `${d.y * TILE_SIZE + TILE_SIZE / 2}px`;

        const oldX = parseInt(token.dataset.gridX || 0);
        const oldY = parseInt(token.dataset.gridY || 0);

        if (typeof updateGridState === 'function') {
            updateGridState(d.token_id, oldX, oldY, d.x, d.y);
        }

        token.dataset.gridX = d.x;
        token.dataset.gridY = d.y;
    });

    socket.on('error', d => console.error('❌ Error del servidor:', d));

    socket.on('entities_result', data => {
        dm_player_list = data.players || [];
        dm_enemies_list = data.enemies || [];
        renderDMEntities(data);
    });

    socket.on("ac_result", data => {
        const el = document.getElementById('char-ac');
        if (el) el.textContent = data.value || '--';
    });

    socket.on("enemy_created", data => {
        if (document.querySelector(`[data-token-id="${data.id}"]`)) return;
        const token = createTokenElement(data);
        document.getElementById("tokens-container").appendChild(token);
        updateGridState(data.id, null, null, data.x, data.y);
    });

    socket.on("tokens_sync", tokens => {
        document.querySelectorAll(".token").forEach(t => t.remove());
        initializeGrid();
        tokens.forEach(data => {
            const token = createTokenElement(data);
            document.getElementById("tokens-container").appendChild(token);
            updateGridState(data.id, null, null, data.x, data.y);
        });
    });

    socket.on("inventory_updated", d => renderCharacterGearAndInventory(d));
    socket.on("ac_result", (data) => {
        document.getElementById('char-ac').textContent = data.value || '--';

    });
    socket.on("character_data_received", c => {
        const nameEl = document.getElementById('char-name');
        if (nameEl) nameEl.textContent = c.name;
        console.log(c)
        const metaEl = document.getElementById('char-meta');
        if (metaEl) metaEl.textContent = `${c.race.name} · ${c.class.name} · Nivel ${c.level}`;

        const hpEl = document.getElementById('char-hp');
        if (hpEl) hpEl.textContent = `${c.hp.current} / ${c.hp.max}`;

        const currentWeight = c.current_weight ?? 0;
        const maxWeight = c.max_weight ?? 0;
        const weightEl = document.getElementById('char-weight');
        if (weightEl) weightEl.textContent = `${currentWeight} / ${maxWeight} lb`;

        const pct = maxWeight > 0 ? Math.min((currentWeight / maxWeight) * 100, 100) : 0;
        const bar = document.getElementById('weight-bar');
        if (bar) {
            bar.style.width = `${pct}%`;
            bar.style.background = pct >= 90
                ? 'linear-gradient(90deg,#dc2626,#ef4444)'
                : pct >= 60
                    ? 'linear-gradient(90deg,#d97706,#f59e0b)'
                    : 'linear-gradient(90deg,#8a6830,#d4a853)';
        }
    socket.emit("get_ac", { actor_id: myCharacterId });
        const STAT_MAP = { STR: 'STR', DEX: 'DEX', CON: 'CON', INT: 'INT', WIS: 'WIS', CHA: 'CHA' };
        const statsDiv = document.getElementById('stats');
        statsDiv.innerHTML = ''; // limpiar antes
        Object.entries(STAT_MAP).forEach(([abbr, key]) => {
            const value = c.attributes[key];
            const modifier = Math.floor((value - 10) / 2);
            const modStr = modifier >= 0 ? `+${modifier}` : `${modifier}`;
            const el = document.createElement('div');
            el.className = 'stat-item';
            el.innerHTML = `
            <div class="stat-label">${abbr}</div>
            <div class="stat-value">${value}</div>
            <div class="stat-modifier">${modStr}</div>
        `;
            statsDiv.appendChild(el);
        });
        const featuresList = document.getElementById('features-list');
        featuresList.innerHTML = '';
        c.features.forEach(f => {
            const li = document.createElement('li');
            li.className = 'feature-item';
            li.innerHTML = `
        <div class="feature-name">${f.name} <span style="font-family:'IM Fell English',serif;font-style:italic;font-size:12px;color:#a78bfa;font-weight:normal;">${f.type}</span></div>
        <div class="feature-desc">${f.description}</div>
    `;
            featuresList.appendChild(li);
        });

        // Separador + Proficiencias
        const profSection = document.createElement('li');
        profSection.style.cssText = 'list-style:none;margin-top:22px;padding-top:0;border:none;background:none;';
        profSection.innerHTML = `<div class="section-title">Competencias</div>`;
        featuresList.appendChild(profSection);

        const profGroups = [
            { label: 'Salvaciones', items: c.saving_throw_proficiencies },
            { label: 'Armaduras', items: c.armor_proficiencies },
            { label: 'Armas', items: c.weapon_proficiencies },
            { label: 'Habilidades',  items: c.skill_proficiencies ?? []    }
        ];
        profGroups.forEach(group => {
            if (!group.items?.length) return;
            const li = document.createElement('li');
            li.className = 'feature-item';

            // Skill proficiencies tienen objeto completo con descripción
            const isSkills = group.label === 'Habilidades' && typeof group.items[0] === 'object';

            li.innerHTML = `
        <div class="feature-name" style="font-size:12px;letter-spacing:1.5px;">${group.label}</div>
        <div style="margin-top:8px;display:flex;flex-direction:column;gap:8px;">
            ${isSkills
                    ? group.items.map(s => `
                    <div style="padding:8px 10px;background:rgba(212,168,83,0.04);
                                border:1px solid rgba(212,168,83,0.12);border-radius:6px;
                                border-left:2px solid rgba(167,139,250,0.5);">
                        <div style="font-family:'Cinzel',serif;font-size:11px;font-weight:700;
                                    letter-spacing:1px;text-transform:uppercase;color:var(--rune-bright);
                                    margin-bottom:3px;">${s.name}</div>
                        <div style="font-family:'IM Fell English',serif;font-style:italic;
                                    font-size:13px;color:var(--text-muted);line-height:1.5;">
                            ${s.description}
                        </div>
                    </div>`
                    ).join('')
                    : `<div style="display:flex;flex-wrap:wrap;gap:5px;">
                    ${group.items.map(i =>
                        `<span style="font-family:'Cinzel',serif;font-size:10px;font-weight:700;
                                      letter-spacing:0.8px;text-transform:uppercase;padding:3px 9px;
                                      background:rgba(212,168,83,0.07);border:1px solid rgba(212,168,83,0.2);
                                      border-radius:4px;color:var(--text-muted);">
                            ${i.replace(/_/g, ' ')}
                        </span>`
                    ).join('')}
                   </div>`
                }
        </div>
    `;
            featuresList.appendChild(li);
        });

        // Equipo
        renderCharacterGearAndInventory(c);
    });
    socket.on("combat_started", d => {      
        if (isDM) {
            console.log("combat started but is DM")
            showPanel('dm-panel', 'toggle-dm-panel');
        } else {
            console.log("combat started")
            hidePanel('player-panel', 'toggle-player-panel');
            showPanel('combat-panel', 'toggle-combat-panel')
        }

    })
};

/* ── Item search ── */
document.addEventListener('DOMContentLoaded', () => {
    const itemSearch = document.getElementById('item-search');
    if (itemSearch) {
        itemSearch.addEventListener('input', e => {
            const filter = e.target.value.toLowerCase();
            document.querySelectorAll('#dm-item-list .item-card').forEach(card => {
                const name = card.querySelector('.feature-name')?.textContent.toLowerCase() || '';
                const type = card.querySelector('.item-type-badge')?.textContent.toLowerCase() || '';
                card.style.display = name.includes(filter) || type.includes(filter) ? 'block' : 'none';
            });
        });
    }
});

/* ================================
   RENDER CHARACTER GEAR & INVENTORY
================================ */
function renderCharacterGearAndInventory(character) {
    const gearList = document.getElementById('gear-list');
    if (gearList) {
        gearList.innerHTML = `
            <li class="feature-item">
                <div class="feature-name">Arma Principal</div>
                <div class="feature-desc">${character.weapon?.name || "Sin arma equipada"}</div>
            </li>
        `;
    }

    const inventoryList = document.getElementById('inventory-list');
    if (!inventoryList) return;
    inventoryList.innerHTML = '';

    if (!character.inventory?.length) {
        inventoryList.innerHTML = '<li class="feature-item"><div class="feature-desc">Sin objetos en el inventario.</div></li>';
        return;
    }

    character.inventory.forEach(item => {
        const type = item.meta.item_type?.toLowerCase() || '';
        const li = document.createElement('li');
        li.className = 'feature-item item-card';
        li.innerHTML = `
            <div class="item-header">
                <div class="feature-name">${item.meta.name}</div>
                <div class="item-type-badge type-${type}">${item.meta.item_type}</div>
            </div>
            <div class="feature-desc">${item.meta.description}</div>
            <div class="item-meta">
                <span>Cantidad: <strong>${item.quantity}</strong></span>
                ${item.meta.weight ? `<span>Peso: <strong>${item.meta.weight} lb</strong></span>` : ''}
            </div>
            <div class="item-actions">
                ${item.equippable
                ? item.equipped
                    ? `<button class="item-btn btn-unequip" onclick="handleItemAction('equip','${item.instance_id}')">Desequipar</button>`
                    : `<button class="item-btn btn-equip"   onclick="handleItemAction('equip','${item.instance_id}')">Equipar</button>`
                : `<button class="item-btn btn-use" onclick="handleItemAction('use','${item.instance_id}')">Usar</button>`
            }
                <button class="item-btn btn-drop" onclick="handleItemAction('drop','${item.instance_id}')">Tirar</button>
            </div>
        `;
        inventoryList.appendChild(li);
    });
}

/* ================================
   CREATE TOKEN ELEMENT
================================ */
function createTokenElement(data) {
    const token = document.createElement("div");
    token.className = "token enemy";
    token.dataset.tokenId = data.id;
    token.dataset.name = data.label ?? "";
    token.dataset.hp = data.hp ?? 0;
    token.dataset.maxHp = data.max_hp ?? 0;
    token.dataset.ac = data.ac ?? 10;
    token.dataset.gridX = data.x;
    token.dataset.gridY = data.y;

    token.style.left = `${data.x * TILE_SIZE + TILE_SIZE / 2}px`;
    token.style.top = `${data.y * TILE_SIZE + TILE_SIZE / 2}px`;
    token.style.width = `${(data.width ?? 1) * TILE_SIZE}px`;
    token.style.height = `${(data.height ?? 1) * TILE_SIZE}px`;

    if (data.asset) {
        const img = document.createElement('img');
        img.src = data.asset;
        img.alt = data.label || '';
        img.draggable = false;
        img.style.cssText = 'width:100%;height:100%;object-fit:contain;';
        token.appendChild(img);
    }
    return token;
}

/* ================================
   MAP PAN / ZOOM
================================ */
const mapViewport = document.getElementById('map-viewport');
const mapContainer = document.getElementById('map-container');
const mapCanvas = document.getElementById('map-canvas');
const mapCtx = mapCanvas.getContext('2d');
const gridCanvas = document.getElementById('grid-canvas');
const gridCtx = gridCanvas.getContext('2d');

let mapScale = 1;
let mapPanX = 0;
let mapPanY = 0;
let isPanning = false;
let panStartX = 0;
let panStartY = 0;
let showGridOverlay = true;

let GRID_COLS;
let GRID_ROWS;

/* ================================
   INITIALIZE GAME
================================ */
function initializeGame() {
    mapCanvas.width = MAP_WIDTH;
    mapCanvas.height = MAP_HEIGHT;
    gridCanvas.width = MAP_WIDTH;
    gridCanvas.height = MAP_HEIGHT;
    GRID_COLS = Math.floor(MAP_WIDTH / TILE_SIZE);
    GRID_ROWS = Math.floor(MAP_HEIGHT / TILE_SIZE);

    renderMap();
    centerMap();

    if (!isDM && myCharacterId) loadCharacter();

    if (isDM) {
        socket.emit("get_entities", { campaign_code: campaignCode });
        initializeGrid();
        setupDMControls();
    }

    socket.emit("get_tokens", { campaign_code: campaignCode });
    hideLoader();
}

function renderMap() {
    mapCtx.drawImage(
        mapImage,
        current_section_offset_x, current_section_offset_y,
        MAP_WIDTH, MAP_HEIGHT,
        0, 0, MAP_WIDTH, MAP_HEIGHT
    );
    if (showGridOverlay) drawGrid();
    else gridCtx.clearRect(0, 0, MAP_WIDTH, MAP_HEIGHT);
}

function drawGrid() {
    gridCtx.clearRect(0, 0, MAP_WIDTH, MAP_HEIGHT);
    gridCtx.strokeStyle = 'rgba(255,255,255,0.3)';
    gridCtx.lineWidth = 1;

    for (let x = 0; x <= MAP_WIDTH; x += TILE_SIZE) {
        gridCtx.beginPath();
        gridCtx.moveTo(x, 0);
        gridCtx.lineTo(x, MAP_HEIGHT);
        gridCtx.stroke();
    }
    for (let y = 0; y <= MAP_HEIGHT; y += TILE_SIZE) {
        gridCtx.beginPath();
        gridCtx.moveTo(0, y);
        gridCtx.lineTo(MAP_WIDTH, y);
        gridCtx.stroke();
    }
}

function updateMapTransform() {
    mapContainer.style.transform = `translate(${mapPanX}px, ${mapPanY}px) scale(${mapScale})`;
}

function centerMap() {
    const vw = mapViewport.clientWidth;
    const vh = mapViewport.clientHeight;
    if (MAP_WIDTH < vw) mapPanX = (vw - MAP_WIDTH) / 2;
    if (MAP_HEIGHT < vh) mapPanY = (vh - MAP_HEIGHT) / 2;
    updateMapTransform();
}

function resetMapView() {
    mapScale = 1; mapPanX = 0; mapPanY = 0;
    centerMap();
}

function toggleGrid() {
    showGridOverlay = !showGridOverlay;
    renderMap();
}

/* Pan */
mapViewport.addEventListener('mousedown', e => {
    if (e.target !== mapViewport && e.target !== mapCanvas && e.target !== gridCanvas) return;
    isPanning = true;
    panStartX = e.clientX - mapPanX;
    panStartY = e.clientY - mapPanY;
    mapViewport.classList.add('panning');
});

document.addEventListener('mousemove', e => {
    if (!isPanning) return;
    mapPanX = e.clientX - panStartX;
    mapPanY = e.clientY - panStartY;
    updateMapTransform();
});

document.addEventListener('mouseup', () => {
    isPanning = false;
    mapViewport.classList.remove('panning');
});

/* Zoom */
mapViewport.addEventListener('wheel', e => {
    e.preventDefault();
    const rect = mapViewport.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const factor = e.deltaY > 0 ? 0.9 : 1.1;
    const newScale = Math.max(0.3, Math.min(4, mapScale * factor));
    const worldX = (mouseX - mapPanX) / mapScale;
    const worldY = (mouseY - mapPanY) / mapScale;
    mapPanX = mouseX - worldX * newScale;
    mapPanY = mouseY - worldY * newScale;
    mapScale = newScale;
    updateMapTransform();
}, { passive: false });

/* ================================
   CHAT
================================ */
let chatOpen = false;
let unreadMessages = 0;
const chatMessages = document.getElementById('chat-messages');

function openChat() {
    chatOpen = true;
    document.getElementById('chat-collapsed').style.display = 'none';
    document.getElementById('chat-expanded').style.display = 'block';
    document.getElementById('chat-input').focus();
    unreadMessages = 0;
    document.getElementById('chat-badge').style.display = 'none';
}

function closeChat() {
    chatOpen = false;
    document.getElementById('chat-collapsed').style.display = 'block';
    document.getElementById('chat-expanded').style.display = 'none';
}

document.addEventListener('keydown', e => {
    if (chatOpen) {
        if (e.key === 'Escape') closeChat();
    } else {
        if ((e.key === 't' || e.key === 'T' || e.key === 'Enter') &&
            document.activeElement.tagName !== 'INPUT' &&
            document.activeElement.tagName !== 'TEXTAREA') {
            e.preventDefault();
            openChat();
        }
    }
});

document.addEventListener('click', e => {
    if (!chatOpen) return;
    const chatWidget = document.querySelector('.chat-widget');
    if (chatWidget && !chatWidget.contains(e.target)) closeChat();
});

document.getElementById('chat-form').onsubmit = e => {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    if (!input.value.trim()) return;
    socket.emit('chat_message', { code: campaignCode, text: input.value });
    input.value = '';
};

function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}

/* ================================
   TABS
================================ */
function openTab(name) {
    document.querySelectorAll('#player-panel .tab').forEach(t => t.style.display = 'none');
    const target = document.getElementById(`tab-${name}`);
    if (target) target.style.display = 'block';
    document.querySelectorAll('#player-panel .tab-btn').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById(`tab-btn-${name}`);
    if (btn) btn.classList.add('active');
}

function openCombatTab(name) {
    document.querySelectorAll('#combat-panel .tab').forEach(t => t.style.display = 'none');
    const target = document.getElementById(`tab-${name}`);
    if (target) target.style.display = 'block';
    document.querySelectorAll('#combat-panel .tab-btn').forEach(b => b.classList.remove('active'));
    // find the clicked button
    const btns = document.querySelectorAll('#combat-panel .tab-btn');
    btns.forEach(b => { if (b.textContent.toLowerCase().includes(name.slice(0, 4))) b.classList.add('active'); });
}

function openDMTab(name) {
    ['map', 'entities', 'combat', 'items'].forEach(n => {
        const t = document.getElementById(`dm-tab-${n}`);
        if (t) t.style.display = 'none';
        const b = document.getElementById(`dm-tab-btn-${n}`);
        if (b) b.classList.remove('active');
    });
    const tab = document.getElementById(`dm-tab-${name}`);
    if (tab) tab.style.display = 'block';
    const btn = document.getElementById(`dm-tab-btn-${name}`);
    if (btn) btn.classList.add('active');

    if (name === 'items') socket.emit('get_items');
}

/* ================================
   LOAD CHARACTER
================================ */
function loadCharacter() {
    socket.emit("get_character_data", {
        character_id: myCharacterId,
        campaign_code: campaignCode
    });
}

/* ================================
   TOKEN PREVIEW
================================ */
const preview = document.getElementById('token-preview');

document.addEventListener('mouseover', e => {
    const token = e.target.closest('.token');
    if (!token) { preview.style.display = 'none'; return; }

    const rect = token.getBoundingClientRect();
    preview.style.display = 'block';
    preview.style.left = (rect.left + rect.width / 2) + 'px';
    preview.style.top = (rect.top - 12) + 'px';
    preview.innerHTML = `
        <div class="preview-name">${token.dataset.name || '???'}</div>
        <div class="preview-info">${token.dataset.level ? `Nivel ${token.dataset.level} ${token.dataset.class}` : 'Entidad'}</div>
        <div class="preview-stats">
            <div><strong>❤ ${token.dataset.hp || 0}/${token.dataset.maxHp || 0}</strong></div>
            <div>🛡 <span class="ac-value">${token.dataset.ac || 10}</span></div>
        </div>
    `;
});

document.addEventListener('mouseout', e => {
    if (e.target.closest('.token')) preview.style.display = 'none';
});

document.getElementById('map-viewport').addEventListener('mouseleave', () => {
    preview.style.display = 'none';
});

/* ================================
   ITEM ACTIONS
================================ */
function handleItemAction(action, itemId) {
    if (action === 'equip') {
        socket.emit("toggle_equip_item", { item_id: itemId, character_id: myCharacterId });
    } else if (action === 'use') {
        console.log("Usando objeto:", itemId);
    } else if (action === 'drop') {
        console.log("Tirando objeto:", itemId);
    }
}

/* ================================
   GRID LOGIC
================================ */
let gridState = [];

function initializeGrid() {
    gridState = [];
    for (let y = 0; y < GRID_ROWS; y++) {
        gridState[y] = [];
        for (let x = 0; x < GRID_COLS; x++) gridState[y][x] = null;
    }
    document.querySelectorAll('.token').forEach(token => {
        const x = parseInt(token.dataset.gridX || 0);
        const y = parseInt(token.dataset.gridY || 0);
        if (isValidGridPosition(x, y)) {
            gridState[y][x] = { tokenId: token.dataset.tokenId, name: token.dataset.name };
        }
    });
}

function isValidGridPosition(x, y) {
    return x >= 0 && x < GRID_COLS && y >= 0 && y < GRID_ROWS;
}

function isCellOccupied(x, y) {
    if (!isValidGridPosition(x, y)) return true;
    return gridState[y][x] !== null;
}

function updateGridState(tokenId, oldX, oldY, newX, newY) {
    if (gridState[oldY] && gridState[oldY][oldX]) gridState[oldY][oldX] = null;
    if (isValidGridPosition(newX, newY)) {
        const token = document.querySelector(`[data-token-id="${tokenId}"]`);
        gridState[newY][newX] = { tokenId, name: token?.dataset.name || 'Unknown' };
    }
}

/* ================================
   ATTACK BUILDER
================================ */
function parseDamageExpression(expr) {
    const match = expr.match(/^(\d+)d(\d+)([+-]\d+)?$/i);
    if (!match) return null;
    return {
        dice_count: parseInt(match[1]),
        dice_size: parseInt(match[2]),
        damage_bonus: match[3] ? parseInt(match[3]) : 0
    };
}

function addAttack() {
    const container = document.getElementById("attacks-container");
    const div = document.createElement("div");
    div.className = "attack-item";
    div.innerHTML = `
        <input type="text"   class="attack-name"        placeholder="Nombre del ataque">
        <input type="number" class="attack-bonus"        placeholder="Bonus al ataque" value="0">
        <input type="text"   class="attack-damage"       placeholder="Daño (ej: 1d6+2)">
        <label>Tipo de ataque</label>
        <select class="attack-category">
            <option value="melee">Melee</option>
            <option value="ranged">Ranged</option>
        </select>
        <label>Tipo de daño</label>
        <select class="attack-damage-type">
            <option value="slashing">Slashing</option>
            <option value="piercing">Piercing</option>
            <option value="bludgeoning">Bludgeoning</option>
            <option value="fire">Fire</option>
            <option value="cold">Cold</option>
            <option value="poison">Poison</option>
            <option value="necrotic">Necrotic</option>
            <option value="radiant">Radiant</option>
        </select>
        <button type="button" onclick="removeAttack(this)">Eliminar</button>
    `;
    container.appendChild(div);
}

function removeAttack(button) { button.parentElement.remove(); }

function collectAttacks() {
    const attacks = [];
    document.querySelectorAll(".attack-item").forEach(el => {
        const name = el.querySelector(".attack-name")?.value.trim();
        const bonus = parseInt(el.querySelector(".attack-bonus")?.value) || 0;
        const damageExpr = el.querySelector(".attack-damage")?.value.trim();
        const damageType = el.querySelector(".attack-damage-type")?.value;
        if (!name || !damageExpr) return;
        const parsed = parseDamageExpression(damageExpr);
        if (!parsed) return;
        attacks.push({ name, attack_bonus: bonus, ...parsed, damage_type: damageType });
    });
    return attacks;
}

async function createEnemy() {
    const name = document.getElementById('enemy-name').value.trim();
    const hp = parseInt(document.getElementById('enemy-hp').value);
    const maxHp = parseInt(document.getElementById('enemy-max-hp').value);
    const ac = parseInt(document.getElementById('enemy-ac').value) || 10;
    const sizeVal = document.getElementById('enemy-size').value;
    const fileInput = document.getElementById('enemy-asset');

    const attributes = {
        STR: parseInt(document.getElementById("enemy-str").value),
        DEX: parseInt(document.getElementById("enemy-dex").value),
        CON: parseInt(document.getElementById("enemy-con").value),
        INT: parseInt(document.getElementById("enemy-int").value),
        WIS: parseInt(document.getElementById("enemy-wis").value),
        CHA: parseInt(document.getElementById("enemy-cha").value),
    };

    const attacks = collectAttacks();
    if (!name || isNaN(hp) || isNaN(maxHp) || !fileInput.files.length || attacks.length === 0) return;

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const uploadRes = await fetch("/api/enemies/upload", { method: "POST", body: formData });
        if (!uploadRes.ok) return;
        const uploadData = await uploadRes.json();
        if (!uploadData.success) return;

        socket.emit("create_enemy", {
            campaign_code: campaignCode,
            name, hp, max_hp: maxHp, ac,
            asset: uploadData.asset_url,
            size: sizeVal.split('x').map(Number),
            attributes, attacks
        });

        document.getElementById('enemy-name').value = "";
        document.getElementById('enemy-hp').value = "";
        document.getElementById('enemy-max-hp').value = "";
        document.getElementById('enemy-asset').value = "";
        document.getElementById('attacks-container').innerHTML = "";

    } catch (err) { console.error("Error en upload:", err); }
}

/* ================================
   DM ENTITIES RENDER
================================ */
function renderDMEntities(data) {
    const playerList = document.getElementById('dm-player-list');
    const enemyList = document.getElementById('dm-enemy-list');
    dm_player_list = [];
    dm_enemies_list = [];

    playerList.innerHTML = '';
    (data.characters || []).forEach(char => {
        dm_player_list.push(char);
        const pct = Math.round((char.hp / char.max_hp) * 100);
        const color = pct > 50 ? '#4ade80' : pct > 25 ? '#f59e0b' : '#f87171';
        const li = document.createElement('li');
        li.className = 'feature-item';
        li.dataset.charId = char.id;
        li.innerHTML = `
            <div class="entity-header">
                <span class="entity-name">${char.name}</span>
                <span class="entity-ac">🛡️ ${char.ac}</span>
            </div>
            <div class="entity-hp-bar-bg">
                <div class="entity-hp-bar" style="width:${pct}%;background:${color};"></div>
            </div>
            <div class="entity-hp-text">${char.hp} / ${char.max_hp} HP</div>
        `;
        playerList.appendChild(li);
    });

    if (!data.characters?.length) {
        playerList.innerHTML = '<li class="feature-item"><div class="feature-desc">Sin jugadores conectados.</div></li>';
    }

    enemyList.innerHTML = '';
    (data.enemies || []).forEach(enemy => {
        dm_enemies_list.push(enemy);
        const pct = Math.round((enemy.hp / enemy.max_hp) * 100);
        const color = pct > 50 ? '#4ade80' : pct > 25 ? '#f59e0b' : '#f87171';
        const li = document.createElement('li');
        li.className = 'feature-item';
        li.dataset.charId = enemy.id;
        li.innerHTML = `
            <div class="entity-header">
                <span class="entity-name">${enemy.name}</span>
                <span class="entity-ac">🛡️ ${enemy.ac}</span>
            </div>
            <div class="entity-hp-bar-bg">
                <div class="entity-hp-bar" style="width:${pct}%;background:${color};"></div>
            </div>
            <div class="entity-hp-text">${enemy.hp} / ${enemy.max_hp} HP</div>
        `;
        enemyList.appendChild(li);
    });

    if (!data.enemies?.length) {
        enemyList.innerHTML = '<li class="feature-item"><div class="feature-desc">Sin enemigos creados.</div></li>';
    }

    renderCombatTab();
}

function renderCombatTab() {
    const container = document.getElementById("combat-selection-container");
    if (!container) return;
    container.innerHTML = "";

    if (dm_player_list.length) {
        const sec = document.createElement("div");
        sec.innerHTML = `<p style="font-family:'Cinzel',serif;font-size:11px;color:#9a8060;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px;">Jugadores</p>`;
        dm_player_list.forEach(p => sec.appendChild(createCombatItem(p, "player")));
        container.appendChild(sec);
    }

    if (dm_enemies_list.length) {
        const sec = document.createElement("div");
        sec.style.marginTop = "14px";
        sec.innerHTML = `<p style="font-family:'Cinzel',serif;font-size:11px;color:#9a8060;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px;">Enemigos</p>`;
        dm_enemies_list.forEach(e => sec.appendChild(createCombatItem(e, "enemy")));
        container.appendChild(sec);
    }
}

function createCombatItem(entity, type) {
    const div = document.createElement("div");
    div.className = "combat-item";
    div.dataset.id = entity.id;
    div.dataset.type = type;
    div.innerHTML = `
        <img src="${entity.asset_url || ''}" onerror="this.style.display='none'" width="36" height="36">
        <span style="flex:1;font-family:'Cinzel',serif;font-size:13px;">${entity.name}</span>
        <span style="font-size:12px;color:#9a8060;font-family:'Cinzel',serif;">${entity.hp}/${entity.max_hp}</span>
    `;
    div.addEventListener("click", () => {
            toggleCombatSelection(div, entity.id);
    });

    return div;
}

function toggleCombatSelection(el, id) {
    console.log("selected ", el, id)
    if (selectedCombatants.has(id)) {
        selectedCombatants.delete(id);
        el.classList.remove("selected");
    } else {
        selectedCombatants.add(id);
        el.classList.add("selected");
    }
}
function startCombat() {

    if (selectedCombatants.size < 2) {
        console.warn("Se requieren al menos 2 combatientes");
        return;
    }

    socket.emit("start_combat", {
        campaign_code: campaignCode,
        combatants: Array.from(selectedCombatants)
    });

    selectedCombatants.clear();
    document.querySelectorAll(".combat-item.selected")
        .forEach(el => el.classList.remove("selected"));
}

/* ================================
   DM TOKEN CONTROLS
================================ */
function setupDMControls() {
    document.addEventListener('click', e => {
        const token = e.target.closest('.token');
        if (token) {
            e.stopPropagation();
            document.querySelectorAll('.token').forEach(t => t.classList.remove('selected'));
            selectedToken = token;
            token.classList.add('selected');
            return;
        }
        if (selectedToken && !e.target.closest('.token')) {
            selectedToken.classList.remove('selected');
            selectedToken = null;
        }
    });

    function handleGridClick(e, canvas) {
        if (!selectedToken) return;
        e.stopPropagation();
        const rect = canvas.getBoundingClientRect();
        const tileX = Math.floor((e.clientX - rect.left) / (TILE_SIZE * mapScale));
        const tileY = Math.floor((e.clientY - rect.top) / (TILE_SIZE * mapScale));
        if (!isValidGridPosition(tileX, tileY) || isCellOccupied(tileX, tileY)) return;
        const oldX = parseInt(selectedToken.dataset.gridX || 0);
        const oldY = parseInt(selectedToken.dataset.gridY || 0);
        updateGridState(selectedToken.dataset.tokenId, oldX, oldY, tileX, tileY);
        selectedToken.dataset.gridX = tileX;
        selectedToken.dataset.gridY = tileY;
        socket.emit("move_token", { campaign_code: campaignCode, token_id: selectedToken.dataset.tokenId, x: tileX, y: tileY });
        selectedToken.classList.remove('selected');
        selectedToken = null;
    }

    gridCanvas.addEventListener('click', e => handleGridClick(e, gridCanvas));
    mapCanvas.addEventListener('click', e => handleGridClick(e, mapCanvas));
}

/* ================================
   LOADING SCREEN
================================ */
const DD_QUOTES = [

    // ÉPICAS
    "No necesito suerte. Necesito alcance.",
    "Mi espada recuerda cada nombre que pronuncio.",
    "Si el destino quiere guerra, tendrá guerra.",
    "No todos sobreviven a una profecía. Yo sí.",
    "El miedo es para los que dudan.",
    "He visto demonios suplicar. Tú no impresionarás.",
    "Hoy no caeré. Hoy avanzamos.",
    "Mi juramento pesa más que tu armadura.",
    "No lucho por gloria. Lucho porque debo.",
    "Si esta es mi última batalla, que la recuerden.",

    // OSCURAS
    "Esa sombra no es nuestra.",
    "El silencio aquí no está vacío.",
    "El aire sabe a tumba antigua.",
    "La puerta no crujió. Susurró.",
    "Algo respira detrás del muro.",
    "No todos los ecos repiten sonidos.",
    "El mapa termina. El horror no.",
    "La antorcha parpadea cuando miente.",
    "Ese frío no es natural.",
    "No estamos solos. Nunca lo estuvimos.",

    // MESA / CAOS
    "El plan era bueno hasta que empezamos a ejecutarlo.",
    "¿Seguro que tocar eso es buena idea?",
    "El bardo dijo que funcionaría.",
    "Dividirse siempre termina igual.",
    "Eso no estaba en el plan. ¿Había plan?",
    "El pícaro sonrió. Mal presagio.",
    "El clérigo dejó de sonreír.",
    "El mago pidió seis segundos más.",
    "Nadie revisó si había trampas. Nadie.",
    "La estrategia murió en el primer turno.",

    // POR CLASE
    "Mi furia no negocia.",
    "El acero responde mejor que las palabras.",
    "La magia es disciplina, no espectáculo.",
    "El oro cambia manos. Yo no.",
    "La luz juzga.",
    "Mi patrono observa.",
    "El bosque escucha.",
    "El ki fluye, aunque el enemigo no.",
    "Las sombras son pacientes.",
    "Un crítico no es suerte. Es preparación.",

    // DRAMÁTICAS
    "Si caigo, que sea avanzando.",
    "Prometí protegerlos. Y cumplo.",
    "No era el héroe que querían. Era el que necesitaban.",
    "El sacrificio no siempre es visible.",
    "No todos los monstruos llevan garras.",
    "Cada cicatriz tiene un nombre.",
    "El deber no descansa.",
    "He perdido antes. No otra vez.",
    "Que canten sobre esto.",
    "Si sobrevivo, beberemos. Si no, recuérdenme.",

    // COMBATE
    "Rueda el dado.",
    "Que decida el acero.",
    "Uno más.",
    "Mantengan la línea.",
    "Apunten al flanco.",
    "Ahora.",
    "No retrocedan.",
    "Es ahora o nunca.",
    "Respiren. Golpeen.",
    "Terminemos esto."
];
const LOADING_STEPS = [
    "Generando el mundo...",
    "Despertando a los monstruos...",
    "Colocando trampas...",
    "Escondiendo el tesoro...",
    "Preparando al Dungeon Master...",
    "¡Que comience la aventura!",
];

(function initLoadingScreen() {
    const quoteEl = document.getElementById('loading-quote');
    const barEl = document.getElementById('loading-bar');
    const statusEl = document.getElementById('loading-status');

    quoteEl.textContent = DD_QUOTES[Math.floor(Math.random() * DD_QUOTES.length)];

    const quoteInterval = setInterval(() => {
        quoteEl.style.animation = 'none';
        void quoteEl.offsetHeight;
        quoteEl.style.animation = '';
        quoteEl.textContent = DD_QUOTES[Math.floor(Math.random() * DD_QUOTES.length)];
    }, 3000);

    let step = 0;
    const progressInterval = setInterval(() => {
        step++;
        barEl.style.width = `${(step / LOADING_STEPS.length) * 100}%`;
        statusEl.textContent = LOADING_STEPS[step - 1];
        if (step >= LOADING_STEPS.length) {
            clearInterval(progressInterval);
            clearInterval(quoteInterval);
        }
    }, 500);
})();

function hideLoader() {
    const screen = document.getElementById('loading-screen');
    if (!screen) return;
    screen.style.transition = 'opacity 0.8s ease';
    screen.style.opacity = '0';
    setTimeout(() => screen.remove(), 800);
}

/* ================================
   GIVE ITEM OVERLAY
================================ */
let _pendingGiveItemId = null;

function openGiveItemPopup(itemId, itemName) {
    _pendingGiveItemId = itemId;
    document.getElementById('give-item-name').textContent = `Objeto: ${itemName || itemId}`;

    const playerListEl = document.getElementById('give-item-player-list');
    playerListEl.innerHTML = '';

    if (!dm_player_list.length) {
        playerListEl.innerHTML = '<p style="color:#888;font-family:\'IM Fell English\',serif;font-style:italic;">Sin jugadores conectados.</p>';
    } else {
        dm_player_list.forEach(char => {
            const btn = document.createElement('button');
            btn.className = 'give-item-btn';
            btn.textContent = `🧙 ${char.name}`;
            btn.onclick = () => confirmGiveItem(char.id);
            playerListEl.appendChild(btn);
        });
    }

    const overlay = document.getElementById('give-item-overlay');
    overlay.style.display = 'flex';
}

function closeGiveItemPopup() {
    document.getElementById('give-item-overlay').style.display = 'none';
    _pendingGiveItemId = null;
}

function confirmGiveItem(targetCharId) {
    if (!_pendingGiveItemId) return;
    socket.emit('dm_give_item', {
        campaign_code: campaignCode,
        item_instance_id: _pendingGiveItemId,
        target_player_id: targetCharId,
    });
    closeGiveItemPopup();
}

function giveItemToPlayer(itemId, itemName) { openGiveItemPopup(itemId, itemName); }