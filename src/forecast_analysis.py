"""
Forecast Analysis Module - Analyzes pollen forecasts and recommends treatments
"""

import json
from datetime import datetime, timedelta
from src.utils import read_json, get_today_str
from src.predict import predict_symptoms

# Treatment database with dosages and timings
TREATMENT_DATABASE = {
    'TREE': {
        'primary': {
            'name': 'Cetirizine (Zyrtec) or Fexofenadine (Allegra)',
            'type': 'Antihistamine - Second Generation (Non-Drowsy)',
            'dosages': {
                'low': {'amount': '5-10 mg', 'timing': 'Once daily', 'notes': 'Morning'},
                'moderate': {'amount': '10 mg', 'timing': 'Once daily', 'notes': 'Morning'},
                'high': {'amount': '10 mg', 'timing': 'Twice daily', 'notes': 'Morning & Evening'}
            }
        },
        'secondary': {
            'name': 'Fluticasone Propionate (Flonase) Nasal Spray',
            'type': 'Intranasal Corticosteroid',
            'dosages': {
                'low': {'amount': '1-2 sprays', 'timing': 'Once daily', 'notes': 'Morning, 20 min before exposure'},
                'moderate': {'amount': '2 sprays', 'timing': 'Twice daily', 'notes': 'Morning & Evening'},
                'high': {'amount': '2 sprays', 'timing': 'Twice daily + PRN', 'notes': 'Morning, Evening, and as needed'}
            }
        },
        'preventive': {
            'name': 'Montelukast (Singulair)',
            'type': 'Leukotriene Receptor Antagonist',
            'dosages': {
                'moderate': {'amount': '10 mg', 'timing': 'Once daily', 'notes': 'Evening for best effect'},
                'high': {'amount': '10 mg', 'timing': 'Once daily', 'notes': 'Evening, start 1-2 weeks before season'}
            }
        }
    },
    'GRASS': {
        'primary': {
            'name': 'Loratadine (Claritin) or Desloratadine (Clarinex)',
            'type': 'Antihistamine - Second Generation (Non-Drowsy)',
            'dosages': {
                'low': {'amount': '10 mg', 'timing': 'Once daily', 'notes': 'Take 30 min before exposure if possible'},
                'moderate': {'amount': '10 mg', 'timing': 'Once daily', 'notes': 'Morning'},
                'high': {'amount': '10 mg', 'timing': 'Twice daily', 'notes': 'Morning & Evening'}
            }
        },
        'secondary': {
            'name': 'Triamcinolone Nasal Spray',
            'type': 'Intranasal Corticosteroid',
            'dosages': {
                'low': {'amount': '1-2 sprays', 'timing': 'Once daily', 'notes': 'Morning'},
                'moderate': {'amount': '2 sprays', 'timing': 'Once daily', 'notes': 'Morning'},
                'high': {'amount': '2 sprays', 'timing': 'Twice daily', 'notes': 'Morning & Evening'}
            }
        },
        'rescue': {
            'name': 'Diphenhydramine (Benadryl)',
            'type': 'Antihistamine - First Generation',
            'dosages': {
                'high': {'amount': '25-50 mg', 'timing': 'As needed', 'notes': 'May cause drowsiness, take at night'}
            }
        }
    },
    'WEED': {
        'primary': {
            'name': 'Levocetirizine (Xyzal)',
            'type': 'Antihistamine - Second Generation (Non-Drowsy)',
            'dosages': {
                'low': {'amount': '2.5-5 mg', 'timing': 'Once daily', 'notes': 'Evening (may cause drowsiness)'},
                'moderate': {'amount': '5 mg', 'timing': 'Once daily', 'notes': 'Evening'},
                'high': {'amount': '5 mg', 'timing': 'Twice daily', 'notes': 'Morning & Evening'}
            }
        },
        'secondary': {
            'name': 'Beclomethasone Nasal Spray',
            'type': 'Intranasal Corticosteroid',
            'dosages': {
                'moderate': {'amount': '1-2 sprays', 'timing': 'Twice daily', 'notes': 'Morning & Evening'},
                'high': {'amount': '2 sprays', 'timing': 'Twice daily', 'notes': 'Morning & Evening, increase as needed'}
            }
        },
        'preventive': {
            'name': 'Olopatadine (Patanol) Eye Drops',
            'type': 'Antihistamine Eye Drops',
            'dosages': {
                'low': {'amount': '1 drop', 'timing': 'Twice daily', 'notes': 'In each eye as needed'},
                'moderate': {'amount': '1 drop', 'timing': 'Twice daily', 'notes': 'In each eye, every 6-8 hours'},
                'high': {'amount': '1 drop', 'timing': 'Every 4-6 hours', 'notes': 'In each eye as needed'}
            }
        }
    },
    'MOLD': {
        'primary': {
            'name': 'Itraconazole (Sporanox)',
            'type': 'Antifungal',
            'dosages': {
                'moderate': {'amount': '200 mg', 'timing': 'Once daily', 'notes': 'For severe mold allergies; requires Rx'},
                'high': {'amount': '200 mg', 'timing': 'Twice daily', 'notes': 'For severe cases; requires Rx'}
            }
        },
        'secondary': {
            'name': 'Mometasone Furoate (Asmanex) Nasal Spray',
            'type': 'Intranasal Corticosteroid',
            'dosages': {
                'low': {'amount': '1-2 sprays', 'timing': 'Once daily', 'notes': 'Morning or evening'},
                'moderate': {'amount': '2 sprays', 'timing': 'Twice daily', 'notes': 'Morning & Evening'},
                'high': {'amount': '2 sprays', 'timing': 'Twice daily', 'notes': 'Morning & Evening, may increase'}
            }
        },
        'environmental': {
            'name': 'Environmental Controls',
            'type': 'Non-Pharmacological',
            'dosages': {
                'any': {'amount': 'Various', 'timing': 'Ongoing', 'notes': 'HEPA filters, dehumidifier (keep humidity <50%), clean ventilation'}
            }
        }
    }
}

