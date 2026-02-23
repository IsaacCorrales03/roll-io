// =======================
// Global State
// =======================
let selectedRace = 'Human';
let selectedClass = 'Barbaro';
let racesCache = null;
let classesCache = null;
let radarChart = null;
let selectedSkills = [];   // ← declarado aquí, no al final

// =======================
// Tab Switching
// =======================
function switchTab(tabName) {
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// =======================
// Preload Data from API
// =======================
async function preloadData() {
    try {
        const [racesRes, classesRes] = await Promise.all([
            fetch("/api/races/all"),
            fetch("/api/classes/all")
        ]);

        racesCache = await racesRes.json();
        classesCache = await classesRes.json();

        // Populate race grid
        const raceGrid = document.getElementById('race-grid');
        raceGrid.innerHTML = Object.keys(racesCache).map((raceKey, index) => `
            <button type="button" class="selection-option ${index === 0 ? 'active' : ''}" data-race="${raceKey}">
                ${racesCache[raceKey].name}
            </button>
        `).join('');

        // Set initial selectedRace to the first key
        const raceKeys = Object.keys(racesCache);
        if (raceKeys.length > 0) {
            selectedRace = raceKeys[0];
        }

        // Populate class grid
        const classGrid = document.getElementById('class-grid');
        classGrid.innerHTML = Object.keys(classesCache).map((classKey, index) => `
            <button type="button" class="selection-option ${index === 0 ? 'active' : ''}" data-class="${classKey}">
                ${classesCache[classKey].name}
            </button>
        `).join('');

        // Set initial selectedClass to the first key
        const classKeys = Object.keys(classesCache);
        if (classKeys.length > 0) {
            selectedClass = classKeys[0];
        }

        // Event listeners — races
        document.querySelectorAll('#race-grid .selection-option').forEach(option => {
            option.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelectorAll('#race-grid .selection-option').forEach(opt => opt.classList.remove('active'));
                this.classList.add('active');
                selectedRace = this.getAttribute('data-race');
                updateRaceInfo();
            });
        });

        // Event listeners — classes
        document.querySelectorAll('#class-grid .selection-option').forEach(option => {
            option.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelectorAll('#class-grid .selection-option').forEach(opt => opt.classList.remove('active'));
                this.classList.add('active');
                selectedClass = this.getAttribute('data-class');
                updateClassInfo();
            });
        });

    } catch (error) {
        console.error("Error loading data:", error);
    }
}

