let socket;
let MAP_WIDTH;
let MAP_HEIGHT;
let TILE_SIZE;
let current_section_offset_x;
let current_section_offset_y;

let isDM;
let myCharacterId;
let dm_player_list = [];
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
        // TODO: Actualizar lista de jugadores/tokens
    });
socket.on('items_result', data => {
    const items = Array.isArray(data.items) ? data.items : Array.isArray(data) ? data : [];
    const container = document.getElementById('dm-item-list');
    container.innerHTML = '';

    if (items.length === 0) {
        container.innerHTML = '<div style="color:#888;">Sin items disponibles</div>';
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
                <button onclick="giveItemToPlayer('${item.item_id || item.instance_id}', '${item.meta.name}')" ...> Dar Item</button>
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

        // Mostrar panel correcto
        if (isDM) {
            document.getElementById('dm-panel').style.display = 'block';
        } else {
            document.getElementById('player-panel').style.display = 'block';
        }

        // Rellenar map-info con datos del socket
        document.getElementById('map-scene-name').textContent = d.current_scene.name;
        document.getElementById('map-grid-info').textContent =
            `Grid: ${TILE_SIZE}px · ${MAP_WIDTH / TILE_SIZE}×${MAP_HEIGHT / TILE_SIZE} tiles`;
        document.getElementById('map-info').style.display = 'block';

        mapImage = new Image();
        mapImage.onload = () => { initializeGame(); };
        mapImage.src = `/storage${d.current_scene.map_url}`;
    });


    socket.on('player_left', d => {
        console.log('👋 Jugador salió:', d);
        // TODO: Actualizar lista de jugadores/tokens
    });
    socket.on('item_equipped_toggled', d => {
        socket.emit("get_character_data", { character_id: myCharacterId, campaign_code: campaignCode })

    });
    socket.on('chat_message', data => {
        const el = document.createElement('div');
        el.className = 'chat-message';
        el.innerHTML = `<strong>${escapeHtml(data.sender)}:</strong> ${escapeHtml(data.text)}`;
        chatMessages.appendChild(el);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Si el chat está cerrado, incrementar contador
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

        // Actualizar posición visual
        token.style.left = `${d.x * TILE_SIZE + TILE_SIZE / 2}px`;
        token.style.top = `${d.y * TILE_SIZE + TILE_SIZE / 2}px`;

        // Actualizar grid state
        const oldX = parseInt(token.dataset.gridX || 0);
        const oldY = parseInt(token.dataset.gridY || 0);

        if (typeof updateGridState === 'function') {
            updateGridState(d.token_id, oldX, oldY, d.x, d.y);
        }

        // Actualizar dataset
        token.dataset.gridX = d.x;
        token.dataset.gridY = d.y;
    });

    socket.on('error', d => {
        console.error('❌ Error del servidor:', d);
    });

    socket.on('entities_result', data => {
        console.log("Entities data:", data);
        renderDMEntities(data);
    });

    socket.on("ac_result", (data) => {
        document.getElementById('char-ac').textContent = data.value || '--';

    });
    socket.on("enemy_created", (data) => {

        if (document.querySelector(`[data-token-id="${data.id}"]`)) return;

        const token = createTokenElement(data);
        document.getElementById("tokens-container").appendChild(token);

        updateGridState(data.id, null, null, data.x, data.y);
    });


    socket.on("tokens_sync", (tokens) => {

        document.querySelectorAll(".token").forEach(t => t.remove());
        initializeGrid();

        tokens.forEach(data => {
            const token = createTokenElement(data);
            document.getElementById("tokens-container").appendChild(token);
            updateGridState(data.id, null, null, data.x, data.y);
        });
    });
    socket.on("inventory_updated", d => {
        renderCharacterGearAndInventory(d)
    }
    )
    socket.on("character_data_received", c => {
        // Nombre en dorado
        const nameEl = document.getElementById('char-name');
        nameEl.textContent = c.name;
        nameEl.style.cssText = `
        font-family: 'Cinzel', serif;
        font-size: 3rem;
        font-weight: 700;
        color: #d4a853;
        text-shadow: 0 0 20px rgba(212,168,83,0.35);
        letter-spacing: 0.03em;
        margin-bottom: 4px;
    `;

        // Raza · Clase · Nivel
        document.getElementById('char-meta').innerHTML = `
        <div style="
            font-size: 1.2rem;
            color: #94a3b8;
            letter-spacing: 0.05em;
            margin-top: 4px;
            margin-bottom: 20px;
        ">
            <span style="color:#475569; font-weight:600">${c.race.name}</span>
            <span style="color:#475569; margin: 0 6px; font-weight:600; font-size:1rem">·</span>
            <span style="color:#475569; font-weight:600">${c.class.name}</span>
            <span style="color:#475569; margin: 0 6px; font-weight:600; font-size:1rem">·</span>
            <span style="color:#475569; font-weight:600">Nivel ${c.level}</span>
        </div>
    `;

        // HP
        document.getElementById('char-hp').textContent = `${c.hp.current} / ${c.hp.max}`;

        // Peso
        const currentWeight = c.current_weight ?? 0;
        const maxWeight = c.max_weight ?? 0;
        document.getElementById('char-weight').textContent = `${currentWeight} / ${maxWeight} lb`;

        const pct = maxWeight > 0 ? Math.min((currentWeight / maxWeight) * 100, 100) : 0;
        const bar = document.getElementById('weight-bar');
        bar.style.width = `${pct}%`;
        if (pct >= 90) {
            bar.style.background = 'linear-gradient(90deg, #7f1d1d, #ef4444)';
            bar.style.boxShadow = '0 0 6px rgba(239,68,68,0.5)';
        } else if (pct >= 60) {
            bar.style.background = 'linear-gradient(90deg, #78350f, #f59e0b)';
            bar.style.boxShadow = '0 0 6px rgba(245,158,11,0.5)';
        } else {
            bar.style.background = 'linear-gradient(90deg, #8a6830, #d4a853)';
            bar.style.boxShadow = '0 0 6px rgba(212,168,83,0.5)';
        }

        // AC (via socket)
        socket.emit("get_ac", { actor_id: myCharacterId });

        // Atributos
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

        // Habilidades
        const featuresList = document.getElementById('features-list');
        featuresList.innerHTML = '';
        c.features.forEach(f => {
            const li = document.createElement('li');
            li.className = 'feature-item';
            li.innerHTML = `
            <div class="feature-name">${f.name}</div>
            <div class="feature-name">${f.type}</div>
            <div class="feature-desc">${f.description}</div>
        `;
            featuresList.appendChild(li);
        });

        // Equipo
        renderCharacterGearAndInventory(c)
    });


    // Inicializar el resto de la UI
};
document.getElementById('item-search').addEventListener('input', e => {
    const filter = e.target.value.toLowerCase();
    document.querySelectorAll('#dm-item-list .item-card').forEach(card => {
        const name = card.querySelector('.feature-name').textContent.toLowerCase();
        const type = card.querySelector('.item-type-badge')?.textContent.toLowerCase() || '';
        card.style.display = name.includes(filter) || type.includes(filter) ? 'block' : 'none';
    });
});
function renderCharacterGearAndInventory(character) {
    // --- Render Gear ---
    const gearList = document.getElementById('gear-list');
    gearList.innerHTML = `
        <li class="feature-item">
            <div class="feature-name">Arma Principal</div>
            <div class="feature-desc">
                ${character.weapon?.name
            ? `<strong>${character.weapon.name}</strong>
                       <br>${character.weapon.dice_count}${character.weapon.dice_size}${character.weapon.bonus ? ` +${character.weapon.bonus}` : ''} ${character.weapon.damage_type}
                       ${character.weapon.equipped ? '<span class="equipped-badge">Equipado</span>' : ''}`
            : "Sin arma"}
            </div>
        </li>
        <li class="feature-item">
            <div class="feature-name">Armadura</div>
            <div class="feature-desc">
                ${character.armor?.name
            ? `<strong>${character.armor.name}</strong>
                       <br>AC: ${character.armor.base_ac} ${character.armor.dex_bonus ? `(DEX aplica)` : ''}
                       ${character.armor.stealth_disadvantage ? '<span class="stealth-badge">Desventaja Sigilo</span>' : ''}
                       ${character.armor.equipped ? '<span class="equipped-badge">Equipado</span>' : ''}`
            : "Sin armadura"}
            </div>
        </li>
        <li class="feature-item">
            <div class="feature-name">Escudo</div>
            <div class="feature-desc">
                ${character.shield?.name
            ? `<strong>${character.shield.name}</strong>
                       <br>AC Bonus: ${character.shield.ac_bonus}
                       ${character.shield.equipped ? '<span class="equipped-badge">Equipado</span>' : ''}`
            : "Sin escudo"}
            </div>
        </li>
    `;

    // --- Render Inventory ---
    const inventoryList = document.getElementById('inventory-list');
    inventoryList.innerHTML = '';
    if (character.inventory && character.inventory.length > 0) {
        character.inventory.forEach(item => {
            const type = item.meta.item_type?.toLowerCase();
            const isEquippable = ['weapon', 'armor', 'shield'].includes(type);
            const isConsumable = type === 'consumable';

            const li = document.createElement('li');
            li.className = 'feature-item item-card';
            li.dataset.itemId = item.item_id || item.id;
            li.innerHTML = `
                <div class="item-header">
                    <div class="feature-name">${item.meta.name}</div>
                    <div class="item-type-badge type-${type}">${item.meta.item_type}</div>
                </div>
                <div class="feature-desc">${item.meta.description}</div>
                <div class="item-meta">
                    <span>Cantidad: <strong>${item.quantity}</strong></span>
                    ${item.meta.weight ? `<span>Peso: <strong>${item.meta.weight} lb</strong></span>` : ''}
                    ${item.equipped ? `<span class="equipped-badge">Equipado</span>` : ''}
                </div>
                <div class="item-actions">
                    ${isConsumable ? `
                        <button class="item-btn btn-use"
                            onclick="handleItemAction('use', '${item.item_id}')">
                            ✨ Usar
                        </button>
                    ` : ''}
                    ${isEquippable ? `
                        <button class="item-btn ${item.equipped ? 'btn-unequip' : 'btn-equip'}"
                            onclick="handleItemAction('equip', '${item.item_id}')">
                            ${item.equipped ? ' Desequipar' : ' Equipar'}
                        </button>
                    ` : ''}
                    <button class="item-btn btn-drop"
                        onclick="handleItemAction('drop', '${item.item_id}')">
                         Tirar
                    </button>
                </div>
            `;
            inventoryList.appendChild(li);
        });
    } else {
        inventoryList.innerHTML = '<li class="feature-item">Sin objetos en el inventario.</li>';
    }
}
function createTokenElement(data) {
    const token = document.createElement("div");
    console.log("Creating token element with data:", data);
    token.className = `token ${data.type || ""}`;

    token.dataset.tokenId = data.id;
    token.dataset.name = data.name || "";
    token.dataset.hp = data.hp || 0;
    token.dataset.maxHp = data.max_hp || 0;
    token.dataset.ac = data.ac || 10;
    token.dataset.gridX = data.x;
    token.dataset.gridY = data.y;
    token.dataset.asset = data.asset || "";
    token.dataset.label = data.label || "";

    token.style.left = `${data.x * TILE_SIZE + TILE_SIZE / 2}px`;
    token.style.top = `${data.y * TILE_SIZE + TILE_SIZE / 2}px`;
    token.style.width = `${data.size[0] * TILE_SIZE}px`;
    token.style.height = `${data.size[1] * TILE_SIZE}px`;

    if (data.texture || data.asset) {
        token.innerHTML = `
            <img src="${data.texture || data.asset}" alt="${data.name}"
                 draggable="false"
                 style="width:100%; height:100%; object-fit:contain;">
        `;
    }

    if (data.label) {
        const label = document.createElement("div");
        label.className = "token-label";
        label.style.textAlign = "center";
        label.textContent = data.label;
        token.appendChild(label);
    }

    return token;
}