# Lifestyle recommendations by severity
LIFESTYLE_RECOMMENDATIONS = {
    'low': {
        'outdoor': 'Outdoor activities are fine',
        'timing': 'Pollen counts typically lowest after rain and in evening',
        'clothing': 'Regular clothing is fine',
        'home': 'Keep windows open if desired; minimal filtering needed'
    },
    'moderate': {
        'outdoor': 'Limit prolonged outdoor activities, especially during peak hours (10am-4pm)',
        'timing': 'Plan outdoor activities for early morning or after rain',
        'clothing': 'Wash clothes after outdoor activities; consider sunglasses/hat',
        'home': 'Keep windows closed during peak pollen hours; run AC on recirculate'
    },
    'high': {
        'outdoor': 'Stay indoors; avoid unnecessary outdoor activities',
        'timing': 'Minimize outdoor time between 10am-4pm',
        'clothing': 'Wear protective clothing (long sleeves, hats); wash immediately after outdoor exposure',
        'home': 'Keep windows and doors closed; run HEPA filter; shower and wash hair after outdoor time',
        'pet': 'Bathe pets after being outdoors to remove pollen'
    }
}


def calculate_forecast_severity(daily_forecast):
    """
    Calculate overall severity of a day's forecast (0-3 scale).
    
    Args:
        daily_forecast: Single day from pollenData.dailyInfo
    
    Returns:
        int: Severity rating 0-3
    """
    if not daily_forecast:
        return 0
    
    max_value = 0
    plant_count_high = 0
    
    if daily_forecast.get('plantInfo'):
        for plant in daily_forecast['plantInfo']:
            if plant.get('indexInfo'):
                value = plant['indexInfo'].get('value', 0)
                max_value = max(max_value, value)
                if value >= 3:
                    plant_count_high += 1
    
    # Map index values to severity: 0-1=low, 2=moderate, 3=high, 4+=very high
    if max_value <= 1:
        return 0
    elif max_value == 2:
        return 1
    elif max_value == 3:
        return 2 if plant_count_high <= 2 else 3
    else:
        return 3


