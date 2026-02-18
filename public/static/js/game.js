let socket;

/* ================================
   SOCKET.IO - CONEXIÓN
================================ */
window.onload = () => {
    socket = io();

    socket.on('connect', () => {
        console.log('✅ Socket conectado');
        socket.emit('join_campaign', { code: campaignCode });
        initializeGame();

    });

    socket.on('player_joined', d => {
        console.log('👋 Jugador se unió:', d);
        // TODO: Actualizar lista de jugadores/tokens
    });

    socket.on('player_left', d => {
        console.log('👋 Jugador salió:', d);
        // TODO: Actualizar lista de jugadores/tokens
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
        console.log("AC:", data.value);
        document.getElementById('char-ac').textContent = data.value || '--';

    });
    socket.on("enemy_created", (data) => {

        // Evitar duplicados
        if (document.querySelector(`[data-token-id="${data.id}"]`)) {
            return;
        }

        const token = document.createElement("div");
        token.className = "token enemy";

        token.dataset.tokenId = data.id;
        token.dataset.name = data.name;
        token.dataset.hp = data.hp;
        token.dataset.maxHp = data.max_hp;
        token.dataset.ac = data.ac || 10;
        token.dataset.gridX = data.x;
        token.dataset.gridY = data.y;

        // Posición centrada como usas en tu sistema
        token.style.left = `${data.x * TILE_SIZE + TILE_SIZE / 2}px`;
        token.style.top = `${data.y * TILE_SIZE + TILE_SIZE / 2}px`;
        token.style.width = `${data.size[0] * TILE_SIZE}px`;
        token.style.height = `${data.size[1] * TILE_SIZE}px`;

        token.innerHTML = `
        <img src="${data.asset}"
             draggable="false"
             style="width:100%; height:100%; object-fit:contain;">
    `;

        document.getElementById("tokens-container").appendChild(token);

        // Actualizar grid lógico
        if (typeof updateGridState === "function") {
            updateGridState(data.id, null, null, data.x, data.y);
        }

        // Si eres DM, refrescar lista
        if (isDM) {
            socket.emit("get_entities", { campaign_code: campaignCode });
        }

        console.log("🧟 Enemigo creado:", data.name);
    });


    // Inicializar el resto de la UI
};

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
mapCanvas.width = MAP_WIDTH;
mapCanvas.height = MAP_HEIGHT;
gridCanvas.width = MAP_WIDTH;
gridCanvas.height = MAP_HEIGHT;


