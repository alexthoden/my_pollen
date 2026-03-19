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
    const response = await apiCall('/pollen/current?days=1');
    if (response && response.data) {
        // Extract the actual forecast data from the response wrapper
        appState.pollenData = response.data;
        renderPollenChart(response.data);
        renderPollenRecords(response.data);
    }
}

function renderPollenChart(pollenData) {
    if (!pollenData || !pollenData.dailyInfo || pollenData.dailyInfo.length === 0) {
        console.error('No valid pollen data for chart:', pollenData);
        // Display empty chart message
        const layout = {
            title: 'Pollen Levels Over Time',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Index Value' },
            annotations: [{
                text: 'No pollen data available',
                xref: 'paper',
                yref: 'paper',
                x: 0.5,
                y: 0.5,
                showarrow: false,
                font: { size: 20, color: '#999' }
            }]
        };
        Plotly.newPlot('pollen-chart', [], layout, { responsive: true, displayModeBar: false });
        return;
    }
    
    // Define robust color palettes for each pollen type (no whites, no transparency > 50%, max contrast)
    const typeColorPalettes = {
        'TREE': [
            'rgb(34, 139, 34)',      // Dark Green
            'rgb(25, 100, 25)',      // Very Dark Green
            'rgb(46, 125, 50)',      // Forest Green
            'rgb(56, 142, 60)',      // Medium Dark Green
            'rgb(27, 94, 32)',       // Deep Green
            'rgb(49, 127, 56)',      // Sage Green
            'rgb(77, 182, 77)',      // Strong Green (max 0.7 opacity)
            'rgb(56, 168, 56)',      // Vibrant Green (max 0.7 opacity)
        ],
        'GRASS': [
            'rgb(13, 71, 161)',      // Dark Blue
            'rgb(7, 57, 138)',       // Very Dark Blue
            'rgb(25, 103, 210)',     // Deep Blue
            'rgb(30, 136, 229)',     // Medium Dark Blue
            'rgb(13, 110, 253)',     // Strong Blue (max 0.7 opacity)
            'rgb(66, 133, 244)',     // Vibrant Blue (max 0.7 opacity)
            'rgb(0, 52, 102)',       // Navy Blue
            'rgb(18, 82, 180)',      // Royal Blue
        ],
        'WEED': [
            'rgb(183, 28, 28)',      // Dark Red
            'rgb(136, 14, 14)',      // Very Dark Red
            'rgb(194, 31, 31)',      // Deep Red
            'rgb(211, 47, 47)',      // Medium Dark Red
            'rgb(229, 57, 53)',      // Strong Red (max 0.7 opacity)
            'rgb(244, 67, 54)',      // Vibrant Red (max 0.7 opacity)
            'rgb(139, 0, 0)',        // Dark Crimson
            'rgb(178, 34, 34)',      // Firebrick Red
        ],
        'MOLD': [
            'rgb(191, 96, 1)',       // Dark Orange
            'rgb(153, 76, 0)',       // Very Dark Orange
            'rgb(230, 124, 12)',     // Deep Orange
            'rgb(245, 127, 23)',     // Medium Dark Orange
            'rgb(255, 152, 0)',      // Strong Orange (max 0.7 opacity)
            'rgb(255, 167, 38)',     // Vibrant Orange (max 0.7 opacity)
            'rgb(140, 70, 0)',       // Dark Brown
            'rgb(180, 90, 0)',       // Brown-Orange
        ],
        'FUNGAL': [
            'rgb(88, 19, 124)',      // Dark Purple
            'rgb(63, 12, 102)',      // Very Dark Purple
            'rgb(123, 31, 162)',     // Deep Purple
            'rgb(142, 36, 170)',     // Medium Dark Purple
            'rgb(171, 71, 188)',     // Strong Purple (max 0.7 opacity)
            'rgb(186, 104, 200)',    // Vibrant Purple (max 0.7 opacity)
        ]
    };
    
    // Collect all family data across all days
    const familyMap = new Map(); // family name -> { type, values, dates }
    const dateSet = new Set();
    
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
            const colorIndex = typeTraceCounts.get(type);
            typeTraceCounts.set(type, colorIndex + 1);
            
            // Get color for this family from the type's palette
            const palette = typeColorPalettes[type] || typeColorPalettes['WEED'];
            const familyColor = palette[colorIndex % palette.length];
            
            // Adjust opacity for lighter colors (some greens and oranges)
            let opacity = 0.85;
            if (familyColor.includes('rgb(77, 182, 77)') || 
                familyColor.includes('rgb(56, 168, 56)') ||
                familyColor.includes('rgb(13, 110, 253)') ||
                familyColor.includes('rgb(66, 133, 244)') ||
                familyColor.includes('rgb(229, 57, 53)') ||
                familyColor.includes('rgb(244, 67, 54)') ||
                familyColor.includes('rgb(255, 152, 0)') ||
                familyColor.includes('rgb(255, 167, 38)') ||
                familyColor.includes('rgb(171, 71, 188)') ||
                familyColor.includes('rgb(186, 104, 200)')) {
                opacity = 0.70; // Cap at 50% transparency (0.50 opacity + some buffer)
            }
            
            // Build x and y arrays with dates aligned
            const yValues = dates.map(date => {
                const idx = data.dates.indexOf(date);
                return idx >= 0 ? data.values[idx] : null;
            });
            
            // Convert rgb() to rgba() with opacity
            const rgbaColor = familyColor.replace('rgb(', 'rgba(').replace(')', `, ${opacity})`);
            
            traces.push({
                x: dates,
                y: yValues,
                type: 'scatter',
                mode: 'lines+markers',
                name: `${familyName} (${type})`,
                line: {
                    color: rgbaColor,
                    width: 2.5
                },
                marker: {
                    size: 7,
                    color: rgbaColor,
                    line: {
                        width: 0.5,
                        color: familyColor
                    }
                },
                connectgaps: false
            });
        });
    
    // Fallback to pollen types if plant data isn't available
    if (traces.length === 0 && pollenData.dailyInfo[0].pollenTypeInfo) {
        const today = pollenData.dailyInfo[0];
        const typeCounts = {};
        
        today.pollenTypeInfo
            .filter(p => p.indexInfo)
            .forEach((ptype) => {
                const type = ptype.code;
                if (!typeCounts[type]) typeCounts[type] = 0;
                
                const palette = typeColorPalettes[type] || typeColorPalettes['WEED'];
                const color = palette[typeCounts[type] % palette.length];
                typeCounts[type]++;
                
                const rgbaColor = color.replace('rgb(', 'rgba(').replace(')', ', 0.85)');
                
                traces.push({
                    x: [ptype.displayName],
                    y: [ptype.indexInfo.value],
                    type: 'scatter',
                    mode: 'markers',
                    name: ptype.displayName,
                    marker: {
                        size: 12,
                        color: rgbaColor,
                        line: {
                            width: 1,
                            color: color
                        }
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
            x: 1.02,
            y: 1,
            xanchor: 'left',
            yanchor: 'top',
            bgcolor: 'rgba(255, 255, 255, 0.8)',
            bordercolor: '#ccc',
            borderwidth: 1,
            font: { size: 11 }
        },
        margin: { t: 40, b: 60, l: 60, r: 280 },
        height: 500,
        plot_bgcolor: 'rgba(249, 249, 249, 0.5)',
        paper_bgcolor: 'white'
    };
    
    Plotly.newPlot('pollen-chart', traces, layout, { responsive: true, displayModeBar: false });
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
    // Initialize location autocomplete
    const locationList = document.getElementById('location-list');
    const locations = getAvailableLocations();
    locations.forEach(location => {
        const option = document.createElement('option');
        option.value = location;
        locationList.appendChild(option);
    });
    
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
    
    // Forecast button
    if (document.getElementById('load-forecast-btn')) {
        document.getElementById('load-forecast-btn').addEventListener('click', loadForecast);
    }
    
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
    } else if (sectionName === 'forecast') {
        // Forecast loads on button click, no auto-load
    } else if (sectionName === 'analysis') {
        loadAnalysisData();
    }
}

async function handleSymptomSubmit(e) {
    e.preventDefault();
    
    const severity = parseInt(document.getElementById('severity').value);
    const period = document.getElementById('period').value;
    const notes = document.getElementById('notes').value;
    let location = document.getElementById('location').value.trim();
    
    // Validate and format location
    if (location) {
        const coords = getLocationCoordinates(location);
        if (!coords) {
            showNotification(`Location "${location}" not recognized. Please select from the list.`, 'warning');
            return;
        }
        location = formatLocation(location); // Standardize format
    }
    
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
    
    // Get location and coordinates if available
    const locationInput = document.getElementById('location');
    const locationName = locationInput ? locationInput.value.trim() : '';
    let lat = 38.9072;  // Default: Washington DC
    let lng = -77.0369;
    
    if (locationName) {
        const coords = getLocationCoordinates(locationName);
        if (coords) {
            lat = coords.lat;
            lng = coords.lng;
            showNotification(`Fetching pollen data for ${locationName}...`, 'info');
        } else {
            showNotification(`Location "${locationName}" not found. Using default location.`, 'warning');
        }
    }
    
    const result = await apiCall('/pollen/fetch', 'POST', {
        lat: lat,
        lng: lng,
        days: 5,
        skip_if_exists: true
    });
    
    btn.disabled = false;
    btn.textContent = 'Fetch Current Pollen Data';
    
    if (result && result.status === 'success') {
        const message = result.skipped 
            ? 'Today\'s data already collected!' 
            : 'Pollen data fetched successfully!';
        showNotification(message, 'success');
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

// ==================== FORECAST FUNCTIONS ====================

async function loadForecast() {
    const btn = document.getElementById('load-forecast-btn');
    btn.disabled = true;
    btn.textContent = 'Loading...';
    
    try {
        const summary = await apiCall('/forecast/summary');
        const preps = await apiCall('/forecast/preparations');
        
        btn.disabled = false;
        btn.textContent = 'Load Forecast';
        
        if (summary && summary.status === 'success' && preps && preps.status === 'success') {
            displayForecast(summary.forecast, preps.preparations, preps.treatment_schedule);
            showNotification('Forecast loaded successfully!', 'success');
        } else {
            showNotification('Failed to load forecast data', 'error');
        }
    } catch (e) {
        btn.disabled = false;
        btn.textContent = 'Load Forecast';
        showNotification('Error loading forecast: ' + e.message, 'error');
    }
}

function displayForecast(forecast, preparations, schedule) {
    // Validate forecast data structure
    if (!forecast || !forecast.days || !Array.isArray(forecast.days)) {
        document.getElementById('forecast-empty').style.display = 'block';
        console.error('Invalid forecast data structure:', forecast);
        return;
    }
    
    // Hide empty message
    document.getElementById('forecast-empty').style.display = 'none';
    
    // Display critical days alert
    const criticalDays = (forecast.days || []).filter(d => d && d.severity >= 2);
    if (criticalDays.length > 0) {
        displayCriticalDays(criticalDays);
    }
    
    // Display preparation timeline
    if (preparations && Array.isArray(preparations.advance_prep)) {
        displayPreparations(preparations);
    }
    
    // Display daily forecasts with treatments
    displayDailyForecasts(forecast.days || []);
    
    // Display treatment schedule
    if (schedule && typeof schedule === 'object') {
        displayTreatmentSchedule(schedule);
    }
}

function displayCriticalDays(criticalDays) {
    const container = document.getElementById('critical-days-alert');
    const content = document.getElementById('critical-days-content');
    
    let html = '<ul style="margin: 10px 0;">';
    criticalDays.forEach(day => {
        const plants = Object.keys(day.risk_plants).join(', ');
        html += `<li><strong>${day.date}</strong> - ${day.severity_label} (${plants})</li>`;
    });
    html += '</ul>';
    html += `<p style="margin: 0; color: #666; font-size: 0.9em;">Plan ahead: Consider limiting outdoor activities on these days</p>`;
    
    content.innerHTML = html;
    container.style.display = 'block';
}

function displayPreparations(preparations) {
    const container = document.getElementById('prep-timeline');
    const content = document.getElementById('prep-content');
    
    if (preparations.advance_prep.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    let html = '<div style="display: flex; flex-direction: column; gap: 15px;">';
    
    preparations.advance_prep.forEach(prep => {
        html += `
            <div style="padding: 12px; background: #f9f9f9; border-left: 4px solid #3498db; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <strong style="color: #3498db;">🕐 ${prep.timing}</strong>
                    <span style="font-size: 0.9em; color: #666;">${prep.action}</span>
                </div>
                <p style="margin: 5px 0 0 0; font-size: 0.85em; color: #777;">${prep.reason}</p>
            </div>
        `;
    });
    
    html += '</div>';
    content.innerHTML = html;
    container.style.display = 'block';
}

function displayDailyForecasts(days) {
    const container = document.getElementById('daily-forecasts');
    
    let html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; margin-top: 10px;">';
    
    days.forEach(day => {
        const severityColor = getSeverityColor(day.severity);
        const treatments = day.treatments.medications;
        
        html += `
            <div class="card" style="border-top: 4px solid ${severityColor};">
                <h4 style="margin-top: 0; color: ${severityColor};">${day.date}</h4>
                <p style="margin: 5px 0;"><strong>Severity:</strong> <span style="color: ${severityColor}; font-weight: bold;">${day.severity_label.toUpperCase()}</span></p>
                <p style="margin: 5px 0;"><strong>High Risk:</strong> ${Object.keys(day.risk_plants).join(', ') || 'None'}</p>
                
                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;">
                    <p style="margin: 0 0 5px 0; font-size: 0.9em; font-weight: bold;">💊 Recommended Treatments:</p>
                    <ul style="margin: 5px 0; padding-left: 20px; font-size: 0.85em;">
                        ${treatments.slice(0, 3).map(med => `
                            <li style="margin-bottom: 3px;">
                                <strong>${med.name}</strong><br>
                                <span style="color: #666;">Dose: ${med.dosage} | ${med.timing}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
                
                <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #eee;">
                    <p style="margin: 0; font-size: 0.8em; color: #888;">\ud83c\udfed ${day.treatments.lifestyle.outdoor}</p>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
    container.style.display = 'block';
}

function displayTreatmentSchedule(schedule) {
    const container = document.getElementById('treatment-schedule');
    const content = document.getElementById('schedule-content');
    
    let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';
    
    Object.entries(schedule).forEach(([date, dayData]) => {
        html += `<div style="padding: 10px; background: #f5f5f5; border-radius: 4px;">`;
        html += `<h5 style="margin: 0 0 8px 0; color: #333;">${date} - <span style="color: ${getSeverityColor(dayData.severity)}; font-weight: bold;">${dayData.severity}</span></h5>`;
        
        Object.entries(dayData.schedule).forEach(([timing, medications]) => {
            html += `<div style="margin: 8px 0; padding-left: 10px; border-left: 2px solid #ddd;">`;
            html += `<p style="margin: 0 0 4px 0; font-weight: bold; font-size: 0.9em;">⏰ ${timing}:</p>`;
            html += '<ul style="margin: 0; padding-left: 20px; font-size: 0.85em;">';
            medications.forEach(med => {
                html += `
                    <li style="margin: 2px 0;">
                        <strong>${med.name}</strong> - ${med.dosage}
                        ${med.notes ? `<br><span style="color: #666; font-size: 0.9em;">${med.notes}</span>` : ''}
                    </li>
                `;
            });
            html += '</ul></div>';
        });
        
        html += '</div>';
    });
    
    html += '</div>';
    content.innerHTML = html;
    container.style.display = 'block';
}

function getSeverityColor(severity) {
    const colors = ['#27ae60', '#f39c12', '#e67e22', '#e74c3c'];
    return colors[Math.min(severity, 3)] || '#95a5a6';
}

// Auto-refresh overview data
setInterval(() => {
    if (appState.currentSection === 'overview') {
        loadOverviewData();
    }
}, config.refreshInterval);