def get_risk_plants(daily_forecast):
    """
    Extract plants with concerning pollen levels from forecast.
    
    Args:
        daily_forecast: Single day from pollenData.dailyInfo
    
    Returns:
        dict: Organized by type with high-risk families
    """
    risk_by_type = {}
    
    if not daily_forecast.get('plantInfo'):
        return risk_by_type
    
    for plant in daily_forecast['plantInfo']:
        if plant.get('indexInfo'):
            value = plant['indexInfo'].get('value', 0)
            if value >= 2:  # Moderate or higher risk
                plant_type = plant.get('plantDescription', {}).get('type', 'UNKNOWN')
                name = plant.get('displayName', 'Unknown')
                
                if plant_type not in risk_by_type:
                    risk_by_type[plant_type] = []
                
                risk_by_type[plant_type].append({
                    'name': name,
                    'value': value,
                    'category': plant['indexInfo'].get('category', 'Unknown')
                })
    
    return risk_by_type


def get_treatment_recommendations(daily_forecast):
    """
    Get personalized treatment recommendations for a forecast day.
    
    Args:
        daily_forecast: Single day from pollenData.dailyInfo
    
    Returns:
        dict: Treatment recommendations including medications and dosages
    """
    severity = calculate_forecast_severity(daily_forecast)
    risk_plants = get_risk_plants(daily_forecast)
    
    severity_level = ['low', 'moderate', 'high', 'very_high'][severity]
    
    recommendations = {
        'severity': severity,
        'severity_label': severity_level.replace('_', ' ').title(),
        'risk_plant_types': list(risk_plants.keys()),
        'medications': [],
        'lifestyle': LIFESTYLE_RECOMMENDATIONS.get(severity_level if severity_level != 'very_high' else 'high', {})
    }
    
    # Get treatments for affected plant types
    processed_types = set()
    
    for plant_type in risk_plants.keys():
        if plant_type not in processed_types and plant_type in TREATMENT_DATABASE:
            processed_types.add(plant_type)
            
            treatments = TREATMENT_DATABASE[plant_type]
            med_recommendations = []
            
            # Add primary treatment
            if 'primary' in treatments:
                primary = treatments['primary']
                dosage = primary['dosages'].get(severity_level if severity_level != 'very_high' else 'high')
                if dosage:
                    med_recommendations.append({
                        'priority': 'PRIMARY',
                        'name': primary['name'],
                        'type': primary['type'],
                        'dosage': dosage['amount'],
                        'timing': dosage['timing'],
                        'notes': dosage.get('notes', '')
                    })
            
            # Add secondary treatment if moderate or higher
            if severity >= 1 and 'secondary' in treatments:
                secondary = treatments['secondary']
                dosage = secondary['dosages'].get(severity_level if severity_level != 'very_high' else 'high')
                if dosage:
                    med_recommendations.append({
                        'priority': 'SECONDARY',
                        'name': secondary['name'],
                        'type': secondary['type'],
                        'dosage': dosage['amount'],
                        'timing': dosage['timing'],
                        'notes': dosage.get('notes', '')
                    })
            
            # Add tertiary treatment if high severity
            if severity >= 2:
                for key in ['preventive', 'rescue', 'environmental']:
                    if key in treatments:
                        tertiary = treatments[key]
                        dosage = tertiary['dosages'].get(severity_level if severity_level != 'very_high' else 'high')
                        if not dosage and key == 'preventive':
                            dosage = tertiary['dosages'].get('moderate')
                        if not dosage and key == 'environmental':
                            dosage = tertiary['dosages'].get('any')
                        if dosage:
                            med_recommendations.append({
                                'priority': 'ADDITIONAL',
                                'name': tertiary['name'],
                                'type': tertiary['type'],
                                'dosage': dosage['amount'],
                                'timing': dosage['timing'],
                                'notes': dosage.get('notes', '')
                            })
            
            recommendations['medications'].extend(med_recommendations)
    
    return recommendations


