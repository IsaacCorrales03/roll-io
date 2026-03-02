// =======================
// Global State
// =======================
let selectedSize = "1x1";
let radarChart = null;

// =======================
// Tab Switching (si necesitas tabs similares)
// =======================
function switchTab(tabName) {
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');
    document.getElementById(`tab-${tabName}`)?.classList.add('active');

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// =======================
// Attack Management
// =======================
function addAttack() {
    const container = document.getElementById('attacks-container');
    const attackId = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2);

    const attackDiv = document.createElement('div');
    attackDiv.className = 'attack-item';
    attackDiv.dataset.id = attackId;
    attackDiv.innerHTML = `
        <input type="text" class="attack-name" placeholder="Nombre del ataque" required>
        <input type="text" class="attack-damage" placeholder="Ej: 1d6+2" required>
        <input type="number" class="attack-bonus" placeholder="Attack bonus" value="0" required>
        <button type="button" onclick="removeAttack('${attackId}')">Eliminar</button>
    `;
    container.appendChild(attackDiv);
}

function removeAttack(id) {
    const div = document.querySelector(`.attack-item[data-id="${id}"]`);
    if (div) div.remove();
}

// Parse dice string "2d6+3" → {dice_count, dice_size, damage_bonus}
function parseDiceString(damageStr) {
    const match = damageStr.match(/(\d+)d(\d+)([+-]\d+)?/);
    if (!match) return null;
    return {
        dice_count: parseInt(match[1]),
        dice_size: parseInt(match[2]),
        damage_bonus: parseInt(match[3] || 0)
    };
}

function collectAttacks() {
    const attacks = [];
    document.querySelectorAll('.attack-item').forEach(div => {
        const name = div.querySelector('.attack-name').value.trim();
        const damageStr = div.querySelector('.attack-damage').value.trim();
        const attackBonus = parseInt(div.querySelector('.attack-bonus').value) || 0;
        const parsed = parseDiceString(damageStr);
        if (name && parsed) {
            attacks.push({
                name,
                dice_count: parsed.dice_count,
                dice_size: parsed.dice_size,
                damage_bonus: parsed.damage_bonus,
                attack_bonus: attackBonus,
                damage_type: "slashing"
            });
        }
    });
    return attacks;
}

// =======================
// Preview Image Upload
// =======================
let uploadedAssetUrl = null;
document.getElementById('enemy-asset')?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/enemies/upload", { method: "POST", body: formData });
        const data = await res.json();
        if (data.success) {
            uploadedAssetUrl = data.asset_url;
            // Mostrar preview
            let preview = document.getElementById('enemy-preview');
            if (!preview) {
                preview = document.createElement('img');
                preview.id = 'enemy-preview';
                preview.style.maxWidth = '200px';
                preview.style.marginTop = '12px';
                document.getElementById('enemy-asset').parentNode.appendChild(preview);
            }
            preview.src = uploadedAssetUrl;
        } else {
            alert("Error al subir la imagen");
        }
    } catch (err) {
        console.error("Error upload:", err);
    }
});

// =======================
// Enemy Creation
// =======================
async function createEnemy() {
    const name = document.getElementById('enemy-name').value.trim();
    const hp = parseInt(document.getElementById('enemy-hp').value);
    const maxHp = parseInt(document.getElementById('enemy-max-hp').value);
    const ac = parseInt(document.getElementById('enemy-ac').value) || 10;
    const sizeVal = document.getElementById('enemy-size').value;
    selectedSize = sizeVal;

    const attributes = {
        STR: parseInt(document.getElementById("enemy-str").value),
        DEX: parseInt(document.getElementById("enemy-dex").value),
        CON: parseInt(document.getElementById("enemy-con").value),
        INT: parseInt(document.getElementById("enemy-int").value),
        WIS: parseInt(document.getElementById("enemy-wis").value),
        CHA: parseInt(document.getElementById("enemy-cha").value),
    };

    const attacks = collectAttacks();

    if (!name || isNaN(hp) || isNaN(maxHp) || !uploadedAssetUrl || attacks.length === 0) {
        alert("Completa todos los campos y agrega al menos un ataque.");
        return;
    }

    const payload = {
        name,
        hp,
        max_hp: maxHp,
        ac,
        size: sizeVal,
        attributes,
        attacks,
        asset_url: uploadedAssetUrl
    };

    try {
        const res = await fetch("/api/enemies/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || "Error al crear enemigo");
        }

        const data = await res.json();
        alert(`Enemigo creado con éxito: ${data.id}`);

        // Reset form
        document.getElementById('enemy-name').value = "";
        document.getElementById('enemy-hp').value = "";
        document.getElementById('enemy-max-hp').value = "";
        document.getElementById('enemy-ac').value = "";
        document.getElementById('enemy-asset').value = "";
        document.getElementById('attacks-container').innerHTML = "";
        uploadedAssetUrl = null;
        const preview = document.getElementById('enemy-preview');
        if (preview) preview.remove();

    } catch (error) {
        console.error("Error:", error);
        alert(error.message || "Error al crear enemigo");
    }
}

// =======================
// Event Listeners
// =======================
document.getElementById("create-enemy-btn")?.addEventListener("click", createEnemy);

// Inicializar primer ataque por defecto
addAttack();