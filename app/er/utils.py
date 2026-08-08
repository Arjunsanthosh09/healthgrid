import speech_recognition as sr
import os
from datetime import datetime

# Symptom keyword database for severity scoring
SEVERE_SYMPTOMS = [
    'chest pain', 'difficulty breathing', 'seizure', 'unconscious',
    'heavy bleeding', 'stroke', 'heart attack', 'not breathing',
    'choking', 'severe burn', 'head injury', 'poisoning',
    'overdose', 'anaphylaxis', 'cardiac arrest', 'respiratory failure'
]

URGENT_SYMPTOMS = [
    'fracture', 'deep cut', 'high fever', 'dehydration',
    'severe pain', 'vomiting', 'diarrhea', 'asthma attack',
    'allergic reaction', 'infection', 'migraine', 'sprain'
]

COMMON_CONDITIONS = {
    'chest pain': ['Myocardial Infarction', 'Angina', 'Pericarditis'],
    'difficulty breathing': ['Asthma', 'COPD', 'Pulmonary Embolism', 'Pneumonia'],
    'high fever': ['Malaria', 'Dengue', 'Typhoid', 'COVID-19'],
    'severe pain': ['Appendicitis', 'Kidney Stone', 'Pancreatitis'],
    'vomiting': ['Food Poisoning', 'Gastroenteritis', 'Migraine'],
    'head injury': ['Concussion', 'Intracranial Hemorrhage', 'Skull Fracture'],
    'seizure': ['Epilepsy', 'Febrile Seizure', 'Meningitis'],
    'unconscious': ['Stroke', 'Hypoglycemia', 'Drug Overdose'],
}

SUGGESTED_TESTS = {
    'Myocardial Infarction': 'ECG, Troponin-I, CK-MB, CBC',
    'Asthma': 'Peak Flow Meter, Chest X-Ray, Pulse Oximetry',
    'Pneumonia': 'Chest X-Ray, CBC, Sputum Culture, CRP',
    'Malaria': 'Malaria Antigen Test, Blood Smear, CBC',
    'Dengue': 'NS1 Antigen, Dengue IgM/IgG, Platelet Count',
    'Appendicitis': 'Ultrasound Abdomen, CBC, CRP',
    'Stroke': 'CT Brain (Non-Contrast), MRI Brain, Carotid Doppler',
    'Food Poisoning': 'Stool Culture, CBC, Electrolytes',
}


def transcribe_audio(audio_file_path, language='en-IN'):
    """
    Convert audio file to text using speech recognition.
    """
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_file_path) as source:
            audio = recognizer.record(source)
        
        # Try Google Speech Recognition (needs internet)
        try:
            text = recognizer.recognize_google(audio, language=language)
            return text, None
        except sr.RequestError:
            # Fallback to offline Sphinx
            try:
                text = recognizer.recognize_sphinx(audio)
                return text, None
            except:
                return None, "Speech recognition failed. Please type symptoms manually."
    except Exception as e:
        return None, str(e)


def analyze_symptoms(symptoms_text):
    """
    Analyze symptoms text and return severity, predictions, and test suggestions.
    """
    if not symptoms_text:
        return {
            'severity': 'unknown',
            'severity_color': 'gray',
            'predicted_conditions': ['Unable to determine'],
            'suggested_tests': 'Manual assessment required',
            'detected_symptoms': [],
            'confidence': 0
        }
    
    symptoms_text_lower = symptoms_text.lower()
    detected_symptoms = []
    severity_score = 0
    
    # Check for severe symptoms
    for symptom in SEVERE_SYMPTOMS:
        if symptom in symptoms_text_lower:
            detected_symptoms.append(symptom)
            severity_score += 3
    
    # Check for urgent symptoms
    for symptom in URGENT_SYMPTOMS:
        if symptom in symptoms_text_lower:
            detected_symptoms.append(symptom)
            severity_score += 1
    
    # Determine severity level
    if severity_score >= 3:
        severity = 'red'
        severity_color = 'red'
        severity_label = 'CRITICAL - Immediate attention required'
    elif severity_score >= 1:
        severity = 'yellow'
        severity_color = 'yellow'
        severity_label = 'URGENT - Attention needed within 30 minutes'
    else:
        severity = 'green'
        severity_color = 'green'
        severity_label = 'STABLE - Can wait for routine care'
    
    # Predict conditions based on detected symptoms
    predicted_conditions = []
    for symptom in detected_symptoms:
        if symptom in COMMON_CONDITIONS:
            predicted_conditions.extend(COMMON_CONDITIONS[symptom])
    
    # Remove duplicates
    predicted_conditions = list(set(predicted_conditions))
    
    if not predicted_conditions:
        predicted_conditions = ['General Assessment Required']
    
    # Suggest tests based on predicted conditions
    suggested_tests = []
    for condition in predicted_conditions:
        if condition in SUGGESTED_TESTS:
            suggested_tests.append(f"{condition}: {SUGGESTED_TESTS[condition]}")
    
    if not suggested_tests:
        suggested_tests = ['Vital Signs (BP, HR, SpO2, Temp), CBC, RBS']
    
    # Calculate confidence
    confidence = min(95, len(detected_symptoms) * 15 + 30)
    
    return {
        'severity': severity,
        'severity_color': severity_color,
        'severity_label': severity_label,
        'predicted_conditions': predicted_conditions[:5],
        'suggested_tests': suggested_tests,
        'detected_symptoms': detected_symptoms,
        'confidence': confidence,
        'raw_text': symptoms_text
    }


def generate_alert_for_severe_case(patient_name, severity, conditions, er_dept_name):
    """
    Generate alert message for Red severity cases.
    """
    if severity == 'red':
        return {
            'title': f'🚨 CRITICAL CASE - {er_dept_name}',
            'message': f'Patient: {patient_name}\nSeverity: CRITICAL\nConditions: {", ".join(conditions)}\nImmediate attention required!',
            'alert_type': 'severe_case',
            'severity': 'red'
        }
    return None