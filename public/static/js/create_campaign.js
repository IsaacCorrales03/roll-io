/* ================================
   VARIABLES GLOBALES
================================ */
const canvas = document.getElementById("map-canvas");
const ctx = canvas.getContext("2d");
const container = document.getElementById("canvas-container");
const fileInput = document.getElementById("map-upload");

let image = new Image();
let selectedFile = null;

// Estado del canvas
let offsetX = 0;
let offsetY = 0;
let scale = 1;

// Selección
let selecting = false;
let selectionStart = { x: 0, y: 0 };
let selection = null;

// Pan
let panning = false;
let panStart = { x: 0, y: 0 };
let panOffset = { x: 0, y: 0 };

// Configuración
let showGrid = true;
let mode = 'select'; // 'select' | 'pan'

/* ================================
   CARGA DE IMAGEN
================================ */
fileInput.addEventListener("change", function(e) {
    const file = e.target.files[0];
    if (!file) return;

    selectedFile = file;

    const reader = new FileReader();
    reader.onload = function(evt) {
        image.src = evt.target.result;
    };
    reader.readAsDataURL(file);
});

image.onload = function() {
    // Ajustar canvas al contenedor
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;

    // Centrar imagen
    const scaleX = canvas.width / image.width;
    const scaleY = canvas.height / image.height;
    scale = Math.min(scaleX, scaleY, 1) * 0.9;

    panOffset.x = (canvas.width - image.width * scale) / 2;
    panOffset.y = (canvas.height - image.height * scale) / 2;

    draw();
};

/* ================================
   MODOS DE INTERACCIÓN
================================ */
function setMode(newMode) {
    mode = newMode;
    document.getElementById('pan-btn').classList.toggle('active', mode === 'pan');
    document.getElementById('select-btn').classList.toggle('active', mode === 'select');
    container.classList.toggle('selecting', mode === 'select');
}

function toggleGrid() {
    showGrid = !showGrid;
    draw();
}

function resetView() {
    if (!image.src) return;
    
    const scaleX = canvas.width / image.width;
    const scaleY = canvas.height / image.height;
    scale = Math.min(scaleX, scaleY, 1) * 0.9;

    panOffset.x = (canvas.width - image.width * scale) / 2;
    panOffset.y = (canvas.height - image.height * scale) / 2;

    selection = null;
    draw();
}

/* ================================
   MOUSE EVENTS
================================ */
canvas.addEventListener("mousedown", e => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    if (mode === 'pan') {
        panning = true;
        panStart = { x: mouseX - panOffset.x, y: mouseY - panOffset.y };
        container.classList.add('panning');
    } else if (mode === 'select') {
        selecting = true;
        // Convertir a coordenadas de imagen
        selectionStart = screenToImage(mouseX, mouseY);
    }
});

canvas.addEventListener("mousemove", e => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    if (panning) {
        panOffset.x = mouseX - panStart.x;
        panOffset.y = mouseY - panStart.y;
        draw();
    } else if (selecting) {
        const current = screenToImage(mouseX, mouseY);
        
        selection = {
            x: Math.min(selectionStart.x, current.x),
            y: Math.min(selectionStart.y, current.y),
            width: Math.abs(current.x - selectionStart.x),
            height: Math.abs(current.y - selectionStart.y)
        };

        draw();
        updateSelectionInfo();
    }
});

canvas.addEventListener("mouseup", () => {
    panning = false;
    selecting = false;
    container.classList.remove('panning');
});

canvas.addEventListener("mouseleave", () => {
    panning = false;
    selecting = false;
    container.classList.remove('panning');
});

// Zoom con rueda del mouse
canvas.addEventListener("wheel", e => {
    e.preventDefault();
    
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
    const newScale = Math.max(0.1, Math.min(5, scale * zoomFactor));

    // Zoom hacia el mouse
    const worldX = (mouseX - panOffset.x) / scale;
    const worldY = (mouseY - panOffset.y) / scale;

    panOffset.x = mouseX - worldX * newScale;
    panOffset.y = mouseY - worldY * newScale;

    scale = newScale;
    draw();
});

/* ================================
   CONVERSIÓN DE COORDENADAS
================================ */
function screenToImage(screenX, screenY) {
    return {
        x: Math.round((screenX - panOffset.x) / scale),
        y: Math.round((screenY - panOffset.y) / scale)
    };
}

