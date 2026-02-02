// =======================
// Estado global
// =======================

let selectedRace = 'Human';
let selectedClass = 'Barbaro';

let racesCache = null;
let classesCache = null;

let radarChart = null;

// =======================
// Precarga de datos
// =======================

async function preloadData() {
    const [racesRes, classesRes] = await Promise.all([
        fetch("/api/races/all"),
        fetch("/api/classes/all")
    ]);

    racesCache = await racesRes.json();
    classesCache = await classesRes.json();
}

// =======================
// Race selection
// =======================

document.querySelectorAll('#race-grid .selection-option').forEach(option => {
    option.addEventListener('click', function () {
        document.querySelectorAll('#race-grid .selection-option').forEach(opt => opt.classList.remove('active'));
        this.classList.add('active');
        selectedRace = this.getAttribute('data-race');
        updateRaceInfo();
    });
});

// =======================
// Class selection
// =======================

document.querySelectorAll('#class-grid .selection-option').forEach(option => {
    option.addEventListener('click', function () {
        document.querySelectorAll('#class-grid .selection-option').forEach(opt => opt.classList.remove('active'));
        this.classList.add('active');
        selectedClass = this.getAttribute('data-class');
        updateClassInfo();
    });
});

// =======================
// Update race info with radar chart
// =======================

function updateRaceInfo() {
    const raceData = racesCache[selectedRace];
    if (!raceData) return;

    const raceInfoDiv = document.getElementById('race-info');

    raceInfoDiv.innerHTML = `
        <h3 class="race-name">${raceData.name}</h3>
        <p class="description">${raceData.description}</p>

        <div class="stats-container">
            <canvas id="radarChart" width="300" height="300"></canvas>
        </div>

        <div style="margin-top:30px;">
            <h4>Bonificaciones Raciales</h4>
            ${Object.entries(raceData.racial_bonus_stats).map(([k, v]) => `
                <div class="trait-item">
                    <div class="trait-title">${k}</div>
                    <div class="trait-description">+${v}</div>
                </div>
            `).join("")}
        </div>

        <div class="traits-list">
            <h4>Rasgos Raciales</h4>
            ${Object.entries(raceData.special_traits).map(([k, v]) => `
                <div class="trait-item">
                    <div class="trait-title">${k}</div>
                    <div class="trait-description">${v}</div>
                </div>
            `).join("")}
        </div>
    `;

    createRadarChart(raceData.base_attributes);
}

// =======================
// Create radar chart
// =======================

function createRadarChart(stats) {
    const ctx = document.getElementById('radarChart');

    if (radarChart) {
        radarChart.destroy();
    }

    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: Object.keys(stats),
            datasets: [{
                label: 'Atributos',
                data: Object.values(stats),
                backgroundColor: 'rgba(212, 175, 55, 0.2)',
                borderColor: 'rgba(212, 175, 55, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(212, 175, 55, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(212, 175, 55, 1)',
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            scales: {
                r: {
                    beginAtZero: true,
                    max: 16,
                    min: 0,
                    ticks: {
                        stepSize: 2,
                        color: 'rgba(244, 228, 193, 0.6)',
                        backdropColor: 'transparent',
                        font: { size: 11 }
                    },
                    grid: { color: 'rgba(212, 175, 55, 0.2)', circular: true },
                    angleLines: { color: 'rgba(212, 175, 55, 0.3)' },
                    pointLabels: {
                        color: 'rgba(212, 175, 55, 1)',
                        font: { size: 13, family: "'Cinzel', serif", weight: '600' }
                    }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(26, 20, 16, 0.95)',
                    titleColor: 'rgba(212, 175, 55, 1)',
                    bodyColor: 'rgba(244, 228, 193, 1)',
                    borderColor: 'rgba(212, 175, 55, 0.5)',
                    borderWidth: 1,
                    padding: 12,
                    titleFont: { family: "'Cinzel', serif", size: 14 },
                    bodyFont: { family: "'Lora', serif", size: 13 }
                }
            },
            maintainAspectRatio: true,
            responsive: true
        }
    });
}

// =======================
// Update class info
// =======================

function updateClassInfo() {
    const classData = classesCache[selectedClass];
    if (!classData) return;

    const classInfoDiv = document.getElementById('class-info');

    classInfoDiv.innerHTML = `
        <h3 class="class-name">${classData.name}</h3>
        <p class="description">${classData.description}</p>

        <div class="hit-die">Dado de Golpe: ${classData.hit_die}</div>

        <div class="class-features">
            ${Object.entries(classData.special_features).map(([level, features]) => `
                <div class="feature-level">
                    <div class="level-header">Nivel ${level}</div>
                    ${features.map(f => `
                        <div class="trait-item">
                            <div class="trait-title">${f.name}</div>
                            <div class="trait-description">${f.description}</div>
                        </div>
                    `).join("")}
                </div>
            `).join("")}
        </div>
    `;
}

// =======================
// Form submission
// =======================

document.getElementById("character-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("char-name").value.trim();

    if (!name || !selectedRace || !selectedClass) {
        alert("Datos incompletos");
        return;
    }

    const params = new URLSearchParams({
        name,
        race: selectedRace,
        class: selectedClass
    });

    const response = await fetch(`/api/character/create?${params.toString()}`, { method: "POST" });

    if (!response.ok) {
        throw new Error("Error al crear personaje");
    }

    const data = await response.json();

    // Obtener código de campaña de la query string
    const urlParams = new URLSearchParams(window.location.search);
    const campaignCode = urlParams.get('campaign');

    // Conectar al lobby pasando UUID (el nombre se cargará del backend)
    if (campaignCode) {
        window.location.href = `/lobby?campaign=${campaignCode}&uuid=${data.id}`;
    } else {
        // Fallback: mostrar la ficha
        window.location.href = `/card?uuid=${data.id}`;
    }
});


// =======================
// Load character
// =======================

document.getElementById("load-button").addEventListener("click", () => {
    const id = document.getElementById("load-id").value.trim();

    if (!id) {
        alert("UUID requerido");
        return;
    }

    window.location.href = `/card?uuid=${id}`;
});

// =======================
// Initialize
// =======================

(async function init() {
    await preloadData();
    updateRaceInfo();
    updateClassInfo();
})();
