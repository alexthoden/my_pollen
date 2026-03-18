import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from src.collect_pollen import get_pollen_forecast
from src.collect_symptoms import log_symptoms, get_symptoms_for_date
from src.predict import predict_symptoms, get_allergen_risk_factors
import threading
import json

class PollenTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pollen Tracker - Symptom Logger")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        self.lat = 38.9072  # Default to Washington DC
        self.lng = -77.0369
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI layout."""
        # Title
        title = tk.Label(
            self.root,
            text="Pollen Tracker - Daily Symptom Logger",
            font=("Helvetica", 16, "bold"),
            bg="#e8f5e9",
            pady=10
        )
        title.pack(fill=tk.X)
        
        # Main frame with scrolling
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Today's Date
        date_frame = ttk.LabelFrame(main_frame, text="Date", padding=10)
        date_frame.pack(fill=tk.X, pady=5)
        today_label = tk.Label(date_frame, text=datetime.now().strftime("%A, %B %d, %Y"))
        today_label.pack()
        
        # Time Period Selection
        period_frame = ttk.LabelFrame(main_frame, text="Time of Day", padding=10)
        period_frame.pack(fill=tk.X, pady=5)
        
        self.period_var = tk.StringVar(value="morning")
        ttk.Radiobutton(period_frame, text="Morning", variable=self.period_var, value="morning").pack(anchor=tk.W)
        ttk.Radiobutton(period_frame, text="Afternoon", variable=self.period_var, value="afternoon").pack(anchor=tk.W)
        
        # Symptom Severity
        severity_frame = ttk.LabelFrame(main_frame, text="Overall Symptom Severity", padding=10)
        severity_frame.pack(fill=tk.X, pady=5)
        
        severity_desc = tk.Label(
            severity_frame,
            text="0 = None  |  1 = Mild  |  2 = Moderate  |  3 = Severe",
            font=("Helvetica", 9, "italic")
        )
        severity_desc.pack()
        
        self.severity_scale = tk.Scale(
            severity_frame,
            from_=0, to=3,
            orient=tk.HORIZONTAL,
            length=300,
            label="Severity",
            tickinterval=1
        )
        self.severity_scale.set(0)
        self.severity_scale.pack(fill=tk.X, pady=5)
        
        # Symptoms Checklist
        symptoms_frame = ttk.LabelFrame(main_frame, text="Symptoms Experienced", padding=10)
        symptoms_frame.pack(fill=tk.X, pady=5)
        
        self.symptom_vars = {}
        symptoms = [
            "Sneezing", "Runny Nose", "Nasal Congestion",
            "Itchy Eyes", "Watery Eyes", "Cough",
            "Itchy Throat", "Fatigue"
        ]
        
        for symptom in symptoms:
            var = tk.BooleanVar()
            self.symptom_vars[symptom] = var
            cb = ttk.Checkbutton(symptoms_frame, text=symptom, variable=var)
            cb.pack(anchor=tk.W, pady=2)
        
        # Additional Notes
        notes_frame = ttk.LabelFrame(main_frame, text="Additional Notes", padding=10)
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.notes_text = tk.Text(notes_frame, height=4, width=50, wrap=tk.WORD)
        self.notes_text.pack(fill=tk.BOTH, expand=True)
        
        # Button Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        submit_btn = ttk.Button(
            button_frame,
            text="Submit Symptom Report",
            command=self.submit_symptoms
        )
        submit_btn.pack(side=tk.LEFT, padx=5)
        
        view_btn = ttk.Button(
            button_frame,
            text="View Today's Data",
            command=self.view_today_data
        )
        view_btn.pack(side=tk.LEFT, padx=5)
        
        fetch_btn = ttk.Button(
            button_frame,
            text="Fetch Pollen Data",
            command=self.fetch_pollen_data
        )
        fetch_btn.pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(status_frame, text="Ready", fg="green")
        self.status_label.pack(anchor=tk.W)
    
    def set_status(self, message, color="black"):
        """Update status label."""
        self.status_label.config(text=message, fg=color)
        self.root.update()
    
    def submit_symptoms(self):
        """Submit symptom report."""
        try:
            severity = self.severity_scale.get()
            period = self.period_var.get()
            
            # Get selected symptoms
            selected_symptoms = [s for s, var in self.symptom_vars.items() if var.get()]
            selected_str = ", ".join(selected_symptoms) if selected_symptoms else "None reported"
            
            # Get notes
            notes = self.notes_text.get("1.0", tk.END).strip()
            full_notes = f"Symptoms: {selected_str}. {notes}"
            
            # Log symptoms
            result = log_symptoms(severity, period=period, notes=full_notes)
            
            self.set_status(f"Symptoms logged successfully for {period}!", color="green")
            messagebox.showinfo("Success", f"Symptom report submitted for {period}!")
            
            # Clear form
            self.severity_scale.set(0)
            for var in self.symptom_vars.values():
                var.set(False)
            self.notes_text.delete("1.0", tk.END)
            
        except Exception as e:
            self.set_status(f"Error: {str(e)}", color="red")
            messagebox.showerror("Error", f"Failed to log symptoms: {str(e)}")
    
    def fetch_pollen_data(self):
        """Fetch pollen data in background thread."""
        self.set_status("Fetching pollen data...", color="blue")
        
        def background_fetch():
            try:
                from src.collect_pollen import collect_daily_pollen
                collect_daily_pollen()
                self.set_status("Pollen data fetched successfully!", color="green")
                messagebox.showinfo("Success", "Pollen forecast updated!")
            except Exception as e:
                self.set_status(f"Error fetching pollen data: {str(e)}", color="red")
                messagebox.showerror("Error", f"Failed to fetch pollen data: {str(e)}")
        
        thread = threading.Thread(target=background_fetch, daemon=True)
        thread.start()
    
    def view_today_data(self):
        """View today's pollen and symptom data."""
        from src.utils import get_today_str
        today = get_today_str()
        
        try:
            from src.collect_symptoms import get_symptoms_for_date
            symptoms = get_symptoms_for_date(today)
            
            # Create info window
            info_window = tk.Toplevel(self.root)
            info_window.title("Today's Data")
            info_window.geometry("500x400")
            
            # Symptoms info
            symptoms_text = tk.Text(info_window, height=20, width=60, wrap=tk.WORD)
            symptoms_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            if symptoms:
                text = "TODAY'S SYMPTOMS:\n\n"
                for i, symptom in enumerate(symptoms, 1):
                    period = symptom.get("period", "unknown")
                    severity = symptom.get("severity", "unrated")
                    notes = symptom.get("notes", "no notes")
                    text += f"{i}. {period.capitalize()}\n"
                    text += f"   Severity: {severity}/3\n"
                    text += f"   Notes: {notes}\n\n"
            else:
                text = "No symptom reports recorded for today."
            
            symptoms_text.insert("1.0", text)
            symptoms_text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve data: {str(e)}")

def launch_gui():
    """Launch the GUI application."""
    root = tk.Tk()
    app = PollenTrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
