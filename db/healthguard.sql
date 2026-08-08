-- Create database
CREATE DATABASE IF NOT EXISTS healthgrid;
USE healthgrid;

-- =============================================
-- USERS TABLE (All roles: ER, Doctor, Health Officer, Patient)
-- =============================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('patient', 'er_doctor', 'clinic_doctor', 'hospital_doctor', 'health_officer', 'admin') NOT NULL,
    phone VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =============================================
-- FACILITIES TABLE (Clinics & Hospitals)
-- =============================================
CREATE TABLE facilities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    type ENUM('clinic', 'hospital') NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    phone VARCHAR(15),
    email VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- FACILITY-DOCTOR LINK (Which doctor belongs to which facility)
-- =============================================
CREATE TABLE facility_doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    facility_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =============================================
-- PATIENTS TABLE
-- =============================================
CREATE TABLE patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    age INT,
    gender ENUM('male', 'female', 'other'),
    blood_group VARCHAR(5),
    allergies TEXT,
    chronic_conditions TEXT,
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- =============================================
-- ER TRIAGE TABLE (Voice symptom input)
-- =============================================
CREATE TABLE er_triage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    symptoms_text TEXT,
    audio_filename VARCHAR(255),
    severity ENUM('red', 'yellow', 'green') NOT NULL,
    predicted_condition VARCHAR(255),
    suggested_tests TEXT,
    triage_notes TEXT,
    triaged_by INT,
    facility_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE SET NULL,
    FOREIGN KEY (triaged_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE SET NULL
);

-- =============================================
-- DISEASE TIMELINE TABLE (Patient history events)
-- =============================================
CREATE TABLE disease_timeline (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    event_date DATE NOT NULL,
    event_type ENUM('symptom', 'diagnosis', 'test', 'prescription', 'procedure', 'hospitalization', 'note') NOT NULL,
    title VARCHAR(255),
    description TEXT,
    report_file_path VARCHAR(255),
    doctor_id INT,
    facility_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE SET NULL
);

-- =============================================
-- PRESCRIPTIONS TABLE
-- =============================================
CREATE TABLE prescriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    facility_id INT,
    diagnosis TEXT,
    drugs_json JSON,
    warnings_triggered BOOLEAN DEFAULT FALSE,
    warning_details TEXT,
    status ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
    prescribed_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE SET NULL
);

-- =============================================
-- DRUG INTERACTIONS REFERENCE TABLE
-- =============================================
CREATE TABLE drug_interactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    drug_a VARCHAR(100) NOT NULL,
    drug_b VARCHAR(100) NOT NULL,
    interaction_type ENUM('contraindicated', 'caution', 'minor') NOT NULL,
    severity ENUM('high', 'medium', 'low') NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- ALERTS & NOTIFICATIONS TABLE
-- =============================================
CREATE TABLE alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_type ENUM('outbreak', 'prescription_error', 'severe_case', 'system') NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    severity ENUM('red', 'yellow', 'green') DEFAULT 'yellow',
    region_city VARCHAR(100),
    region_state VARCHAR(100),
    facility_id INT,
    triggered_by INT,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE SET NULL,
    FOREIGN KEY (triggered_by) REFERENCES users(id) ON DELETE SET NULL
);

-- =============================================
-- USER NOTIFICATIONS (Links alerts to specific users)
-- =============================================
CREATE TABLE user_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    alert_id INT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE
);

-- =============================================
-- SAMPLE DATA: Drug Interactions
-- =============================================
INSERT INTO drug_interactions (drug_a, drug_b, interaction_type, severity, description) VALUES
('Warfarin', 'Aspirin', 'contraindicated', 'high', 'Increased risk of bleeding. Avoid combination.'),
('Ibuprofen', 'Lisinopril', 'caution', 'medium', 'NSAIDs may reduce antihypertensive effect of ACE inhibitors.'),
('Metformin', 'Contrast Dye', 'contraindicated', 'high', 'Risk of lactic acidosis. Stop Metformin 48 hours before contrast.'),
('Paracetamol', 'Alcohol', 'caution', 'high', 'Increased risk of liver damage with chronic alcohol use.'),
('Amoxicillin', 'Methotrexate', 'caution', 'medium', 'Penicillins may increase Methotrexate toxicity.'),
('Ciprofloxacin', 'Theophylline', 'caution', 'high', 'Increased Theophylline levels, risk of toxicity.'),
('Simvastatin', 'Grapefruit Juice', 'contraindicated', 'high', 'Grapefruit increases Simvastatin levels, risk of muscle damage.'),
('ACE Inhibitors', 'Potassium Supplements', 'contraindicated', 'high', 'Risk of hyperkalemia. Avoid combination.'),
('Clopidogrel', 'Omeprazole', 'caution', 'medium', 'Omeprazole may reduce Clopidogrel effectiveness.'),
('Lithium', 'NSAIDs', 'contraindicated', 'high', 'NSAIDs increase Lithium levels, risk of toxicity.');

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_patients_user_id ON patients(user_id);
CREATE INDEX idx_er_triage_severity ON er_triage(severity);
CREATE INDEX idx_er_triage_created ON er_triage(created_at);
CREATE INDEX idx_disease_timeline_patient ON disease_timeline(patient_id);
CREATE INDEX idx_prescriptions_patient ON prescriptions(patient_id);
CREATE INDEX idx_prescriptions_doctor ON prescriptions(doctor_id);
CREATE INDEX idx_alerts_type ON alerts(alert_type);
CREATE INDEX idx_alerts_region ON alerts(region_city, region_state);
CREATE INDEX idx_user_notifications_user ON user_notifications(user_id);
CREATE INDEX idx_user_notifications_read ON user_notifications(is_read);