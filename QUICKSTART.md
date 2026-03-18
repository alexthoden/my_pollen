QUICK START GUIDE - Pollen Tracker
==================================

## 1. INITIAL SETUP (One Time)

### Windows:
```bash
# Double-click setup.bat or run in PowerShell:
.\setup.bat
```

### Linux/macOS:
```bash
chmod +x setup.sh
./setup.sh
```

## 2. CONFIGURE API KEY

1. Get your FREE Google Pollen API key:
   - Visit: https://developers.google.com/maps/documentation/pollen/overview
   - Click "Get Started" and follow the prompts
   - Create a new project or use existing one
   - Enable the Pollen API
   - Create an API key

2. Edit `.env` file:
   ```
   GOOGLE_POLLEN_API_KEY="your_actual_api_key_here"
   ```

3. Optional: Set your location in `.env`:
   ```
   POLLEN_LAT=40.7128
   POLLEN_LNG=-74.0060
   ```

## 3. RUN THE APPLICATION

### Option A: Web Dashboard Only
```bash
python main.py
# Then open: http://localhost:5000
```

### Option B: Web Dashboard + Desktop GUI
```bash
python main.py --gui
# Dashboard: http://localhost:5000
# Desktop GUI: Separate window
```

## 4. DAILY USAGE WORKFLOW

### Morning:
1. Open the app (web or GUI)
2. Go to "Symptom Log" section
3. Select "Morning"
4. Set severity (0-3)
5. Check experienced symptoms
6. Add any notes
7. Submit

### Afternoon:
- Repeat the same process but select "Afternoon"

### View Data:
- **Overview**: See trends and averages
- **Pollen Data**: View current pollen levels (can manually refresh)
- **Analysis**: See correlations between pollen and symptoms

## 5. BUILD YOUR MODEL (After ~1-2 weeks of data)

1. Collect at least 5-7 days of both pollen AND symptom data
2. Go to "Analysis" section
3. Click "Train Model"
4. Wait for training to complete
5. Once trained, the system will show predictions and allergen profile

## 6. USING THE DASHBOARD

### Components:

**Overview Tab:**
- See today's symptom reports
- View 7-day trend
- Quick statistics

**Symptom Log Tab:**
- Log symptoms for morning/afternoon
- See today's reports
- Adjust severity with slider
- Select multiple symptoms

**Pollen Data Tab:**
- View current pollen chart
- Manually fetch latest data
- See pollen by type

**Analysis Tab:**
- Model training status
- Your allergen profile
- 30-day severity trends
- Quick statistics

**Settings Tab:**
- Export data as JSON
- View app info
- Data management

## 7. KEYBOARD SHORTCUTS & TIPS

**Web Dashboard:**
- Press Tab to navigate between sections
- Charts are interactive (hover, zoom, pan)

**Desktop GUI:**
- Slider controls severity
- Checkboxes for multiple symptoms

## 8. DATA STORAGE

All your data is stored locally:
```
data/
  ├── my_pollen.json      # API responses
  ├── symptoms.json       # Your logged symptoms
  └── dataset.csv         # Training data
```

No data is sent to external servers except API requests to Google.

## 9. TROUBLESHOOTING

**"ModuleNotFoundError" on startup:**
```bash
pip install --upgrade -r requirements.txt
```

**Port 5000 already in use:**
Edit `main.py`, find `app.run()`, change to:
```python
app.run(debug=True, host="0.0.0.0", port=8000)
```

**GUI won't open:**
On Linux, install tkinter:
```bash
sudo apt-get install python3-tk
```

**Model won't train:**
- Ensure you have at least 3-5 days of data
- Make sure both pollen and symptom data exist
- Click "Fetch Pollen Data" first

**API key not working:**
- Check .env file is in the root directory
- Verify API key is valid and copied correctly
- Ensure Pollen API is enabled in Google Cloud Console

## 10. EXAMPLE WORKFLOW (First Week)

**Day 1-2:**
- Set up the app
- Start logging symptoms morning/afternoon
- Don't worry about model yet

**Day 3-5:**
- Continue logging daily
- Fetch pollen data
- Start noticing patterns

**Day 6-7:**
- Collect full week of data
- Go to Analysis → Train Model
- View your allergen profile
- Make predictions for next week

## 11. NEXT STEPS

After you've been using it:

1. **Export your data**: Settings → Export All Data
2. **Analyze patterns**: Look at Analysis tab for trends
3. **Adjust predictions**: The model learns from your reports
4. **Share insights**: Use exported data with your doctor

## 12. GETTING HELP

For common issues:
- Check the main README.md
- Review code comments in main.py
- Check .env setup

### API Endpoints (for advanced users):
- GET `/api/dashboard/overview` - Overall stats
- GET `/api/symptoms/today` - Today's symptoms
- POST `/api/symptoms/log` - Log new symptoms
- GET `/api/pollen/current` - Current pollen
- POST `/api/pollen/fetch` - Fetch pollen data
- POST `/api/model/train` - Train ML model

---
Happy tracking! Your personalized allergen profile will help you manage your allergies better.