/* ================================
   INICIALIZAR JUEGO
================================ */
function initializeGame() {
    renderMap();
    centerMap();

    if (!isDM) {
        loadCharacter();
    }

    // Inicializar grid después de un pequeño delay para que los tokens estén cargados
    if (isDM) {
        socket.emit("get_entities", { campaign_code: campaignCode });
        initializeGrid();
    }
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
    fetch(`/api/character/load?from_id=${myCharacterId}`)
        .then(r => r.json())
        .then(c => {
            console.log("Character data:", c);

            document.getElementById('char-name').textContent = c.name;
            document.getElementById('char-meta').textContent =
                `Nivel ${c.level} ${c.race.name} ${c.class.name}`;

            // HP y AC
            document.getElementById('char-hp').textContent =
                `${c.hp.current} / ${c.hp.max}`;


            // Atributos
            const STAT_MAP = {
                STR: 'STR',
                DEX: 'DEX',
                CON: 'CON',
                INT: 'INT',
                WIS: 'WIS',
                CHA: 'CHA'
            };

            const statsDiv = document.getElementById('stats');
            Object.entries(STAT_MAP).forEach(([abbr, key]) => {
                const value = c.attributes[key];
                const modifier = Math.floor((value - 10) / 2);
                const modStr = modifier >= 0 ? `+${modifier}` : modifier;

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
            socket.emit("get_ac", {
                actor_id: myCharacterId
            });
            console.log(ac)

            // Equipo (placeholder)
            const gearList = document.getElementById('gear-list');
            gearList.innerHTML = `
                        <li class="feature-item">
                            <div class="feature-name">Arma Principal</div>
                            <div class="feature-desc">${c.weapon || "Sin arma"}</div>
                        </li>
                        <li class="feature-item">
                            <div class="feature-name">Armadura</div>
                            <div class="feature-desc">${c.armor || "Sin armadura"}</div>
                        </li>
                        <li class="feature-item">
                            <div class="feature-name">Escudo</div>
                            <div class="feature-desc">${c.shield || "Sin escudo"}</div>
                        </li>
                    `;
        })
        .catch(err => console.error('Error loading character:', err));
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

// Calcular dimensiones del grid
const GRID_COLS = Math.floor(MAP_WIDTH / TILE_SIZE);
const GRID_ROWS = Math.floor(MAP_HEIGHT / TILE_SIZE);

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

        const li = document.createElement('li');
        li.className = 'feature-item';
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

if (isDM) {
    
    // Click en token → seleccionar
    document.addEventListener('click', (e) => {
        const token = e.target.closest('.token');

        if (token) {
            e.stopPropagation();

            // Quitar selección previa
            document.querySelectorAll('.token').forEach(t => {
                t.classList.remove('selected');
            });

            selectedToken = token;
            token.classList.add('selected');

            return;
        }

        // Si no clickeó un token, deseleccionar
        if (selectedToken && !e.target.closest('.token')) {
            selectedToken.classList.remove('selected');
            selectedToken = null;
        }
    });

    // Click en grid canvas → mover token
    gridCanvas.addEventListener('click', (e) => {
        if (!selectedToken) return;
        e.stopPropagation();

        // Obtener coordenadas CORRECTAS considerando scroll y zoom
        const rect = gridCanvas.getBoundingClientRect();

        // Posición del click en el viewport
        const viewportX = e.clientX - rect.left;
        const viewportY = e.clientY - rect.top;

        // Convertir a coordenadas del canvas (considerando zoom)
        // Como el canvas está dentro del container con transform, usamos la escala
        const canvasX = viewportX / mapScale;
        const canvasY = viewportY / mapScale;

        // Convertir a coordenadas de grid
        const tileX = Math.floor(canvasX / TILE_SIZE);
        const tileY = Math.floor(canvasY / TILE_SIZE);


        // Validar posición
        if (!isValidGridPosition(tileX, tileY)) {
            console.warn('❌ Posición fuera del grid');
            return;
        }

        if (isCellOccupied(tileX, tileY)) {
            const occupant = gridState[tileY][tileX];
            console.warn(`❌ Casilla ocupada por: ${occupant.name}`);
            return;
        }

        // Obtener posición anterior
        const oldX = parseInt(selectedToken.dataset.gridX || 0);
        const oldY = parseInt(selectedToken.dataset.gridY || 0);

        // Actualizar grid state
        updateGridState(selectedToken.dataset.tokenId, oldX, oldY, tileX, tileY);

        // Actualizar dataset del token
        selectedToken.dataset.gridX = tileX;
        selectedToken.dataset.gridY = tileY;

        // Emitir al servidor
        console.log(`Moviendo token ${selectedToken.dataset.id} a (${tileX}, ${tileY})`);
        console.log(selectedToken.dataset.tokenId)

        socket.emit("move_token", {
            campaign_code: campaignCode,
            token_id: selectedToken.dataset.tokenId,
            x: tileX,
            y: tileY
        });

        // Deseleccionar
        selectedToken.classList.remove('selected');
        selectedToken = null;
    });

    // También permitir click en mapCanvas (el fondo)
    mapCanvas.addEventListener('click', (e) => {
        if (!selectedToken) return;
        e.stopPropagation();

        const rect = mapCanvas.getBoundingClientRect();
        const viewportX = e.clientX - rect.left;
        const viewportY = e.clientY - rect.top;

        const canvasX = viewportX / mapScale;
        const canvasY = viewportY / mapScale;

        const tileX = Math.floor(canvasX / TILE_SIZE);
        const tileY = Math.floor(canvasY / TILE_SIZE);

        if (!isValidGridPosition(tileX, tileY) || isCellOccupied(tileX, tileY)) {
            return;
        }

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
function openDMTab(name) {
    document.querySelectorAll('#dm-tab-map, #dm-tab-entities, #dm-tab-combat')
        .forEach(t => t.style.display = 'none');

    document.getElementById(`dm-tab-${name}`).style.display = 'block';

    document.querySelectorAll('#dm-tab-btn-map, #dm-tab-btn-entities, #dm-tab-btn-combat')
        .forEach(b => b.classList.remove('active'));

    document.getElementById(`dm-tab-btn-${name}`).classList.add('active');
}