def build_forecast_summary(pollen_data, days_ahead=5):
    """
    Build a comprehensive forecast summary with recommendations.
    
    Args:
        pollen_data: Complete forecast data from Google API
        days_ahead: Number of days to analyze (default 5)
    
    Returns:
        dict: Forecast summary with daily recommendations
    """
    if not pollen_data or not pollen_data.get('dailyInfo'):
        return {'status': 'error', 'message': 'No pollen data available'}
    
    forecast_summary = {
        'status': 'success',
        'generated_at': datetime.now().isoformat(),
        'days': []
    }
    
    # Analyze each day in forecast
    for idx, daily in enumerate(pollen_data['dailyInfo'][:days_ahead]):
        date_info = daily.get('date', {})
        date_str = f"{date_info.get('year', '')}-{date_info.get('month', ''):02d}-{date_info.get('day', ''):02d}"
        
        day_summary = {
            'date': date_str,
            'day_of_week': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][
                (idx + 2) % 7  # Approximate day of week
            ],
            'severity': calculate_forecast_severity(daily),
            'severity_label': ['Low', 'Moderate', 'High', 'Very High'][calculate_forecast_severity(daily)],
            'risk_plants': get_risk_plants(daily),
            'treatments': get_treatment_recommendations(daily)
        }
        
        forecast_summary['days'].append(day_summary)
    
    return forecast_summary


def get_critical_days(forecast_summary, threshold=2):
    """
    Identify days with concerning pollen forecasts.
    
    Args:
        forecast_summary: Output from build_forecast_summary()
        threshold: Severity threshold (0-3); days at or above are critical
    
    Returns:
        list: Days with concerning forecasts
    """
    critical = []
    
    for day in forecast_summary.get('days', []):
        if day['severity'] >= threshold:
            critical.append({
                'date': day['date'],
                'severity': day['severity_label'],
                'plants': list(day['risk_plants'].keys())
            })
    
    return critical


def get_preparation_recommendations(forecast_summary):
    """
    Get advance preparation recommendations based on 5-day forecast.
    
    Args:
        forecast_summary: Output from build_forecast_summary()
    
    Returns:
        dict: Preparation steps and timeline
    """
    critical_days = get_critical_days(forecast_summary, threshold=2)
    max_severity = max([d['severity'] for d in forecast_summary['days']], default=0)
    
    recommendations = {
        'advance_prep': [],
        'critical_days': len(critical_days),
        'max_forecast_severity': max_severity
    }
    
    if max_severity >= 1:
        recommendations['advance_prep'].append({
            'timing': 'Now',
            'action': 'Refill or purchase antihistamine medications',
            'reason': 'Avoid running out during peak pollen period'
        })
    
    if max_severity >= 2:
        recommendations['advance_prep'].extend([
            {
                'timing': '1-2 days before high pollen',
                'action': 'Start nasal corticosteroid spray (if not already using)',
                'reason': 'Takes 24-48 hours to reach full effectiveness'
            },
            {
                'timing': 'Before high pollen days',
                'action': 'Clean HVAC filters and prepare air purifier',
                'reason': 'Reduces indoor pollen levels significantly'
            }
        ])
    
    if max_severity >= 3:
        recommendations['advance_prep'].extend([
            {
                'timing': '1-2 weeks before peak',
                'action': 'Consider leukotriene inhibitor (Singulair) if severe',
                'reason': 'Provides additional symptom control for severe allergies'
            },
            {
                'timing': 'Before high pollen days',
                'action': 'Plan indoor activities; arrange work-from-home if possible',
                'reason': 'Severe pollen may cause significant symptoms'
            }
        ])
    
    return recommendations


def format_treatment_schedule(forecast_summary):
    """
    Format treatment recommendations into a simple daily schedule.
    
    Args:
        forecast_summary: Output from build_forecast_summary()
    
    Returns:
        dict: Daily treatment schedule
    """
    schedule = {}
    
    for day in forecast_summary.get('days', []):
        date = day['date']
        treatments = day['treatments'].get('medications', [])
        
        # Organize by timing
        by_timing = {}
        for med in treatments:
            timing = med['timing']
            if timing not in by_timing:
                by_timing[timing] = []
            by_timing[timing].append({
                'name': med['name'],
                'dosage': med['dosage'],
                'notes': med.get('notes', '')
            })
        
        schedule[date] = {
            'severity': day['severity_label'],
            'schedule': by_timing
        }
    
    return schedule