/* ================================
   MAPA CON PAN/ZOOM
================================ */
const mapViewport = document.getElementById('map-viewport');
const mapContainer = document.getElementById('map-container');
const mapCanvas = document.getElementById('map-canvas');
const mapCtx = mapCanvas.getContext('2d');
const gridCanvas = document.getElementById('grid-canvas');
const gridCtx = gridCanvas.getContext('2d');



// Estado de pan/zoom
let mapScale = 1;
let mapPanX = 0;
let mapPanY = 0;
let isPanning = false;
let panStartX = 0;
let panStartY = 0;
let showGridOverlay = true;

// Configurar tamaño de canvas


let GRID_COLS;
let GRID_ROWS;

/* ================================
   INICIALIZAR JUEGO
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

    if (!isDM && myCharacterId) {
        loadCharacter();
    }

    if (isDM) {
        socket.emit("get_entities", { campaign_code: campaignCode });
        initializeGrid();
        setupDMControls();
    }

    socket.emit("get_tokens", { campaign_code: campaignCode });
    hideLoader();
}


function renderMap() {
    // Dibujar SOLO la sección recortada
    mapCtx.drawImage(
        mapImage,
        current_section_offset_x,
        current_section_offset_y,
        MAP_WIDTH,
        MAP_HEIGHT,
        0,
        0,
        MAP_WIDTH,
        MAP_HEIGHT
    );

    // Dibujar grid
    if (showGridOverlay) {
        drawGrid();
    } else {
        gridCtx.clearRect(0, 0, MAP_WIDTH, MAP_HEIGHT);
    }
}

function drawGrid() {
    gridCtx.clearRect(0, 0, MAP_WIDTH, MAP_HEIGHT);
    gridCtx.strokeStyle = 'rgb(255, 255, 255)';
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
    const viewportWidth = mapViewport.clientWidth;
    const viewportHeight = mapViewport.clientHeight;

    // Si el mapa es más pequeño que el viewport, centrarlo
    if (MAP_WIDTH < viewportWidth) {
        mapPanX = (viewportWidth - MAP_WIDTH) / 2;
    }
    if (MAP_HEIGHT < viewportHeight) {
        mapPanY = (viewportHeight - MAP_HEIGHT) / 2;
    }

    updateMapTransform();
}

function resetMapView() {
    mapScale = 1;
    mapPanX = 0;
    mapPanY = 0;
    centerMap();
}

function toggleGrid() {
    showGridOverlay = !showGridOverlay;
    renderMap();
}

// Pan del mapa
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

// Zoom con rueda del mouse
mapViewport.addEventListener('wheel', e => {
    e.preventDefault();

    const rect = mapViewport.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
    const newScale = Math.max(0.5, Math.min(3, mapScale * zoomFactor));

    const worldX = (mouseX - mapPanX) / mapScale;
    const worldY = (mouseY - mapPanY) / mapScale;

    mapPanX = mouseX - worldX * newScale;
    mapPanY = mouseY - worldY * newScale;
    mapScale = newScale;

    updateMapTransform();
});

/* ================================
   CHAT COLAPSABLE
================================ */
let chatOpen = false;
let unreadMessages = 0;
const chatMessages = document.getElementById('chat-messages');

