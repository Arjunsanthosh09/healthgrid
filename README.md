# 🏥 HealthGrid — AI-Powered Community Health Intelligence Platform

![HealthGrid Banner](https://img.shields.io/badge/HealthGrid-v1.0-0b5e40)
![Python](https://img.shields.io/badge/Python-3.14-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-red)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![License](https://img.shields.io/badge/License-MIT-green)

> **One platform. ER triage, patient timelines, prescription safety, and outbreak detection — all connected.**

---

## 📖 Table of Contents
- [Problem Statement](#-problem-statement)
- [Solution](#-solution)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Database Setup](#-database-setup)
- [Usage](#-usage)
- [User Roles](#-user-roles)
- [Screenshots](#-screenshots)
- [Team](#-team)
- [Social Impact](#-social-impact)
- [Future Roadmap](#-future-roadmap)
- [License](#-license)

---

## 🚨 Problem Statement

Healthcare in developing nations operates in disconnected silos:

| Stakeholder | Challenge |
|-------------|-----------|
| **ER Departments** | Manual triage without AI severity scoring. Critical patients buried in queues. |
| **Doctors** | Years of patient history scattered across paper files. No unified timeline. Drug interactions missed. |
| **Health Departments** | Outbreaks detected days too late. No real-time symptom aggregation from clinics and hospitals. |

**Result:** Preventable deaths from medical errors (4th leading cause globally — WHO), delayed outbreak response, and inefficient resource allocation.

---

## 💡 Solution

**HealthGrid** connects ERs, doctors, and health departments on a single, privacy-first AI platform — requiring zero new hardware.

- 🎤 **Voice Triage:** ER patients describe symptoms. AI assigns severity (Red/Yellow/Green) and suggests tests in under 90 seconds.
- 📊 **Disease Timeline:** Doctors see years of blood tests, scans, and prescriptions in one visual timeline.
- 💊 **Prescription Safety:** AI checks every prescription for drug interactions, allergies, pregnancy risks, and organ issues.
- 🗺️ **Outbreak Detection:** Symptom clusters trigger real-time alerts to health department officers.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎤 Voice Symptom Triage | Speech-to-text → AI severity scoring → Test suggestions |
| 📊 Patient Disease Timeline | Visual timeline of all tests, diagnoses, and prescriptions |
| 💊 Prescription Error Checker | Drug interactions, allergies, pregnancy, kidney/liver safety |
| 🗺️ Outbreak Heat Maps | Real-time community health monitoring with AI alerts |
| 🔔 Real-Time Alerts | Severe cases alert on-duty doctors and health departments |
| 🏥 Hospital/Clinic Management | Admins add doctors, register ER departments, manage staff |
| 🔐 Role-Based Access | Super Admin → Hospital/Clinic Admin → Doctors → Health Officers |
| 📱 Offline-Ready | Pre-cached hospital data works without internet |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│                     HEALTHGRID                       │
├──────────────┬──────────────────┬───────────────────┤
│  ER MODULE   │  DOCTOR MODULE   │   HEALTH DEPT      │
│              │                  │   MODULE           │
├──────────────┴──────────────────┴───────────────────┤
│                    AUTH LAYER                         │
│         Flask-Login + Bcrypt + Role-Based Access      │
├─────────────────────────────────────────────────────┤
│                    AI ENGINE                          │
│   Speech-to-Text + Severity Prediction +              │
│   Drug Interaction Checker + Outbreak Detection       │
├─────────────────────────────────────────────────────┤
│                 DATABASE (MySQL)                      │
│  users | facilities | patients | er_triage |          │
│  disease_timeline | prescriptions | alerts            │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML5, CSS3, JavaScript, Jinja2, Chart.js |
| **Backend** | Python 3.14, Flask 3.0 |
| **Database** | MySQL 8.0 (PyMySQL) |
| **Authentication** | Flask-Login, Flask-Bcrypt |
| **Voice Processing** | SpeechRecognition (Google Speech API / PocketSphinx) |
| **AI/ML** | Scikit-learn, NLTK |
| **Maps** | Folium |
| **Deployment** | Local Flask Server (Docker/AWS planned) |

---

## ⚙️ Installation

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- pip

### Step 1: Clone the Repository
```bash
git clone https://github.com/arjunsanthosh/healthgrid.git
cd healthgrid
```

### Step 2: Create Virtual Environment
```bash
python -m venv env
env\Scripts\activate  # Windows
source env/bin/activate  # macOS/Linux
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Database
Edit `config.py` or set environment variables:

```python
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'your_password'
DB_NAME = 'healthgrid'
```

### Step 5: Run the Application
```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser.

---

## 🗄️ Database Setup

Run the SQL schema file to create all tables:

```bash
mysql -u root -p < database/schema.sql
```

Or import `database/schema.sql` via phpMyAdmin / MySQL Workbench.

**Key Tables:**
- `users` — All user accounts with roles
- `facilities` — Hospitals and clinics
- `patients` — Patient records
- `er_triage` — Voice triage records
- `disease_timeline` — Patient history events
- `prescriptions` — Prescriptions with warning flags
- `drug_interactions` — Known drug conflict database
- `alerts` — Outbreak and error alerts

---

## 🚀 Usage

### Default Admin Login
| Email | Password |
|-------|----------|
| admin@healthgrid.com | Set during setup |

### User Flows

**Hospital Registration:**
1. Visit `/register/hospital`
2. Fill hospital details and admin credentials
3. Wait for Super Admin approval
4. Login → Manage ER departments → Add doctors

**Clinic Registration:**
1. Visit `/register/clinic`
2. Fill clinic details and admin credentials
3. Wait for Super Admin approval
4. Login → Add clinic doctors

**Health Officer Registration:**
1. Visit `/register/user`
2. Fill personal and department details
3. Wait for Super Admin approval
4. Login → Access community health dashboard

**Doctors (Added by Admin):**
1. Receive credentials from Hospital/Clinic Admin
2. Login directly → Access ER triage or Doctor dashboard

---

## 👥 User Roles

| Role | Access | Dashboard |
|------|--------|-----------|
| Super Admin | Approve/reject facility registrations | `/admin/dashboard` |
| Hospital Admin | Manage ER departments, add/remove doctors | `/dashboard/hospital-admin` |
| Clinic Admin | Manage clinic, add/remove doctors | `/dashboard/clinic-admin` |
| ER Doctor | Voice triage, severity scoring | `/dashboard/er` |
| Hospital Doctor | Patient timeline, prescription checker | `/dashboard/doctor` |
| Clinic Doctor | Patient timeline, prescription checker | `/dashboard/doctor` |
| Health Officer | Community health map, outbreak alerts | `/dashboard/health-dept` |

---

## 📸 Screenshots

_Add screenshots here after deployment_

- Homepage with role selection
- Hospital registration form
- Admin dashboard with pending approvals
- Hospital management dashboard
- ER voice triage interface
- Patient disease timeline
- Community health heat map

---

## 👨‍💻 Team

| Name | Role | GitHub |
|------|------|--------|
| Arjun Santhosh | Team Lead & Full-Stack Developer | [@arjunsanthosh](https://github.com/arjunsanthosh) |
| Anjali Suresh | Frontend Developer & UI/UX Designer | [@anjalisuresh](https://github.com/anjalisuresh) |
| Karthika S Nair | AI/ML Engineer | [@karthikasnair](https://github.com/karthikasnair) |
| Gowtham Thulasi | Backend Developer & Database Manager | [@gowthamthulasi](https://github.com/gowthamthulasi) |
| Lakshmi Anil | Healthcare Domain Specialist | [@lakshmianil](https://github.com/lakshmianil) |

---

## 🌍 Social Impact

| SDG | Impact |
|-----|--------|
| SDG 3 — Good Health | Prevents medical errors, early outbreak detection, standardized triage |
| SDG 10 — Reduced Inequalities | Free tier for small clinics, offline support for rural areas |
| SDG 5 — Gender Equality | Pregnancy-safe prescription alerts, maternal health tracking |

- 🏥 Accessible to clinics without specialist ER doctors
- 📱 Works on basic smartphones — no expensive hardware
- 🌐 Functional with intermittent internet (offline caching)
- 🆓 Free tier for low-income community clinics

---

## 🔮 Future Roadmap

- [ ] WhatsApp Bot Integration — Submit symptoms via WhatsApp voice notes
- [ ] Multilingual Voice Support — Hindi, Tamil, Malayalam, Bengali
- [ ] Federated Learning — Train AI across hospitals without sharing patient data
- [ ] Mobile App — Native Android/iOS app with push notifications
- [ ] Ambulance Integration — Auto-dispatch nearest ambulance for Red cases
- [ ] Insurance Claim Automation — Pre-filled forms from patient timeline
- [ ] Telemedicine Bridge — Connect rural clinics to city specialists

---

## 📄 License

This project is licensed under the MIT License — see the `LICENSE` file for details.

---

## 🙏 Acknowledgments

- Flask and Python open-source communities
- WHO patient safety guidelines
- Ayushman Bharat Digital Mission for healthcare digitization inspiration
- All healthcare professionals who provided domain expertise

<p align="center"><b>Built with ❤️ for hackathon</b></p>
