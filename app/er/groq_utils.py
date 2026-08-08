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
    """Use Groq AI for comprehensive prescription safety check with patient history."""
    if not os.getenv('GROQ_API_KEY'):
        return None
    
    # Get patient's previous prescriptions from database
    try:
        import pymysql
        conn = pymysql.connect(
            host='localhost', user='root', password='', database='healthgrid',
            cursorclass=pymysql.cursors.DictCursor
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT drugs_json, diagnosis, prescribed_date 
            FROM prescriptions WHERE patient_id = %s 
            ORDER BY prescribed_date DESC LIMIT 10
        """, (patient['id'],))
        past_meds = cur.fetchall()
        
        cur.execute("""
            SELECT event_date, event_type, title, description 
            FROM disease_timeline WHERE patient_id = %s 
            ORDER BY event_date DESC LIMIT 20
        """, (patient['id'],))
        past_history = cur.fetchall()
        cur.close()
        conn.close()
    except:
        past_meds = []
        past_history = []
    
    # Build comprehensive patient profile
    patient_info = f"""
PATIENT PROFILE:
Name: {patient.get('full_name', 'Unknown')}
Age: {patient.get('age', 'N/A')}
Gender: {patient.get('gender', 'N/A')}
Blood Group: {patient.get('blood_group', 'N/A')}
ALLERGIES: {patient.get('allergies', 'None reported')}
CHRONIC CONDITIONS: {patient.get('chronic_conditions', 'None reported')}
"""

    # Add past medications
    if past_meds:
        patient_info += "\nPAST MEDICATIONS:\n"
        for med in past_meds:
            patient_info += f"- {med['prescribed_date']}: {med.get('drugs_json', 'Unknown')} (Diagnosis: {med.get('diagnosis', 'Unknown')})\n"
    
    # Add disease history
    if past_history:
        patient_info += "\nMEDICAL HISTORY:\n"
        for event in past_history:
            patient_info += f"- {event['event_date']}: [{event['event_type']}] {event['title']}"
            if event.get('description'):
                patient_info += f" — {event['description']}"
            patient_info += "\n"
    
    prompt = f"""You are a clinical pharmacist AI. Review this prescription against the patient's complete medical history.

{patient_info}

NEW PRESCRIPTION:
Drug: {drug_name}
Dosage: {dosage}

PERFORM THESE CHECKS:
1. ALLERGY CHECK: Does patient have known allergy to this drug or similar drugs?
2. DRUG INTERACTION: Does this drug interact with any past medications?
3. DISEASE CONTRADICTION: Is this drug contraindicated with patient's chronic conditions?
4. DOSAGE SAFETY: Is the dosage appropriate for patient's age and conditions?
5. DUPLICATE THERAPY: Is patient already taking this or similar drug?
6. ORGAN FUNCTION: Any kidney/liver concerns based on patient history?

Return ONLY JSON:
{{
    "safe": false,
    "warnings": [
        {{"severity": "high", "message": "Specific warning with reason"}}
    ],
    "alternative_suggestions": ["Safer alternative drug"],
    "monitoring_required": ["What to monitor"],
    "confidence": 90,
    "summary": "Brief assessment summary"
}}"""

    try:
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a clinical pharmacist AI. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2, max_tokens=600
        )
        result_text = response.choices[0].message.content.strip()
        if '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()
        return json.loads(result_text)
    except Exception as e:
        print(f"AI prescription check failed: {e}")
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
    

def predict_health_risks_with_ai(patient, timeline_data):
    """Use Groq AI to predict future health risks from patient history."""
    if not os.getenv('GROQ_API_KEY'):
        return None
    
    # Build patient history summary
    history_summary = f"Patient: {patient.get('full_name', 'Unknown')}, Age: {patient.get('age', 'N/A')}, Gender: {patient.get('gender', 'N/A')}\n"
    history_summary += f"Blood Group: {patient.get('blood_group', 'N/A')}, Allergies: {patient.get('allergies', 'None')}\n"
    history_summary += f"Chronic Conditions: {patient.get('chronic_conditions', 'None')}\n\n"
    history_summary += "Medical History Timeline:\n"
    
    for event in timeline_data:
        history_summary += f"- {event['event_date']}: [{event['event_type']}] {event['title']}\n"
    
    prompt = f"""You are a clinical AI assistant. Analyze this patient's medical history and predict future health risks.

{history_summary}

Return ONLY JSON:
{{
    "risks": [
        {{
            "condition": "Disease name",
            "probability": "High/Medium/Low",
            "timeframe": "Expected timeframe",
            "recommendation": "Preventive action"
        }}
    ],
    "overall_score": 45,
    "risk_level": "Medium",
    "summary": "Brief clinical summary"
}}"""

    try:
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a clinical AI. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2, max_tokens=500
        )
        result_text = response.choices[0].message.content.strip()
        if '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()
        return json.loads(result_text)
    except Exception as e:
        print(f"AI prediction failed: {e}")
        return {
            "risks": [],
            "overall_score": 0,
            "risk_level": "Unknown",
            "summary": "AI analysis unavailable"
        }