function openChat() {
    chatOpen = true;
    document.getElementById('chat-collapsed').style.display = 'none';
    document.getElementById('chat-expanded').style.display = 'block';
    document.getElementById('chat-input').focus();

    // Reset unread
    unreadMessages = 0;
    document.getElementById('chat-badge').style.display = 'none';
}

function closeChat() {
    chatOpen = false;
    document.getElementById('chat-collapsed').style.display = 'block';
    document.getElementById('chat-expanded').style.display = 'none';
}

// Atajo de teclado: T o Enter para abrir chat
document.addEventListener('keydown', e => {
    if (chatOpen) {
        if (e.key === 'Escape') {
            closeChat();
        }
    } else {
        if (e.key === 't' || e.key === 'T' || e.key === 'Enter') {
            // Solo si no estamos escribiendo en otro input
            if (document.activeElement.tagName !== 'INPUT' &&
                document.activeElement.tagName !== 'TEXTAREA') {
                e.preventDefault();
                openChat();
            }
        }
    }
});

// Cerrar chat al hacer click fuera
document.addEventListener('click', e => {
    if (!chatOpen) return;

    const chatWidget = document.querySelector('.chat-widget');
    const clickedInsideChat = chatWidget && chatWidget.contains(e.target);

    if (!clickedInsideChat) {
        closeChat();
    }
});

