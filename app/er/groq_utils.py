import os
import json
from groq import Groq

# Initialize Groq client
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY', ''))

def analyze_symptoms_with_groq(symptoms_text, patient_name=None, patient_age=None, patient_gender=None):
    """
    Use Groq AI to analyze symptoms and return structured medical assessment.
    """
    if not os.getenv('GROQ_API_KEY'):
        print("No GROQ_API_KEY found — skipping AI analysis")
        return None
    
    # Build patient info string
    patient_info_parts = []
    if patient_name:
        patient_info_parts.append(f"Name: {patient_name}")
    if patient_age:
        patient_info_parts.append(f"Age: {patient_age}")
    if patient_gender:
        patient_info_parts.append(f"Gender: {patient_gender}")
    
    patient_info = ', '.join(patient_info_parts) if patient_info_parts else 'Not provided'
    
    prompt = f"""
You are an emergency room AI triage assistant. Analyze the following patient symptoms and provide a structured medical assessment.

Patient Information:
{patient_info}

Symptoms:
{symptoms_text}

Provide your analysis in the following JSON format ONLY (no other text):
{{
    "severity": "red",
    "severity_label": "CRITICAL - Immediate attention required",
    "predicted_conditions": ["condition1", "condition2"],
    "suggested_tests": ["test1", "test2", "test3"],
    "detected_symptoms": ["symptom1", "symptom2"],
    "confidence": 85,
    "immediate_actions": ["action1", "action2"],
    "emergency_care_steps": [
        "Step 1: Clear step-by-step first aid instruction",
        "Step 2: What ER staff can do before doctor arrives"
    ],
    "vital_signs_to_monitor": ["BP every 5 mins", "Heart Rate", "SpO2"],
    "red_flags": ["Danger sign 1", "Danger sign 2"],
    "medications_to_prepare": ["Medication 1", "Medication 2"],
    "equipment_needed": ["Equipment 1", "Equipment 2"],
    "differential_diagnosis": ["possible condition 1", "possible condition 2"],
    "follow_up_questions": ["Question 1?", "Question 2?"]
}}

Severity Guidelines:
- RED: Life-threatening (chest pain, difficulty breathing, severe bleeding, unconscious, stroke, heart attack, seizure, anaphylaxis)
- YELLOW: Urgent, needs attention within 30 mins (fractures, high fever >103°F, severe pain, dehydration, asthma attack)
- GREEN: Stable, can wait (mild symptoms, minor injuries, cold/flu, rash, sprain)

Include practical emergency care steps that ER nurses/staff can perform while waiting for the doctor.
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an emergency medicine AI. Always respond with valid JSON only. No markdown, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=600
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Clean the response (remove markdown if any)
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()
        
        result = json.loads(result_text)
        
        # Add metadata
        result['raw_text'] = symptoms_text
        result['ai_model'] = 'Groq AI (Llama 3.1 8B)'
        result['analysis_type'] = 'AI-Powered'
        
        # Ensure severity_color exists
        severity_colors = {'red': 'red', 'yellow': 'yellow', 'green': 'green'}
        result['severity_color'] = severity_colors.get(result.get('severity', 'green'), 'green')
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"Groq JSON parsing error: {e}")
        print(f"Raw response: {result_text}")
        return None
    except Exception as e:
        print(f"Groq API error: {e}")
        return None


def analyze_symptoms_hybrid(symptoms_text, patient_name=None, patient_age=None, patient_gender=None):
    """
    Hybrid approach: Try Groq AI first, fall back to rule-based if it fails.
    """
    # Try Groq first
    print("=" * 50)
    print("Attempting Groq AI analysis...")
    groq_result = analyze_symptoms_with_groq(
        symptoms_text, 
        patient_name=patient_name,
        patient_age=patient_age,
        patient_gender=patient_gender
    )
    
    if groq_result:
        print("✅ Using Groq AI analysis")
        return groq_result
    
    # Fallback to rule-based
    print("⚠️ Groq unavailable — using rule-based analysis")
    from app.er.utils import analyze_symptoms
    rule_result = analyze_symptoms(symptoms_text)
    rule_result['ai_model'] = 'Rule-Based (Offline)'
    rule_result['analysis_type'] = 'Standard'
    return rule_result

def check_prescription_with_ai(patient, drug_name, dosage):
    """Use Groq AI for comprehensive prescription safety check."""
    if not os.getenv('GROQ_API_KEY'):
        return None
    
    patient_info = f"""
Patient: {patient.get('full_name', 'Unknown')}
Age: {patient.get('age', 'N/A')}
Gender: {patient.get('gender', 'N/A')}
Allergies: {patient.get('allergies', 'None')}
Chronic Conditions: {patient.get('chronic_conditions', 'None')}
Blood Group: {patient.get('blood_group', 'N/A')}
"""
    
    prompt = f"""You are a clinical pharmacist AI. Check this prescription for safety issues.

PATIENT:
{patient_info}

PRESCRIPTION:
Drug: {drug_name}
Dosage: {dosage}

Check for: drug interactions, allergies, pregnancy risks, kidney/liver issues, duplicate therapy, age-appropriate dosing, contraindications.

Return ONLY JSON:
{{
    "safe": true,
    "warnings": [
        {{"severity": "high", "message": "Warning message"}}
    ],
    "alternative_suggestions": ["Alternative drug 1"],
    "monitoring_required": ["Monitor liver function", "Check renal panel"],
    "confidence": 90
}}"""

    try:
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a pharmacist AI. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, max_tokens=400
        )
        result_text = response.choices[0].message.content.strip()
        if '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()
        return json.loads(result_text)
    except Exception as e:
        print(f"Prescription AI check failed: {e}")
        return None


def detect_outbreaks_with_ai(clusters):
    """Use Groq AI to analyze community health data and detect outbreaks."""
    if not os.getenv('GROQ_API_KEY') or not clusters:
        return None
    
    data_summary = "Symptom clusters detected in last 7 days:\n"
    for c in clusters:
        data_summary += f"- {c.get('predicted_condition', 'Unknown')}: {c['case_count']} cases in {c['city']}, {c['state']}\n"
    
    prompt = f"""You are a public health epidemiologist AI. Analyze this community health data for outbreak patterns.

{data_summary}

Return ONLY JSON:
{{
    "outbreak_alerts": [
        {{"location": "City, State", "condition": "Disease", "risk_level": "High", "action_required": "Immediate action"}}
    ],
    "trend_analysis": "Brief epidemiological analysis",
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "confidence": 85
}}"""

    try:
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a public health AI. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, max_tokens=500
        )
        result_text = response.choices[0].message.content.strip()
        if '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()
        return json.loads(result_text)
    except Exception as e:
        print(f"Outbreak AI detection failed: {e}")
        return None