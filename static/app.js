// ==================== STATE & CONFIGURATION ====================

const config = {
    apiBase: '',
    refreshInterval: 30000 // 30 seconds
};

let appState = {
    currentSection: 'overview',
    symptoms: [],
    pollenData: [],
    modelReady: false
};

// ==================== UTILITY FUNCTIONS ====================

function showNotification(message, type = 'success') {
    const notif = document.getElementById('notification');
    notif.textContent = message;
    notif.className = `notification show ${type}`;
    
    setTimeout(() => {
        notif.classList.remove('show');
    }, 3000);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function formatDateTime(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ==================== API FUNCTIONS ====================

async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${config.apiBase}/api${endpoint}`, options);
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showNotification('Error: ' + error.message, 'error');
        return null;
    }
}

async function loadOverviewData() {
    const data = await apiCall('/dashboard/overview');
    if (data) {
        document.getElementById('today-symptoms').textContent = data.recent_symptoms_count;
        document.getElementById('avg-severity').textContent = 
            data.average_severity ? data.average_severity.toFixed(1) : '-';
        document.getElementById('data-points').textContent = data.pollen_records;
        
        await loadSymptomTrend();
    }
}

async function loadSymptomTrend() {
    const data = await apiCall('/symptoms/recent?days=7');
    if (data && data.symptoms.length > 0) {
        const symptoms = data.symptoms;
        
        // Group by date
        const byDate = {};
        symptoms.forEach(s => {
            const date = s.date;
            if (!byDate[date]) byDate[date] = [];
            byDate[date].push(s);
        });
        
        const dates = Object.keys(byDate).sort();
        const severities = dates.map(date => {
            const avgSev = byDate[date].reduce((sum, s) => sum + s.severity, 0) / byDate[date].length;
            return avgSev;
        });
        
        const trace = {
            x: dates.map(d => formatDate(d)),
            y: severities,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#2ecc71', width: 2 },
            marker: { size: 8, color: '#2ecc71' }
        };
        
        const layout = {
            title: '7-Day Symptom Trend',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Severity (0-3)', range: [0, 3] },
            margin: { t: 40, b: 40, l: 60, r: 40 }
        };
        
        Plotly.newPlot('symptom-trend-chart', [trace], layout, { responsive: true });
    }
}

async function loadTodayReports() {
    const data = await apiCall('/symptoms/today');
    const container = document.getElementById('today-reports');
    
    if (data && data.symptoms.length > 0) {
        container.innerHTML = data.symptoms.map(report => `
            <div class="report-item">
                <strong>${report.period.charAt(0).toUpperCase() + report.period.slice(1)}</strong>
                <p>Severity: ${report.severity}/3</p>
                <p>${report.notes || 'No notes'}</p>
            </div>
        `).join('');
    } else {
        container.innerHTML = '<p class="text-center">No reports logged yet today</p>';
    }
}

async function loadPollenData() {
    const data = await apiCall('/pollen/current?days=1');
    if (data) {
        appState.pollenData = data;
        renderPollenChart(data);
        renderPollenRecords(data);
    }
}

function renderPollenChart(pollenData) {
    if (!pollenData.dailyInfo || pollenData.dailyInfo.length === 0) return;
    
    // Define primary colors for pollen types
    const typeColors = {
        'TREE': '#2ecc71',    // Green
        'GRASS': '#3498db',   // Blue
        'WEED': '#e74c3c',    // Red
        'MOLD': '#f39c12'     // Orange
    };
    
    // Helper function to shade a hex color
    function shadeColor(color, percent) {
        const num = parseInt(color.replace("#", ""), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (G < 255 ? G < 1 ? 0 : G : 255))
            .toString(16).slice(1);
    }
    
    // Collect all family data across all days
    const familyMap = new Map(); // family name -> { type, values, dates }
    const dateSet = new Set();
    const typeMap = new Map(); // track which families belong to which type for coloring
    
    // Process all daily entries
    pollenData.dailyInfo.forEach(daily => {
        const dateInfo = daily.date;
        const dateStr = `${dateInfo.month}/${dateInfo.day}`;
        dateSet.add(dateStr);
        
        if (daily.plantInfo) {
            daily.plantInfo.forEach(plant => {
                if (plant.indexInfo && plant.indexInfo.value >= 0) {
                    const familyName = plant.displayName;
                    const plantType = plant.plantDescription?.type || 'UNKNOWN';
                    
                    if (!familyMap.has(familyName)) {
                        familyMap.set(familyName, {
                            type: plantType,
                            values: [],
                            dates: []
                        });
                    }
                    familyMap.get(familyName).values.push(plant.indexInfo.value);
                    familyMap.get(familyName).dates.push(dateStr);
                }
            });
        }
    });
    
    // Convert dates to sorted array
    const dates = Array.from(dateSet).sort();
    
    // Create traces for each family, grouped by type
    const traces = [];
    const typeTraceCounts = new Map();
    
    Array.from(familyMap.entries())
        .sort((a, b) => a[0].localeCompare(b[0]))
        .forEach(([familyName, data]) => {
            const type = data.type;
            
            if (!typeTraceCounts.has(type)) {
                typeTraceCounts.set(type, 0);
            }
            const traceCount = typeTraceCounts.get(type);
            typeTraceCounts.set(type, traceCount + 1);
            
            // Determine color shade for this family
            const baseColor = typeColors[type] || '#95a5a6';
            const shadePercent = (traceCount * 15) - 15; // Create shades: -15, 0, 15, 30...
            const familyColor = shadePercent === 0 ? baseColor : shadeColor(baseColor, shadePercent);
            
            // Build x and y arrays with dates aligned
            const yValues = dates.map(date => {
                const idx = data.dates.indexOf(date);
                return idx >= 0 ? data.values[idx] : null;
            });
            
            traces.push({
                x: dates,
                y: yValues,
                type: 'scatter',
                mode: 'lines+markers',
                name: `${familyName} (${type})`,
                line: {
                    color: familyColor,
                    width: 2
                },
                marker: {
                    size: 6,
                    color: familyColor
                },
                connectgaps: false
            });
        });
    
    // Fallback to pollen types if plant data isn't available
    if (traces.length === 0 && pollenData.dailyInfo[0].pollenTypeInfo) {
        const today = pollenData.dailyInfo[0];
        today.pollenTypeInfo
            .filter(p => p.indexInfo)
            .forEach((ptype, idx) => {
                const baseColor = typeColors[ptype.code] || '#95a5a6';
                traces.push({
                    x: [ptype.displayName],
                    y: [ptype.indexInfo.value],
                    type: 'scatter',
                    mode: 'markers',
                    name: ptype.displayName,
                    marker: {
                        size: 12,
                        color: baseColor
                    }
                });
            });
    }
    
    const layout = {
        title: 'Pollen Levels Over Time by Type & Family',
        xaxis: {
            title: dates.length > 1 ? 'Date' : 'Pollen Family',
            type: 'category'
        },
        yaxis: {
            title: 'Index Value (0 = None, 5 = Very High)',
            range: [0, 5]
        },
        hovermode: 'x unified',
        legend: {
            x: 1.05,
            y: 1,
            xanchor: 'left',
            yanchor: 'top'
        },
        margin: { t: 40, b: 60, l: 60, r: 200 },
        height: 500
    };
    
    Plotly.newPlot('pollen-chart', traces, layout, { responsive: true });
}

function renderPollenRecords(pollenData) {
    const container = document.getElementById('pollen-records');
    
    if (pollenData.dailyInfo && pollenData.dailyInfo.length > 0) {
        const dateInfo = pollenData.dailyInfo[0].date;
        const dateStr = `${dateInfo.year}-${String(dateInfo.month).padStart(2, '0')}-${String(dateInfo.day).padStart(2, '0')}`;
        
        const pollenTypes = pollenData.dailyInfo[0].pollenTypeInfo
            .filter(p => p.indexInfo)
            .map(p => `${p.displayName}: ${p.indexInfo.value}`)
            .join('<br>');
        
        container.innerHTML = `
            <div class="record-item">
                <strong>Date:</strong> ${formatDate(dateStr)}<br>
                <strong>Pollen Levels:</strong><br>${pollenTypes}
            </div>
        `;
    } else {
        container.innerHTML = '<p class="text-center">No pollen data available</p>';
    }
}

async function loadAnalysisData() {
    // Load model status
    const modelStatus = await apiCall('/model/status');
    if (modelStatus) {
        const statusDiv = document.getElementById('model-status');
        statusDiv.innerHTML = `
            <p>Model Status: <strong>${modelStatus.model_exists ? '✓ Ready' : '✗ Not Trained'}</strong></p>
            <p>Dataset Status: <strong>${modelStatus.dataset_exists ? '✓ Available' : '✗ Insufficient Data'}</strong></p>
        `;
        appState.modelReady = modelStatus.ready;
    }
    
    // Load quick stats
    const symptoms = await apiCall('/symptoms/recent?days=365');
    if (symptoms && symptoms.symptoms.length > 0) {
        const dates = [...new Set(symptoms.symptoms.map(s => s.date))];
        document.getElementById('total-reports').textContent = symptoms.symptoms.length;
        document.getElementById('date-range').textContent = 
            `${formatDate(dates[0])} to ${formatDate(dates[dates.length - 1])}`;
    }
    
    // Load allergen profile
    const profile = await apiCall('/allergen-profile');
    if (profile && Object.keys(profile.profile).length > 0) {
        const profileDiv = document.getElementById('allergen-profile');
        const profileHTML = Object.entries(profile.profile)
            .sort((a, b) => b[1].avg_severity - a[1].avg_severity)
            .map(([pollen, stats]) => `
                <div class="profile-item">
                    <strong>${pollen}</strong>
                    <p>Average Severity: ${stats.avg_severity.toFixed(1)}/3</p>
                    <p>Occurrences: ${stats.count}</p>
                </div>
            `).join('');
        profileDiv.innerHTML = profileHTML || '<p class="text-center">No allergen data available</p>';
    }
    
    // Load severity chart
    await loadSeverityChart();
}

async function loadSeverityChart() {
    const data = await apiCall('/symptoms/recent?days=30');
    if (data && data.symptoms.length > 0) {
        const symptoms = data.symptoms;
        const byDate = {};
        
        symptoms.forEach(s => {
            if (!byDate[s.date]) byDate[s.date] = [];
            byDate[s.date].push(s.severity);
        });
        
        const dates = Object.keys(byDate).sort();
        const avg = dates.map(d => 
            byDate[d].reduce((a, b) => a + b) / byDate[d].length
        );
        const min = dates.map(d => Math.min(...byDate[d]));
        const max = dates.map(d => Math.max(...byDate[d]));
        
        const trace1 = {
            x: dates.map(d => formatDate(d)),
            y: max,
            fill: 'tozeroy',
            name: 'Max',
            type: 'scatter',
            line: { color: '#e74c3c' }
        };
        
        const trace2 = {
            x: dates.map(d => formatDate(d)),
            y: avg,
            name: 'Average',
            type: 'scatter',
            line: { color: '#2ecc71', width: 2 }
        };
        
        const trace3 = {
            x: dates.map(d => formatDate(d)),
            y: min,
            fill: 'tonexty',
            name: 'Min',
            type: 'scatter',
            line: { color: '#3498db' }
        };
        
        const layout = {
            title: '30-Day Symptom Severity Range',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Severity (0-3)', range: [0, 3] },
            margin: { t: 40, b: 60, l: 60, r: 40 }
        };
        
        Plotly.newPlot('severity-chart', [trace1, trace2, trace3], layout, { responsive: true });
    }
}

// ==================== EVENT HANDLERS ====================

document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadOverviewData();
});

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            switchSection(this.dataset.section);
        });
    });
    
    // Symptom form
    document.getElementById('symptom-form').addEventListener('submit', handleSymptomSubmit);
    
    // Severity slider
    document.getElementById('severity').addEventListener('input', function() {
        document.getElementById('severity-display').textContent = this.value;
    });
    
    // Buttons
    document.getElementById('fetch-pollen-btn').addEventListener('click', handleFetchPollen);
    document.getElementById('train-model-btn').addEventListener('click', handleTrainModel);
    document.getElementById('export-data-btn').addEventListener('click', handleExportData);
    document.getElementById('clear-data-btn').addEventListener('click', handleClearData);
}

function switchSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Deactivate all buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(sectionName).classList.add('active');
    document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
    
    appState.currentSection = sectionName;
    
    // Load section-specific data
    if (sectionName === 'symptoms') {
        loadTodayReports();
    } else if (sectionName === 'pollen') {
        loadPollenData();
    } else if (sectionName === 'analysis') {
        loadAnalysisData();
    }
}

async function handleSymptomSubmit(e) {
    e.preventDefault();
    
    const severity = parseInt(document.getElementById('severity').value);
    const period = document.getElementById('period').value;
    const notes = document.getElementById('notes').value;
    const location = document.getElementById('location').value;
    
    const result = await apiCall('/symptoms/log', 'POST', {
        severity: severity,
        period: period,
        notes: notes,
        location: location || null
    });
    
    if (result && result.status === 'success') {
        showNotification('Symptom report submitted successfully!', 'success');
        document.getElementById('symptom-form').reset();
        document.getElementById('severity-display').textContent = '0';
        loadTodayReports();
        loadOverviewData();
    }
}

async function handleFetchPollen() {
    const btn = document.getElementById('fetch-pollen-btn');
    btn.disabled = true;
    btn.textContent = 'Fetching...';
    
    const result = await apiCall('/pollen/fetch', 'POST');
    
    btn.disabled = false;
    btn.textContent = 'Fetch Current Pollen Data';
    
    if (result && result.status === 'success') {
        showNotification('Pollen data fetched successfully!', 'success');
        loadPollenData();
    }
}

async function handleTrainModel() {
    const btn = document.getElementById('train-model-btn');
    btn.disabled = true;
    btn.textContent = 'Training...';
    
    const result = await apiCall('/model/train', 'POST');
    
    btn.disabled = false;
    btn.textContent = 'Train Model';
    
    if (result && result.status === 'success') {
        showNotification('Model trained successfully!', 'success');
        loadAnalysisData();
    }
}

async function handleExportData() {
    const data = await apiCall('/data/export');
    if (data) {
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pollen-tracker-export-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        showNotification('Data exported successfully!', 'success');
    }
}

function handleClearData() {
    if (confirm('Are you sure? This will delete all collected data. This cannot be undone.')) {
        // Would need backend endpoint for this
        showNotification('Data clearing not yet implemented', 'info');
    }
}

// Auto-refresh overview data
setInterval(() => {
    if (appState.currentSection === 'overview') {
        loadOverviewData();
    }
}, config.refreshInterval);