// Enviar mensaje
document.getElementById('chat-form').onsubmit = e => {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    if (!input.value.trim()) return;
    socket.emit('chat_message', {
        code: campaignCode,
        text: input.value
    });
    input.value = '';
};

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/* ================================
   TABS
================================ */
function openTab(name) {
    document.querySelectorAll('.tab').forEach(t => t.style.display = 'none');
    document.getElementById(`tab-${name}`).style.display = 'block';

    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`tab-btn-${name}`).classList.add('active');
}

/* ================================
   CARGAR PERSONAJE
================================ */
function loadCharacter() {
    // Pedir los datos del personaje
    socket.emit("get_character_data", {
        character_id: myCharacterId,
        campaign_code: campaignCode
    });
}

// Token Preview Functionality
const preview = document.getElementById('token-preview');

document.addEventListener('mouseover', e => {
    const token = e.target.closest('.token');

    if (!token) {
        preview.style.display = 'none';
        return;
    }

    // Obtener la posición del token en la pantalla
    const rect = token.getBoundingClientRect();

    // Posicionar el preview
    preview.style.display = 'block';
    preview.style.left = (rect.left + rect.width / 2) + 'px';
    preview.style.top = (rect.top - 10) + 'px';

    // Rellenar contenido del preview
    preview.innerHTML = `
        <div class="preview-name">${token.dataset.name}</div>
        <div class="preview-info">Nivel ${token.dataset.level} ${token.dataset.class}</div>
        <div class="preview-stats">
            <div><strong>❤️ ${token.dataset.hp}/${token.dataset.maxHp}</strong></div>
            <div>🛡️ <span class="ac-value">${token.dataset.ac}</span></div>
        </div>
    `;
});
function handleItemAction(action, itemId) {
    if (action === 'use') {
        socket.emit("save_and_exit", {
            campaign_code: campaignCode,
        });

    }
    else if (action === 'equip') {
        socket.emit("toggle_equip_item", {
            item_id: itemId,
            character_id: myCharacterId,
        });
    }
    else if (action === 'drop') {
        socket.emit("save_and_exit", {
            campaign_code: campaignCode,
        });
        console.log("Tirando objeto:", itemId);
    }
    else {
        console.warn("Acción desconocida:", action);
    }
}
document.addEventListener('mouseout', e => {
    const token = e.target.closest('.token');

    if (token) {
        preview.style.display = 'none';
    }
});