function imageToScreen(imageX, imageY) {
    return {
        x: imageX * scale + panOffset.x,
        y: imageY * scale + panOffset.y
    };
}

/* ================================
   RENDERIZADO
================================ */
function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!image.src) {
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#94a3b8';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Sube un mapa para empezar', canvas.width / 2, canvas.height / 2);
        return;
    }

    // Dibujar imagen
    ctx.save();
    ctx.translate(panOffset.x, panOffset.y);
    ctx.scale(scale, scale);
    ctx.drawImage(image, 0, 0);
    ctx.restore();

    // Dibujar grid
    if (showGrid) {
        drawGrid();
    }

    // Dibujar selección
    if (selection) {
        const screenPos = imageToScreen(selection.x, selection.y);
        const width = selection.width * scale;
        const height = selection.height * scale;

        ctx.strokeStyle = '#a78bfa';
        ctx.lineWidth = 3;
        ctx.strokeRect(screenPos.x, screenPos.y, width, height);

        ctx.fillStyle = 'rgba(167, 139, 250, 0.1)';
        ctx.fillRect(screenPos.x, screenPos.y, width, height);

        // Esquinas
        const cornerSize = 8;
        ctx.fillStyle = '#a78bfa';
        ctx.fillRect(screenPos.x - cornerSize/2, screenPos.y - cornerSize/2, cornerSize, cornerSize);
        ctx.fillRect(screenPos.x + width - cornerSize/2, screenPos.y - cornerSize/2, cornerSize, cornerSize);
        ctx.fillRect(screenPos.x - cornerSize/2, screenPos.y + height - cornerSize/2, cornerSize, cornerSize);
        ctx.fillRect(screenPos.x + width - cornerSize/2, screenPos.y + height - cornerSize/2, cornerSize, cornerSize);
    }
}

function drawGrid() {
    const tileSize = parseInt(document.getElementById('tile-size').value) || 64;
    
    ctx.save();
    ctx.translate(panOffset.x, panOffset.y);
    ctx.scale(scale, scale);

    ctx.strokeStyle = 'rgba(167, 139, 250, 0.2)';
    ctx.lineWidth = 1 / scale;

    // Líneas verticales
    for (let x = 0; x < image.width; x += tileSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, image.height);
        ctx.stroke();
    }

    // Líneas horizontales
    for (let y = 0; y < image.height; y += tileSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(image.width, y);
        ctx.stroke();
    }

    ctx.restore();
}

function updateSelectionInfo() {
    const tileSize = parseInt(document.getElementById('tile-size').value) || 64;
    const tilesX = Math.floor(selection.width / tileSize);
    const tilesY = Math.floor(selection.height / tileSize);
    
    document.getElementById('selection-info').textContent = 
        `Área: ${selection.width}×${selection.height}px (${tilesX}×${tilesY} tiles)`;
}

/* ================================
   CREAR CAMPAÑA
================================ */
async function createCampaign() {
    if (!selectedFile) {
        alert("❌ Debes subir un mapa");
        return;
    }

    if (!selection) {
        alert("❌ Debes seleccionar una sección del mapa");
        return;
    }

    const campaignName = document.getElementById("campaign-name").value;
    const worldName = document.getElementById("world-name").value;
    const sceneName = document.getElementById("scene-name").value;

    if (!campaignName || !worldName || !sceneName) {
        alert("❌ Completa todos los campos obligatorios");
        return;
    }

    const formData = new FormData();
    formData.append("campaign_name", campaignName);
    formData.append("world_name", worldName);
    formData.append("world_lore", document.getElementById("world-lore").value);
    formData.append("scene_name", sceneName);
    formData.append("tile_size", parseInt(document.getElementById("tile-size").value));
    formData.append("offset_x", Math.round(selection.x));
    formData.append("offset_y", Math.round(selection.y));
    formData.append("width_px", Math.round(selection.width));
    formData.append("height_px", Math.round(selection.height));
    formData.append("map_file", selectedFile);

    try {
        const res = await fetch("/api/campaigns/create_full", {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        if (res.ok) {
            window.location.href = "/campaign/" + data.id;
        } else {
            alert("❌ Error: " + (data.error || "Error interno"));
        }
    } catch (err) {
        alert("❌ Error de conexión: " + err.message);
    }
}

// Ajustar canvas al redimensionar ventana
window.addEventListener('resize', () => {
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    draw();
});