// =======================
// Update Race Info
// =======================
function updateRaceInfo() {
    const raceData = racesCache[selectedRace];
    if (!raceData) return;

    // Column 2: Name, Description, Chart
    const raceInfoMain = document.getElementById('race-info-main');
    raceInfoMain.innerHTML = `
        <h3 class="race-name">${raceData.name}</h3>
        <p class="description">${raceData.description}</p>
        <div class="stats-container">
            <canvas id="radarChart" width="280" height="280"></canvas>
        </div>
    `;

    // Column 3: Bonuses & Traits
    const raceInfoDetails = document.getElementById('race-info-details');
    raceInfoDetails.innerHTML = `
        <div>
            <h4 class="text-lg font-bold text-amber-400 mb-3">Bonificaciones Raciales</h4>
            ${Object.entries(raceData.racial_bonus_stats).map(([k, v]) => `
                <div class="trait-item">
                    <div class="trait-title">${k}</div>
                    <div class="trait-description">+${v}</div>
                </div>
            `).join("")}
        </div>
        <div class="traits-list mt-6">
            <h4 class="text-lg font-bold text-amber-400 mb-3">Rasgos Raciales</h4>
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
// Create Radar Chart
// =======================
function createRadarChart(stats) {
    const ctx = document.getElementById('radarChart');
    if (!ctx) return;

    if (radarChart) {
        radarChart.destroy();
        radarChart = null;
    }

    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: Object.keys(stats),
            datasets: [{
                label: 'Atributos',
                data: Object.values(stats),
                backgroundColor: 'rgba(251, 191, 36, 0.2)',
                borderColor: 'rgba(251, 191, 36, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(251, 191, 36, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(251, 191, 36, 1)',
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
                        color: 'rgba(203, 213, 225, 0.6)',
                        backdropColor: 'transparent',
                        font: { size: 11 }
                    },
                    grid: { color: 'rgba(251, 191, 36, 0.2)', circular: true },
                    angleLines: { color: 'rgba(251, 191, 36, 0.3)' },
                    pointLabels: {
                        color: 'rgba(251, 191, 36, 1)',
                        font: { size: 13, family: "'Cinzel', serif", weight: '600' }
                    }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(30, 41, 59, 0.95)',
                    titleColor: 'rgba(251, 191, 36, 1)',
                    bodyColor: 'rgba(203, 213, 225, 1)',
                    borderColor: 'rgba(251, 191, 36, 0.5)',
                    borderWidth: 1,
                    padding: 12,
                    titleFont: { family: "'Cinzel', serif", size: 14 },
                    bodyFont: { family: "'Inter', sans-serif", size: 13 }
                }
            },
            maintainAspectRatio: true,
            responsive: true
        }
    });
}

// =======================
// Update Class Info
// =======================
function updateClassInfo() {
    const classData = classesCache[selectedClass];
    if (!classData) return;

    const classInfoDiv = document.getElementById('class-info');

    classInfoDiv.innerHTML = `
        <h3 class="text-xl font-bold text-white mb-4 flex items-center gap-3 sticky top-0 bg-slate-900/95 backdrop-blur-sm pb-4 -mt-2 pt-4 z-10 rounded-lg">
            <div class="w-8 h-8 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-lg flex items-center justify-center border border-purple-500/20">
                <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
            </div>
            Información de Clase
        </h3>
        <div class="mt-4">
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
        </div>
    `;

    // Reset skills
    selectedSkills = [];
    const skillContainer = document.getElementById("skill-selection-container");

    if (classData.skill_choices_count > 0 && classData.skill_choices.length > 0) {
        skillContainer.innerHTML = `
            <div class="skill-section">
                <h4>Competencias de Habilidad</h4>
                <p>Selecciona ${classData.skill_choices_count} habilidad${classData.skill_choices_count > 1 ? 'es' : ''}</p>
                <div id="skill-options">
                    ${classData.skill_choices.map(skill => `
                        <label class="skill-option">
                            <input type="checkbox" value="${skill}">
                            ${skill}
                        </label>
                    `).join("")}
                </div>
            </div>
        `;

        skillContainer.querySelectorAll("input[type=checkbox]").forEach(box => {
            box.addEventListener("change", function () {
                if (this.checked) {
                    if (selectedSkills.length >= classData.skill_choices_count) {
                        this.checked = false;
                        return;
                    }
                    selectedSkills.push(this.value);
                } else {
                    selectedSkills = selectedSkills.filter(s => s !== this.value);
                }
            });
        });

    } else {
        skillContainer.innerHTML = "";
    }
}

// =======================
// Form Submission
// =======================
document.getElementById("create-character-btn").addEventListener("click", async (e) => {
    e.preventDefault();

    const name = document.getElementById("char-name").value.trim();

    if (!name) {
        alert("Por favor ingresa un nombre para tu héroe");
        return;
    }

    if (!selectedRace || !selectedClass) {
        alert("Por favor selecciona una raza y una clase");
        return;
    }

    // Validate skill count if required
    const classData = classesCache[selectedClass];
    if (classData && classData.skill_choices_count > 0) {
        if (selectedSkills.length !== classData.skill_choices_count) {
            alert(`Debes seleccionar exactamente ${classData.skill_choices_count} habilidad${classData.skill_choices_count > 1 ? 'es' : ''}`);
            switchTab('clase');
            return;
        }
    }

    try {
        const response = await fetch(`/api/character/create`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name,
                race: selectedRace,
                class: selectedClass,
                skills: selectedSkills   // ← incluido en el body
            })
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error || "Error al crear personaje");
        }

        const data = await response.json();

        const urlParams = new URLSearchParams(window.location.search);
        const campaignCode = urlParams.get('campaign');

        if (campaignCode) {
            window.location.href = `/lobby?campaign=${campaignCode}&uuid=${data.id}`;
        } else {
            window.location.href = `/dashboard`;
        }

    } catch (error) {
        console.error("Error:", error);
        alert(error.message || "Error al crear el personaje. Por favor intenta de nuevo.");
    }
});

// =======================
// Load Character
// =======================
document.getElementById("load-button").addEventListener("click", () => {
    const id = document.getElementById("load-id").value.trim();

    if (!id) {
        alert("Por favor ingresa un UUID válido");
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