// Ocultar preview cuando el mouse sale del área del mapa
document.getElementById('map-viewport').addEventListener('mouseleave', () => {
    preview.style.display = 'none';
});

/* ================================
   GRID LÓGICO DEL MAPA
================================ */



// Grid lógico: null = vacío, objeto = token info
let gridState = [];

function initializeGrid() {
    // Crear matriz vacía
    gridState = [];
    for (let y = 0; y < GRID_ROWS; y++) {
        gridState[y] = [];
        for (let x = 0; x < GRID_COLS; x++) {
            gridState[y][x] = null;
        }
    }

    // Registrar posiciones iniciales de tokens
    document.querySelectorAll('.token').forEach(token => {
        const x = parseInt(token.dataset.gridX || 0);
        const y = parseInt(token.dataset.gridY || 0);

        if (isValidGridPosition(x, y)) {
            gridState[y][x] = {
                tokenId: token.dataset.tokenId,
                name: token.dataset.name
            };
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
    console.log(tokenId, oldX, oldY, newX, newY);
    // Limpiar posición anterior
    if (gridState[oldY] && gridState[oldY][oldX]) {
        gridState[oldY][oldX] = null;
    }
    // Ocupar nueva posición
    if (isValidGridPosition(newX, newY)) {
        const token = document.querySelector(`[data-token-id="${tokenId}"]`);
        gridState[newY][newX] = {
            tokenId: tokenId,
            name: token?.dataset.name || 'Unknown'
        };
    }

}
async function createEnemy() {
    const name = document.getElementById('enemy-name').value.trim();
    const hp = parseInt(document.getElementById('enemy-hp').value);
    const maxHp = parseInt(document.getElementById('enemy-max-hp').value);
    const attributes = {
        STR: parseInt(document.getElementById("enemy-str").value),
        DEX: parseInt(document.getElementById("enemy-dex").value),
        CON: parseInt(document.getElementById("enemy-con").value),
        INT: parseInt(document.getElementById("enemy-int").value),
        WIS: parseInt(document.getElementById("enemy-wis").value),
        CHA: parseInt(document.getElementById("enemy-cha").value),
    };

    const attacks = [{
        name: document.getElementById("attack-name").value,
        attack_bonus: parseInt(document.getElementById("attack-bonus").value),
        damage: document.getElementById("attack-damage").value,
        type: document.getElementById("attack-type").value
    }];
    const fileInput = document.getElementById('enemy-asset');
    const size = document.getElementById('enemy-size').value;
    const ac = parseInt(document.getElementById('enemy-ac').value) || 10;
    if (!name || !hp || !maxHp || !fileInput.files.length) {
        console.warn("Datos incompletos");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
        const uploadRes = await fetch("/api/enemies/upload", {
            method: "POST",
            body: formData
        });

        const uploadData = await uploadRes.json();

        if (!uploadData.success) {
            console.error("Upload falló");
            return;
        }

        size_map = size.split('x').map(Number);

        socket.emit("create_enemy", {
            campaign_code: campaignCode,
            name: name,
            hp: hp,
            ac: ac,
            max_hp: maxHp,
            asset: uploadData.asset_url,
            size: size_map,
            attributes: attributes,
            attacks: attacks
        });

        // Limpieza opcional de formulario
        document.getElementById('enemy-name').value = "";
        document.getElementById('enemy-hp').value = "";
        document.getElementById('enemy-max-hp').value = "";
        document.getElementById('enemy-asset').value = "";

    } catch (err) {
        console.error("Error en upload:", err);
    }
}

/* ================================
   DM TOKEN MOVE SYSTEM (MEJORADO)
================================ */

function renderDMEntities(data) {
    const playerList = document.getElementById('dm-player-list');
    const enemyList = document.getElementById('dm-enemy-list');

    // Render jugadores
    playerList.innerHTML = '';
    data.characters.forEach(char => {
        const hpPercent = Math.round((char.hp / char.max_hp) * 100);
        const hpColor = hpPercent > 50 ? '#4caf50' : hpPercent > 25 ? '#ff9800' : '#f44336';
        dm_player_list.push(char)
        const li = document.createElement('li');
        li.className = 'feature-item';
        li.dataset.charId = char.id; // ← añadir
        li.innerHTML = `
            <div class="entity-header">
                <span class="entity-name">${char.name}</span>
                <span class="entity-ac">🛡️ ${char.ac}</span>
            </div>
            <div class="entity-hp-bar-bg">
                <div class="entity-hp-bar" style="width:${hpPercent}%; background:${hpColor};"></div>
            </div>
            <div class="entity-hp-text">${char.hp} / ${char.max_hp} HP</div>
        `;
        playerList.appendChild(li);
    });

    if (data.characters.length === 0) {
        playerList.innerHTML = '<li class="feature-item" style="color:#888;">Sin jugadores conectados</li>';
    }

    // Render enemigos
    enemyList.innerHTML = '';
    data.enemies.forEach(enemy => {
        const hpPercent = Math.round((enemy.hp / enemy.max_hp) * 100);
        const hpColor = hpPercent > 50 ? '#4caf50' : hpPercent > 25 ? '#ff9800' : '#f44336';

        const li = document.createElement('li');
        li.className = 'feature-item';
        li.dataset.charId = char.id;
        li.innerHTML = `
            <div class="entity-header">
                <span class="entity-name">${enemy.name}</span>
                <span class="entity-ac">🛡️ ${enemy.ac}</span>
            </div>
            <div class="entity-hp-bar-bg">
                <div class="entity-hp-bar" style="width:${hpPercent}%; background:${hpColor};"></div>
            </div>
            <div class="entity-hp-text">${enemy.hp} / ${enemy.max_hp} HP</div>
        `;
        enemyList.appendChild(li);
    });

    if (data.enemies.length === 0) {
        enemyList.innerHTML = '<li class="feature-item" style="color:#888;">Sin enemigos creados</li>';
    }
}

function setupDMControls() {
    // Click en token → seleccionar
    document.addEventListener('click', (e) => {
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

    // Click en grid canvas → mover token
    gridCanvas.addEventListener('click', (e) => {
        if (!selectedToken) return;
        e.stopPropagation();

        const rect = gridCanvas.getBoundingClientRect();
        const tileX = Math.floor((e.clientX - rect.left) / (TILE_SIZE * mapScale));
        const tileY = Math.floor((e.clientY - rect.top) / (TILE_SIZE * mapScale));

        if (!isValidGridPosition(tileX, tileY) || isCellOccupied(tileX, tileY)) return;

        const oldX = parseInt(selectedToken.dataset.gridX || 0);
        const oldY = parseInt(selectedToken.dataset.gridY || 0);

        updateGridState(selectedToken.dataset.tokenId, oldX, oldY, tileX, tileY);
        selectedToken.dataset.gridX = tileX;
        selectedToken.dataset.gridY = tileY;

        socket.emit("move_token", {
            campaign_code: campaignCode,
            token_id: selectedToken.dataset.tokenId,
            x: tileX,
            y: tileY
        });

        selectedToken.classList.remove('selected');
        selectedToken = null;
    });

    // Igual para mapCanvas
    mapCanvas.addEventListener('click', (e) => {
        if (!selectedToken) return;
        e.stopPropagation();

        const rect = mapCanvas.getBoundingClientRect();
        const tileX = Math.floor((e.clientX - rect.left) / (TILE_SIZE * mapScale));
        const tileY = Math.floor((e.clientY - rect.top) / (TILE_SIZE * mapScale));

        if (!isValidGridPosition(tileX, tileY) || isCellOccupied(tileX, tileY)) return;

        const oldX = parseInt(selectedToken.dataset.gridX || 0);
        const oldY = parseInt(selectedToken.dataset.gridY || 0);

        updateGridState(selectedToken.dataset.tokenId, oldX, oldY, tileX, tileY);
        selectedToken.dataset.gridX = tileX;
        selectedToken.dataset.gridY = tileY;

        socket.emit("move_token", {
            campaign_code: campaignCode,
            token_id: selectedToken.dataset.tokenId,
            x: tileX,
            y: tileY
        });

        selectedToken.classList.remove('selected');
        selectedToken = null;
    });
}
// ================================
// LOADING SCREEN LOGIC
// ================================
const DD_QUOTES = [
    "\"Un d20 decide el destino de héroes y dioses por igual.\"",
    "\"El dungeon master no miente... solo improvisa la verdad.\"",
    "\"No es una trampa si el bardo consigue un 20 en Persuasión.\"",
    "\"Cada puerta cerrada es una oportunidad para el pícaro.\"",
    "\"El grupo decidió dividirse. El dungeon master sonrió.\"",
    "\"Un crítico en el peor momento posible... como siempre.\"",
    "\"¿Negociar con el dragón? El clérigo tiró un 3. Buena suerte.\"",
    "\"El mago dijo: 'Confíen en mí'. Nadie sobrevivió para arrepentirse.\"",
    "\"El mapa decía 'aquí hay monstruos'. El grupo fue de todas formas.\"",
    "\"Todo daño de fuego es culpa del hechicero. Sin excepciones.\"",
    "\"Los héroes descansan un momento... el dungeon no descansa nunca.\"",
    "\"El dado rueda. El destino espera. La taberna cierra pronto.\"",
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

    // Frase aleatoria inicial
    quoteEl.textContent = DD_QUOTES[Math.floor(Math.random() * DD_QUOTES.length)];

    // Rotar frases cada 3 s
    const quoteInterval = setInterval(() => {
        quoteEl.style.animation = 'none';
        quoteEl.offsetHeight; // reflow
        quoteEl.style.animation = '';
        quoteEl.textContent = DD_QUOTES[Math.floor(Math.random() * DD_QUOTES.length)];
    }, 3000);

    // Simular progreso
    let step = 0;
    const totalSteps = LOADING_STEPS.length;

    const progressInterval = setInterval(() => {
        step++;
        barEl.style.width = `${(step / totalSteps) * 100}%`;
        statusEl.textContent = LOADING_STEPS[step - 1];

        if (step >= totalSteps) {
            clearInterval(progressInterval);
            clearInterval(quoteInterval);
            setTimeout(hideLoadingScreen, 600);
        }
    }, 500);
})();

function hideLoadingScreen() {
    const screen = document.getElementById('loading-screen');
    screen.style.transition = 'opacity 0.8s ease';
    screen.style.opacity = '0';
    setTimeout(() => screen.remove(), 800);
}
function openDMTab(name) {
    // Añade dm-tab-items aquí:
    document.querySelectorAll('#dm-tab-map, #dm-tab-entities, #dm-tab-combat, #dm-tab-items')
        .forEach(t => t.style.display = 'none');

    document.getElementById(`dm-tab-${name}`).style.display = 'block';

    // Añade dm-tab-btn-items aquí:
    document.querySelectorAll('#dm-tab-btn-map, #dm-tab-btn-entities, #dm-tab-btn-combat, #dm-tab-btn-items')
        .forEach(b => b.classList.remove('active'));

    document.getElementById(`dm-tab-btn-${name}`).classList.add('active');

    if (name === 'items') {
        socket.emit('get_items');
    }
}
let _pendingGiveItemId = null;


function openGiveItemPopup(itemId, itemName) {
  _pendingGiveItemId = itemId;

  document.getElementById('give-item-name').textContent = `Objeto: ${itemName || itemId}`;

  const playerListEl = document.getElementById('give-item-player-list');
  playerListEl.innerHTML = '';

  if (dm_player_list.length === 0) {
    playerListEl.innerHTML = '<p style="color:#888; font-size:0.85rem;">Sin jugadores conectados.</p>';
  } else {
    dm_player_list.forEach(char => {
      const btn = document.createElement('button');
      btn.style.cssText = `
        background:#0d1117; border:1px solid #d4a853; color:#d4a853;
        padding:10px 14px; border-radius:8px; cursor:pointer;
        font-family:'Cinzel',serif; font-size:0.9rem; text-align:left;
        transition:background 0.2s; width:100%;
      `;
      btn.textContent = `🧙 ${char.name}`;
      btn.onmouseover = () => btn.style.background = '#1f1a0e';
      btn.onmouseout  = () => btn.style.background = '#0d1117';
      btn.onclick = () => confirmGiveItem(char.id, char.name);
      playerListEl.appendChild(btn);
    });
  }

  document.getElementById('give-item-overlay').style.display = 'flex';
}

function closeGiveItemPopup() {
  document.getElementById('give-item-overlay').style.display = 'none';
  _pendingGiveItemId = null;
}

function confirmGiveItem(targetCharId, targetName) {
  if (!_pendingGiveItemId || !targetCharId) return;

  socket.emit('dm_give_item', {
    campaign_code: campaignCode,
    item_instance_id: _pendingGiveItemId,
    target_player_id: targetCharId,
  });

    closeGiveItemPopup();
}

// Reemplaza la función anterior
function giveItemToPlayer(itemId, itemName) {
  openGiveItemPopup(itemId, itemName);
}