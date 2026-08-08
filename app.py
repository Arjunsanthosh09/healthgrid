from flask import Flask, render_template, session, redirect, url_for, request, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from functools import wraps
from datetime import datetime
import pymysql
import os
import re
import json   

# =============================================
# APP SETUP
# =============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'app', 'templates'),
            static_folder=os.path.join(BASE_DIR, 'app', 'static'))

app.config['SECRET_KEY'] = 'your-secret-key-here'

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'healthgrid',
    'cursorclass': pymysql.cursors.DictCursor
}

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

# =============================================
# DATABASE HELPER
# =============================================
def get_db():
    """Get a new database connection."""
    return pymysql.connect(**DB_CONFIG)

# =============================================
# USER MODEL
# =============================================
class User(UserMixin):
    def __init__(self, id, full_name, email, role, er_department_id=None):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.role = role
        self.er_department_id = er_department_id

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, email, role, er_department_id FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        return User(
            id=user['id'],
            full_name=user['full_name'],
            email=user['email'],
            role=user['role'],
            er_department_id=user.get('er_department_id')
        )
    return None

# =============================================
# DECORATORS
# =============================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def approved_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role == 'admin':
            return f(*args, **kwargs)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM registration_requests WHERE email = %s AND status = 'approved'", 
                    (current_user.email,))
        approved = cur.fetchone()
        cur.close()
        conn.close()
        if not approved:
            flash('Your registration is pending approval.', 'warning')
            return redirect(url_for('pending_approval'))
        return f(*args, **kwargs)
    return decorated_function

# =============================================
# PUBLIC ROUTES
# =============================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pending-approval')
def pending_approval():
    return render_template('auth/pending_approval.html')

# =============================================
# AUTH ROUTES
# =============================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        print(f"DEBUG: Login attempt for {email}")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, full_name, email, password_hash, role FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        print(f"DEBUG: User found: {user is not None}")
        if user:
            print(f"DEBUG: User role from DB: '{user['role']}'")

        if user and bcrypt.check_password_hash(user['password_hash'], password):
            print(f"DEBUG: Password correct")
            
            if user['role'] != 'admin':
                conn = get_db()
                cur = conn.cursor()
                cur.execute("SELECT id FROM registration_requests WHERE email = %s AND status = 'approved'", (email,))
                approved = cur.fetchone()
                
                cur.close()
                conn.close()
                print(f"DEBUG: Registration approved: {approved is not None}")
                
                if not approved:
                    flash('Your registration has not been approved yet.', 'warning')
                    return redirect(url_for('pending_approval'))

            user_obj = User(id=user['id'], full_name=user['full_name'], email=user['email'], role=user['role'], er_department_id=user.get('er_department_id'))
            login_user(user_obj)
            flash(f'Welcome back, {user["full_name"]}!', 'success')

            role_redirects = {
                'admin': 'admin_dashboard',
                'er_doctor': 'er_dashboard',
                'hospital_admin': 'hospital_admin_dashboard',
                'hospital_doctor': 'doctor_dashboard',
                'clinic_admin': 'clinic_admin_dashboard',
                'clinic_doctor': 'doctor_dashboard',
                'health_officer': 'health_dept_dashboard',
                'patient': 'patient_dashboard'
            }
            
            redirect_to = role_redirects.get(user['role'], 'index')
            print(f"DEBUG: Redirecting to: {redirect_to}")
            return redirect(url_for(redirect_to))
        else:
            print(f"DEBUG: Invalid password or user not found")
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'patient')
        phone = request.form.get('phone')
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        cur.execute("SELECT id FROM registration_requests WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            flash('A registration request with this email already exists.', 'danger')
            return redirect(url_for('register'))

        cur.execute("""
            INSERT INTO registration_requests (full_name, email, password_hash, role, phone)
            VALUES (%s, %s, %s, %s, %s)
        """, (full_name, email, password_hash, role, phone))
        conn.commit()
        cur.close()
        conn.close()

        flash('Registration submitted. Please wait for admin approval.', 'success')
        return redirect(url_for('pending_approval'))

    return render_template('auth/register.html')

@app.route('/register/user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'health_officer')  # Always health_officer
        phone = request.form.get('phone')
        license_no = request.form.get('license_no')
        facility_name = request.form.get('facility_name')  # Department/Region
        agreement = request.form.get('agreement')

        if not agreement:
            flash('You must agree to the Terms and Privacy Policy.', 'danger')
            return redirect(url_for('register_user'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register_user'))

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('register_user'))

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            flash('Email already registered.', 'danger')
            return redirect(url_for('register_user'))

        cur.execute("""
            INSERT INTO registration_requests 
            (full_name, email, password_hash, role, facility_name, phone)
            VALUES (%s, %s, %s, 'health_officer', %s, %s)
        """, (full_name, email, password_hash, facility_name, phone))

        conn.commit()
        cur.close()
        conn.close()

        flash('Registration submitted. Please wait for admin approval.', 'success')
        return redirect(url_for('pending_approval'))

    return render_template('auth/register-user.html')

@app.route('/register/clinic', methods=['GET', 'POST'])
def register_clinic():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        facility_phone = request.form.get('facility_phone')
        facility_name = request.form.get('facility_name')
        license_no = request.form.get('license_no')
        specialty = request.form.get('specialty')
        facility_address = request.form.get('facility_address')
        facility_city = request.form.get('facility_city')
        facility_state = request.form.get('facility_state')
        facility_pincode = request.form.get('facility_pincode')
        agreement = request.form.get('agreement')

        # Validation
        if not agreement:
            flash('You must agree to the Terms and Data Processing Agreement.', 'danger')
            return redirect(url_for('register_clinic'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register_clinic'))

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('register_clinic'))

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db()
        cur = conn.cursor()

        # Check if email already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            flash('Email already registered.', 'danger')
            return redirect(url_for('register_clinic'))

        cur.execute("SELECT id FROM registration_requests WHERE email = %s AND status = 'pending'", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            flash('A pending registration request with this email already exists.', 'warning')
            return redirect(url_for('register_clinic'))

        # Insert into registration_requests (pending approval)
        cur.execute("""
    INSERT INTO registration_requests 
    (full_name, email, password_hash, role, facility_name, facility_type,
     facility_address, facility_city, facility_state, facility_pincode, facility_phone, phone)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (full_name, email, password_hash, 'clinic_admin', facility_name, 'clinic', 
      facility_address, facility_city, facility_state, facility_pincode, facility_phone, facility_phone))
        
        conn.commit()
        cur.close()
        conn.close()

        flash('Clinic registration submitted successfully. Please wait for admin approval.', 'success')
        return redirect(url_for('pending_approval'))

    return render_template('auth/register-clinic.html')

@app.route('/register/hospital', methods=['GET', 'POST'])
def register_hospital():
    if request.method == 'POST':
        print("=" * 50)
        print("DEBUG: Hospital registration form submitted")
        
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        facility_phone = request.form.get('facility_phone')
        facility_name = request.form.get('facility_name')
        license_no = request.form.get('license_no')
        bed_capacity = request.form.get('bed_capacity')
        facility_address = request.form.get('facility_address')
        facility_city = request.form.get('facility_city')
        facility_state = request.form.get('facility_state')
        facility_pincode = request.form.get('facility_pincode')
        departments = request.form.getlist('departments')
        agreement = request.form.get('agreement')

        print(f"DEBUG: full_name={full_name}, email={email}, facility_name={facility_name}")
        print(f"DEBUG: agreement={agreement}, password_match={password == confirm_password}")

        # Validation
        if not agreement:
            print("DEBUG: Agreement not checked - redirecting")
            flash('You must agree to the Terms and Data Processing Agreement.', 'danger')
            return redirect(url_for('register_hospital'))

        if password != confirm_password:
            print("DEBUG: Passwords don't match - redirecting")
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register_hospital'))

        if len(password) < 8:
            print("DEBUG: Password too short - redirecting")
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('register_hospital'))

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        print("DEBUG: Password hashed successfully")

        try:
            conn = get_db()
            cur = conn.cursor()
            print("DEBUG: Database connection successful")

            # Check if email already exists
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                print("DEBUG: Email already in users table")
                cur.close()
                conn.close()
                flash('Email already registered.', 'danger')
                return redirect(url_for('register_hospital'))

            cur.execute("SELECT id FROM registration_requests WHERE email = %s AND status = 'pending'", (email,))
            if cur.fetchone():
                print("DEBUG: Pending request already exists")
                cur.close()
                conn.close()
                flash('A pending registration request with this email already exists.', 'warning')
                return redirect(url_for('register_hospital'))

            # INSERT
            print("DEBUG: Attempting INSERT into registration_requests")
            cur.execute("""
    INSERT INTO registration_requests 
    (full_name, email, password_hash, role, facility_name, facility_type,
     facility_address, facility_city, facility_state, facility_pincode, facility_phone, phone)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (full_name, email, password_hash, 'hospital_admin', facility_name, 'hospital', 
      facility_address, facility_city, facility_state, facility_pincode, facility_phone, facility_phone))
            
            print(f"DEBUG: INSERT successful, rows affected: {cur.rowcount}")
            
            conn.commit()
            print("DEBUG: Commit successful")
            
            cur.close()
            conn.close()

            flash('Hospital registration submitted successfully. Please wait for admin approval.', 'success')
            return redirect(url_for('pending_approval'))

        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            flash(f'Database error: {str(e)}', 'danger')
            return redirect(url_for('register_hospital'))

    return render_template('auth/register-hospital.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# =============================================
# ADMIN ROUTES
# =============================================
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, full_name, email, role, facility_name, facility_type,
               facility_city, status, created_at
        FROM registration_requests
        ORDER BY status ASC, created_at DESC
    """)
    requests = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin/dashboard.html', requests=requests)

@app.route('/admin/approve/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def approve_registration(request_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM registration_requests WHERE id = %s", (request_id,))
    req = cur.fetchone()

    if not req:
        cur.close()
        conn.close()
        flash('Request not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Determine correct role with fallback
    role = req['role']
    if not role or role.strip() == '':
        if req['facility_type'] == 'hospital':
            role = 'hospital_admin'
        elif req['facility_type'] == 'clinic':
            role = 'clinic_admin'
        elif req['role'] == 'health_officer':
            role = 'health_officer'
        else:
            role = 'patient'

    # Insert into users table
    cur.execute("""
        INSERT INTO users (full_name, email, password_hash, role, phone)
        VALUES (%s, %s, %s, %s, %s)
    """, (req['full_name'], req['email'], req['password_hash'], role, req['phone']))
    user_id = cur.lastrowid

    # Create facility and link for hospital/clinic admins
    if role in ['clinic_admin', 'hospital_admin']:
        facility_type = 'hospital' if role == 'hospital_admin' else 'clinic'
        
        cur.execute("""
            INSERT INTO facilities (name, type, address, city, state, pincode, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (req['facility_name'], facility_type, req['facility_address'], 
              req['facility_city'], req['facility_state'], req['facility_pincode'], req['facility_phone']))
        facility_id = cur.lastrowid
        
        cur.execute("""
            INSERT INTO facility_doctors (facility_id, user_id)
            VALUES (%s, %s)
        """, (facility_id, user_id))

    # Update registration status
    cur.execute("""
        UPDATE registration_requests
        SET status = 'approved', reviewed_by = %s, reviewed_at = NOW()
        WHERE id = %s
    """, (current_user.id, request_id))
    
    conn.commit()
    cur.close()
    conn.close()

    flash(f'Registration for {req["full_name"]} approved successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reject/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def reject_registration(request_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE registration_requests
        SET status = 'rejected', reviewed_by = %s, reviewed_at = NOW()
        WHERE id = %s
    """, (current_user.id, request_id))
    conn.commit()
    cur.close()
    conn.close()

    flash('Registration rejected.', 'warning')
    return redirect(url_for('admin_dashboard'))

# =============================================
# DASHBOARD ROUTES
# =============================================


@app.route('/dashboard/patient')
@login_required
@approved_required
def patient_dashboard():
    return render_template('patient/dashboard.html')

# =============================================
# FEATURE ROUTES
# =============================================
@app.route('/doctor/patient-timeline', methods=['GET', 'POST'])
@login_required
@approved_required
def patient_timeline():
    if current_user.role not in ['hospital_doctor', 'clinic_doctor']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    timeline_data = []
    patient = None
    risk_prediction = None
    
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        patient = cur.fetchone()
        
        if patient:
            cur.execute("""
                SELECT event_date, event_type, title, description, report_file_path
                FROM disease_timeline WHERE patient_id = %s ORDER BY event_date ASC
            """, (patient['id'],))
            timeline_data = cur.fetchall()
            
            # 🔥 AI-POWERED RISK PREDICTION
            from app.er.groq_utils import predict_health_risks_with_ai
            risk_prediction = predict_health_risks_with_ai(patient, timeline_data)
        
        cur.close()
        conn.close()
    
    return render_template('doctor/patient_timeline.html',
                         patient=patient, timeline_data=timeline_data,
                         risk_prediction=risk_prediction)


# =============================================
# ERROR HANDLERS
# =============================================
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500
@app.route('/dashboard/hospital-admin')
@login_required
@approved_required
def hospital_admin_dashboard():
    if current_user.role not in ['hospital_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get hospital info
    cur.execute("""
        SELECT f.id, f.name, f.address, f.city, f.state, f.phone
        FROM facilities f
        JOIN facility_doctors fd ON f.id = fd.facility_id
        WHERE fd.user_id = %s AND f.type = 'hospital'
    """, (current_user.id,))
    facility = cur.fetchone()
    
    # If no facility linked, show error
    if not facility:
        cur.close()
        conn.close()
        flash('No hospital linked to your account. Please contact super admin.', 'danger')
        return render_template('hospital/admin_dashboard.html', 
                             facility=None, 
                             er_departments=[], 
                             doctors=[])
    
    # Get ER departments
    cur.execute("""
        SELECT ed.id, ed.name, ed.bed_capacity, ed.current_occupancy, ed.contact_phone,
               ed.is_active, ed.created_at, u.full_name as head_doctor
        FROM er_departments ed
        LEFT JOIN users u ON ed.head_doctor_id = u.id
        WHERE ed.facility_id = %s
        ORDER BY ed.created_at DESC
    """, (facility['id'],))
    er_departments = cur.fetchall()
    
    # Get all doctors
    cur.execute("""
        SELECT u.id, u.full_name, u.email, u.role, u.phone, u.created_at,
               ed.name as er_dept_name
        FROM users u
        JOIN facility_doctors fd ON u.id = fd.user_id
        LEFT JOIN er_departments ed ON u.er_department_id = ed.id
        WHERE fd.facility_id = %s AND u.role IN ('er_doctor', 'hospital_doctor')
        ORDER BY u.created_at DESC
    """, (facility['id'],))
    doctors = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('hospital/admin_dashboard.html', 
                         facility=facility, 
                         er_departments=er_departments if er_departments else [], 
                         doctors=doctors if doctors else [])


# HOSPITAL ADMIN - REGISTER ER DEPARTMENT


@app.route('/hospital/add-er-department', methods=['POST'])
@login_required
@approved_required
def hospital_add_er_department():
    if current_user.role not in ['hospital_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    bed_capacity = request.form.get('bed_capacity', 0)
    contact_phone = request.form.get('contact_phone')
    
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT f.id, f.name FROM facilities f
        JOIN facility_doctors fd ON f.id = fd.facility_id
        WHERE fd.user_id = %s AND f.type = 'hospital'
    """, (current_user.id,))
    facility = cur.fetchone()
    
    cur.execute("SELECT id FROM er_departments WHERE email = %s", (email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        flash('Email already used by another ER department.', 'danger')
        return redirect(url_for('hospital_admin_dashboard'))
    
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        flash('Email already registered.', 'danger')
        return redirect(url_for('hospital_admin_dashboard'))

    cur.execute("""
        INSERT INTO er_departments (facility_id, name, email, password_hash, bed_capacity, contact_phone)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (facility['id'], name, email, password_hash, bed_capacity, contact_phone))
    er_dept_id = cur.lastrowid

    cur.execute("""
        INSERT INTO users (full_name, email, password_hash, role, phone, er_department_id)
        VALUES (%s, %s, %s, 'er_doctor', %s, %s)
    """, (name, email, password_hash, contact_phone, er_dept_id))
    user_id = cur.lastrowid

    cur.execute("""
        INSERT INTO facility_doctors (facility_id, user_id)
        VALUES (%s, %s)
    """, (facility['id'], user_id))
    cur.execute("""
        INSERT INTO registration_requests 
        (full_name, email, password_hash, role, facility_name, status, reviewed_by, reviewed_at)
        VALUES (%s, %s, %s, 'er_doctor', %s, 'approved', %s, NOW())
    """, (name, email, password_hash, facility['name'], current_user.id))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash(f'ER Department "{name}" registered! Staff can log in with {email}', 'success')
    return redirect(url_for('hospital_admin_dashboard'))

# =============================================
# HOSPITAL ADMIN - ADD DOCTOR
# =============================================
@app.route('/hospital/add-doctor', methods=['POST'])
@login_required
@approved_required
def hospital_add_doctor():
    if current_user.role not in ['hospital_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    role = request.form.get('role')
    password = request.form.get('password')
    specialty = request.form.get('specialty', '')
    er_department_id = request.form.get('er_department_id')  # Only for ER doctors
    
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Check email
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        flash('Email already exists.', 'danger')
        return redirect(url_for('hospital_admin_dashboard'))
    
    # Get facility
    cur.execute("""
        SELECT f.id, f.name FROM facilities f
        JOIN facility_doctors fd ON f.id = fd.facility_id
        WHERE fd.user_id = %s AND f.type = 'hospital'
    """, (current_user.id,))
    facility = cur.fetchone()
    
    # Insert user
    cur.execute("""
        INSERT INTO users (full_name, email, password_hash, role, phone, er_department_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (full_name, email, password_hash, role, phone, 
          er_department_id if er_department_id else None))
    user_id = cur.lastrowid
    
    # Link to facility
    cur.execute("""
        INSERT INTO facility_doctors (facility_id, user_id)
        VALUES (%s, %s)
    """, (facility['id'], user_id))
    
    # Auto-approve registration record
    cur.execute("""
        INSERT INTO registration_requests 
        (full_name, email, password_hash, role, facility_name, status, reviewed_by, reviewed_at)
        VALUES (%s, %s, %s, %s, %s, 'approved', %s, NOW())
    """, (full_name, email, password_hash, role, facility['name'], current_user.id))
    
    # If ER doctor, update ER department head if needed
    if role == 'er_doctor' and er_department_id:
        cur.execute("""
            UPDATE er_departments 
            SET head_doctor_id = %s 
            WHERE id = %s AND head_doctor_id IS NULL
        """, (user_id, er_department_id))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash(f'{full_name} added successfully! They can log in immediately.', 'success')
    return redirect(url_for('hospital_admin_dashboard'))

# =============================================
# HOSPITAL ADMIN - REMOVE DOCTOR
# =============================================
@app.route('/hospital/remove-doctor/<int:doctor_id>', methods=['POST'])
@login_required
@approved_required
def hospital_remove_doctor(doctor_id):
    if current_user.role not in ['hospital_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Verify permission
    cur.execute("""
        SELECT fd.id FROM facility_doctors fd
        JOIN facilities f ON fd.facility_id = f.id
        JOIN facility_doctors fd2 ON f.id = fd2.facility_id
        WHERE fd2.user_id = %s AND fd.user_id = %s AND f.type = 'hospital'
    """, (current_user.id, doctor_id))
    
    if cur.fetchone():
        cur.execute("DELETE FROM facility_doctors WHERE user_id = %s", (doctor_id,))
        cur.execute("DELETE FROM users WHERE id = %s AND role IN ('er_doctor', 'hospital_doctor')", (doctor_id,))
        conn.commit()
        flash('Doctor removed successfully.', 'success')
    else:
        flash('Permission denied.', 'danger')
    
    cur.close()
    conn.close()
    return redirect(url_for('hospital_admin_dashboard'))

# =============================================
# ER TRIAGE ROUTES
# =============================================
@app.route('/er/triage', methods=['GET', 'POST'])
@login_required
@approved_required
def triage():
    if current_user.role not in ['er_doctor']:
        flash('Access denied. ER staff only.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        patient_name = request.form.get('patient_name')
        patient_age = request.form.get('patient_age')
        patient_gender = request.form.get('patient_gender')
        symptoms_text = request.form.get('symptoms_text', '')
        
        # Handle voice input
        audio_filename = None
        if 'audio_file' in request.files:
            audio_file = request.files['audio_file']
            if audio_file.filename != '':
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                audio_filename = f"er_audio_{timestamp}_{current_user.id}.wav"
                audio_path = os.path.join(app.static_folder, 'uploads', audio_filename)
                audio_file.save(audio_path)
                
                # Transcribe audio
                from app.er.utils import transcribe_audio
                transcribed_text, error = transcribe_audio(audio_path)
                
                if error:
                    flash(f'Voice recognition error: {error}', 'warning')
                elif transcribed_text:
                    symptoms_text = transcribed_text
                    flash(f'Transcribed: "{transcribed_text}"', 'info')
        
        if symptoms_text:
            # 🔥 HYBRID APPROACH: Try Groq AI first, fallback to rule-based
            from app.er.groq_utils import analyze_symptoms_hybrid
            
            result = analyze_symptoms_hybrid(
                symptoms_text,
                patient_name=patient_name,
                patient_age=patient_age,
                patient_gender=patient_gender
            )
            
            # Get ER department info
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT ed.id, ed.name, f.id as facility_id
                FROM er_departments ed
                JOIN facilities f ON ed.facility_id = f.id
                WHERE ed.id = %s
            """, (current_user.er_department_id,))
            er_dept = cur.fetchone()
            
            # Save to database
            cur.execute("""
                INSERT INTO er_triage 
                (patient_id, symptoms_text, audio_filename, severity, predicted_condition, 
                 suggested_tests, triaged_by, facility_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                None,
                symptoms_text,
                audio_filename,
                result.get('severity', 'green'),
                ', '.join(result.get('predicted_conditions', [])),
                ', '.join(result.get('suggested_tests', [])),
                current_user.id,
                er_dept['facility_id'] if er_dept else None
            ))
            
            triage_id = cur.lastrowid
            
            # Create alert for severe cases
            if result.get('severity') == 'red':
                cur.execute("""
                    INSERT INTO alerts 
                    (alert_type, title, message, severity, facility_id, triggered_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    'severe_case',
                    f'🚨 CRITICAL CASE - {er_dept["name"] if er_dept else "ER"}',
                    f'Triage ID: {triage_id}\n'
                    f'Patient: {patient_name or "Unknown"}\n'
                    f'Age: {patient_age or "N/A"} | Gender: {patient_gender or "N/A"}\n'
                    f'Severity: CRITICAL\n'
                    f'Conditions: {", ".join(result.get("predicted_conditions", []))}\n'
                    f'Immediate Actions: {", ".join(result.get("immediate_actions", []))}',
                    'red',
                    er_dept['facility_id'] if er_dept else None,
                    current_user.id
                ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            # Store result in session
            session['triage_result'] = result
            session['patient_name'] = patient_name
            session['patient_age'] = patient_age
            session['patient_gender'] = patient_gender
            session['triage_id'] = triage_id
            
            return redirect(url_for('er_result'))
        
        else:
            flash('Please enter symptoms or record voice.', 'warning')
    
    return render_template('er/triage.html')

@app.route('/er/result')
@login_required
@approved_required
def er_result():
    if current_user.role not in ['er_doctor']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    result = session.get('triage_result', {})
    patient_name = session.get('patient_name', 'Unknown')
    patient_age = session.get('patient_age', 'N/A')
    patient_gender = session.get('patient_gender', 'N/A')
    
    if not result:
        flash('No triage result found.', 'warning')
        return redirect(url_for('triage'))
    
    return render_template('er/result.html',
                         result=result,
                         patient_name=patient_name,
                         patient_age=patient_age,
                         patient_gender=patient_gender)
    

@app.route('/dashboard/er')
@login_required
@approved_required
def er_dashboard():
    if current_user.role not in ['er_doctor']:
        flash('Access denied. ER staff only.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get today's triage records for this ER department
    cur.execute("""
        SELECT et.id, et.symptoms_text, et.severity, et.predicted_condition,
               et.suggested_tests, et.created_at, et.triage_notes,
               p.full_name as patient_name
        FROM er_triage et
        LEFT JOIN patients p ON et.patient_id = p.id
        WHERE et.triaged_by = %s 
        AND DATE(et.created_at) = CURDATE()
        ORDER BY 
            CASE et.severity 
                WHEN 'red' THEN 1 
                WHEN 'yellow' THEN 2 
                WHEN 'green' THEN 3 
            END,
            et.created_at DESC
    """, (current_user.id,))
    triage_list = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('er/dashboard.html', triage_list=triage_list if triage_list else [])
   
# =============================================
# HOSPITAL ADMIN - REGISTER PATIENT
# =============================================
@app.route('/hospital/add-patient', methods=['POST'])
@login_required
@approved_required
def hospital_add_patient():
    if current_user.role not in ['hospital_admin', 'clinic_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    password = request.form.get('password', 'Patient@123')
    phone = request.form.get('phone')
    age = request.form.get('age')
    gender = request.form.get('gender')
    blood_group = request.form.get('blood_group')
    allergies = request.form.get('allergies')
    chronic_conditions = request.form.get('chronic_conditions')
    emergency_contact_name = request.form.get('emergency_contact_name')
    emergency_contact_phone = request.form.get('emergency_contact_phone')
    assigned_doctor_id = request.form.get('assigned_doctor_id')
    
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Check email unique
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        flash('Email already registered.', 'danger')
        return redirect(url_for('hospital_admin_dashboard'))
    
    # Insert into users
    cur.execute("""
        INSERT INTO users (full_name, email, password_hash, role, phone)
        VALUES (%s, %s, %s, 'patient', %s)
    """, (full_name, email, password_hash, phone))
    user_id = cur.lastrowid
    
    # Insert into patients
    cur.execute("""
        INSERT INTO patients 
        (user_id, full_name, age, gender, blood_group, allergies, chronic_conditions,
         emergency_contact_name, emergency_contact_phone)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (user_id, full_name, age, gender, blood_group, allergies, chronic_conditions,
          emergency_contact_name, emergency_contact_phone))
    patient_id = cur.lastrowid
    
    # Get facility ID
    # Get facility ID and name
    cur.execute("""
    SELECT f.id, f.name FROM facilities f
    JOIN facility_doctors fd ON f.id = fd.facility_id
    WHERE fd.user_id = %s
    """, (current_user.id,))
    facility = cur.fetchone()
    
    # Link patient to facility
    if facility:
        cur.execute("""
            INSERT INTO facility_doctors (facility_id, user_id)
            VALUES (%s, %s)
        """, (facility['id'], user_id))
    
    # Assign doctor if selected
    if assigned_doctor_id:
        cur.execute("""
            INSERT INTO doctor_patient_assignments (doctor_id, patient_id, assigned_date)
            VALUES (%s, %s, CURDATE())
        """, (assigned_doctor_id, patient_id))
    
    # Auto-approve registration
    facility_name = facility.get('name') if facility else 'Hospital'

    cur.execute("""
    INSERT INTO registration_requests 
    (full_name, email, password_hash, role, facility_name, status, reviewed_by, reviewed_at)
    VALUES (%s, %s, %s, 'patient', %s, 'approved', %s, NOW())
""", (full_name, email, password_hash, facility_name, current_user.id))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash(f'Patient {full_name} registered successfully! Login: {email} / {password}', 'success')
    return redirect(url_for('hospital_admin_dashboard'))


# =============================================
# ASSIGN DOCTOR TO PATIENT
# =============================================
@app.route('/hospital/assign-doctor', methods=['POST'])
@login_required
@approved_required
def assign_doctor_to_patient():
    if current_user.role not in ['hospital_admin', 'clinic_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    patient_id = request.form.get('patient_id')
    doctor_id = request.form.get('doctor_id')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Check if already assigned
    cur.execute("""
        SELECT id FROM doctor_patient_assignments 
        WHERE doctor_id = %s AND patient_id = %s AND status = 'active'
    """, (doctor_id, patient_id))
    
    if cur.fetchone():
        flash('Doctor already assigned to this patient.', 'warning')
    else:
        cur.execute("""
            INSERT INTO doctor_patient_assignments (doctor_id, patient_id, assigned_date)
            VALUES (%s, %s, CURDATE())
        """, (doctor_id, patient_id))
        conn.commit()
        flash('Doctor assigned successfully!', 'success')
    
    cur.close()
    conn.close()
    return redirect(url_for('hospital_admin_dashboard'))

@app.route('/dashboard/doctor')
@login_required
@approved_required
def doctor_dashboard():
    if current_user.role not in ['hospital_doctor', 'clinic_doctor']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get assigned patients
    cur.execute("""
        SELECT p.id, p.full_name, p.age, p.gender, p.blood_group, p.allergies,
               p.chronic_conditions, dpa.assigned_date
        FROM patients p
        JOIN doctor_patient_assignments dpa ON p.id = dpa.patient_id
        WHERE dpa.doctor_id = %s AND dpa.status = 'active'
        ORDER BY dpa.assigned_date DESC
    """, (current_user.id,))
    patients = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('doctor/dashboard.html', patients=patients if patients else [])

# =============================================
# DOCTOR - PRESCRIPTION SAFETY CHECKER
# =============================================
@app.route('/doctor/prescription-check', methods=['GET', 'POST'])
@login_required
@approved_required
def prescription_check():
    if current_user.role not in ['hospital_doctor', 'clinic_doctor']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    warnings = []
    patient = None
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get assigned patients — exclude ones already prescribed today
    cur.execute("""
        SELECT p.id, p.full_name, p.age, p.gender, p.blood_group, p.allergies, p.chronic_conditions
        FROM patients p
        JOIN doctor_patient_assignments dpa ON p.id = dpa.patient_id
        WHERE dpa.doctor_id = %s AND dpa.status = 'active'
        AND p.id NOT IN (
            SELECT patient_id FROM prescriptions 
            WHERE doctor_id = %s AND prescribed_date = CURDATE()
        )
        ORDER BY p.full_name
    """, (current_user.id, current_user.id))
    assigned_patients = cur.fetchall()
    
    # Get today's completed prescriptions
    cur.execute("""
        SELECT p.id, p.full_name, pr.drugs_json, pr.diagnosis, pr.prescribed_date
        FROM prescriptions pr
        JOIN patients p ON pr.patient_id = p.id
        WHERE pr.doctor_id = %s AND pr.prescribed_date = CURDATE()
        ORDER BY pr.prescribed_date DESC
    """, (current_user.id,))
    completed_today = cur.fetchall()
    
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        drug_name = request.form.get('drug_name', '')
        dosage = request.form.get('dosage', '')
        
        # 🔴 OVERDOSE CHECK
        if dosage:
            nums = re.findall(r'[\d.]+', dosage)
            if nums:
                d = float(nums[0])
                max_dosages = {
                    'warfarin': 10, 'paracetamol': 4000, 'ibuprofen': 3200,
                    'aspirin': 4000, 'metformin': 2550, 'diclofenac': 150,
                }
                drug_lower = drug_name.lower().strip()
                if drug_lower in max_dosages and d > max_dosages[drug_lower]:
                    warnings.append({
                        'type': 'danger',
                        'message': f'🚨 FATAL OVERDOSE: {d}mg exceeds max {max_dosages[drug_lower]}mg for {drug_name}!'
                    })
                if d > 10000:
                    warnings.append({
                        'type': 'danger',
                        'message': f'🚨 EXTREME OVERDOSE: {d}mg is dangerously high!'
                    })
        
        cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        patient = cur.fetchone()
        
        if patient:
            # Past prescriptions
            cur.execute("""
                SELECT drugs_json, diagnosis, prescribed_date 
                FROM prescriptions WHERE patient_id = %s 
                ORDER BY prescribed_date DESC LIMIT 5
            """, (patient_id,))
            past_prescriptions = cur.fetchall()
            
            # Allergy check
            if patient.get('allergies') and drug_name.lower() in patient['allergies'].lower():
                warnings.append({
                    'type': 'danger',
                    'message': f'⚠️ ALLERGY ALERT: Patient is allergic to {drug_name}!'
                })
            
            # Pregnancy check
            if drug_name.lower() in ['isotretinoin', 'thalidomide', 'warfarin', 'valproate']:
                warnings.append({
                    'type': 'warning',
                    'message': f'⚠️ PREGNANCY RISK: {drug_name} is contraindicated in pregnancy.'
                })
            
            # Kidney/liver check
            if drug_name.lower() in ['ibuprofen', 'naproxen', 'diclofenac', 'gentamicin']:
                warnings.append({
                    'type': 'warning',
                    'message': f'⚠️ KIDNEY RISK: {drug_name} may affect kidney function.'
                })
            
            # Drug interactions
            cur.execute("SELECT * FROM drug_interactions WHERE drug_a = %s OR drug_b = %s", (drug_name, drug_name))
            for interaction in cur.fetchall():
                warnings.append({
                    'type': 'danger' if interaction['severity'] == 'high' else 'warning',
                    'message': f'⚠️ INTERACTION: {interaction["drug_a"]} + {interaction["drug_b"]} — {interaction["description"]}'
                })
            
            # Duplicate check
            for presc in past_prescriptions:
                if presc['drugs_json'] and drug_name.lower() in str(presc['drugs_json']).lower():
                    warnings.append({
                        'type': 'warning',
                        'message': f'⚠️ DUPLICATE: Already prescribed on {presc["prescribed_date"]}'
                    })
            
            # 🤖 AI check with full history
            try:
                from app.er.groq_utils import check_prescription_with_ai
                ai_result = check_prescription_with_ai(patient, drug_name, dosage)
                if ai_result:
                    if not ai_result.get('safe', True):
                        for w in ai_result.get('warnings', []):
                            warnings.append({
                                'type': 'danger' if w.get('severity') == 'high' else 'warning',
                                'message': f"🤖 AI: {w['message']}"
                            })
                    if ai_result.get('alternative_suggestions'):
                        for alt in ai_result['alternative_suggestions']:
                            warnings.append({
                                'type': 'info',
                                'message': f"💡 Alternative: {alt}"
                            })
            except Exception as e:
                print(f"AI check skipped: {e}")
        
        if not warnings:
            flash('✅ No safety concerns detected.', 'success')
    
    cur.close()
    conn.close()
    
    return render_template('doctor/prescription_check.html', 
                         warnings=warnings, patient=patient,
                         assigned_patients=assigned_patients,
                         completed_today=completed_today)


@app.route('/doctor/save-prescription', methods=['POST'])
@login_required
@approved_required
def save_prescription():
    if current_user.role not in ['hospital_doctor', 'clinic_doctor']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    patient_id = request.form.get('patient_id')
    drug_name = request.form.get('drug_name')
    dosage = request.form.get('dosage')
    frequency = request.form.get('frequency')
    duration = request.form.get('duration')
    diagnosis = request.form.get('diagnosis')
    
    drugs_json = json.dumps([{
        'name': drug_name,
        'dosage': dosage,
        'frequency': frequency,
        'duration': duration
    }])
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO prescriptions 
        (patient_id, doctor_id, diagnosis, drugs_json, prescribed_date)
        VALUES (%s, %s, %s, %s, CURDATE())
    """, (patient_id, current_user.id, diagnosis, drugs_json))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash('✅ Prescription saved successfully!', 'success')
    return redirect(url_for('prescription_check'))

# =============================================
# HEALTH DEPARTMENT - ZONE WATCH (Outbreak Detection)
# =============================================
@app.route('/health-dept/report')
@login_required
@approved_required
def health_report():
    if current_user.role not in ['health_officer']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Cluster symptoms across facilities
    cur.execute("""
        SELECT 
            et.severity,
            et.predicted_condition,
            et.symptoms_text,
            f.city,
            f.state,
            COUNT(*) as case_count,
            MAX(et.created_at) as latest_case
        FROM er_triage et
        JOIN facilities f ON et.facility_id = f.id
        WHERE et.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY et.predicted_condition, f.city, f.state
        HAVING case_count >= 2
        ORDER BY case_count DESC
    """)
    clusters = cur.fetchall()
    
    # Active alerts
    cur.execute("""
        SELECT * FROM alerts 
        WHERE alert_type IN ('outbreak', 'severe_case')
        ORDER BY created_at DESC LIMIT 10
    """)
    alerts = cur.fetchall()
    
    # City-wise stats
    cur.execute("""
        SELECT f.city, f.state, COUNT(*) as total_cases,
               SUM(CASE WHEN et.severity = 'red' THEN 1 ELSE 0 END) as critical,
               SUM(CASE WHEN et.severity = 'yellow' THEN 1 ELSE 0 END) as urgent
        FROM er_triage et
        JOIN facilities f ON et.facility_id = f.id
        WHERE et.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY f.city, f.state
        ORDER BY total_cases DESC
    """)
    city_stats = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # 🔥 AI OUTBREAK DETECTION
    ai_analysis = None
    try:
        from app.er.groq_utils import detect_outbreaks_with_ai
        ai_analysis = detect_outbreaks_with_ai(clusters)
    except Exception as e:
        print(f"AI outbreak detection skipped: {e}")
    
    return render_template('health_dept/report.html',
                         clusters=clusters,
                         alerts=alerts,
                         city_stats=city_stats,
                         ai_analysis=ai_analysis)

@app.route('/dashboard/health-dept')
@login_required
@approved_required
def health_dept_dashboard():
    if current_user.role not in ['health_officer']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Quick stats
    cur.execute("SELECT COUNT(*) as total FROM er_triage WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
    total_week = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as critical FROM er_triage WHERE severity = 'red' AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
    critical = cur.fetchone()['critical']
    
    cur.execute("SELECT COUNT(*) as facilities FROM facilities")
    total_facilities = cur.fetchone()['facilities']
    
    # Get symptom clusters for AI analysis
    cur.execute("""
        SELECT et.predicted_condition, f.city, f.state, COUNT(*) as case_count,
               MAX(et.created_at) as latest_case
        FROM er_triage et 
        JOIN facilities f ON et.facility_id = f.id
        WHERE et.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY et.predicted_condition, f.city, f.state 
        HAVING case_count >= 1
        ORDER BY case_count DESC
    """)
    clusters = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # 🔥 AI OUTBREAK DETECTION
    ai_analysis = None
    try:
        from app.er.groq_utils import detect_outbreaks_with_ai
        ai_analysis = detect_outbreaks_with_ai(clusters)
    except Exception as e:
        print(f"AI outbreak detection skipped: {e}")
    
    return render_template('health_dept/dashboard.html',
                         total_week=total_week,
                         critical=critical,
                         total_facilities=total_facilities,
                         clusters=clusters,
                         ai_analysis=ai_analysis)

@app.route('/doctor/add-timeline-event', methods=['POST'])
@login_required
@approved_required
def add_timeline_event():
    if current_user.role not in ['hospital_doctor', 'clinic_doctor']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    patient_id = request.form.get('patient_id')
    event_date = request.form.get('event_date')
    event_type = request.form.get('event_type')
    title = request.form.get('title')
    description = request.form.get('description')
    
    report_file_path = None
    if 'report_file' in request.files:
        file = request.files['report_file']
        if file.filename != '':
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"report_{timestamp}_{patient_id}.pdf"
            file_path = os.path.join(app.static_folder, 'uploads', filename)
            file.save(file_path)
            report_file_path = filename
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO disease_timeline 
        (patient_id, event_date, event_type, title, description, report_file_path, doctor_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (patient_id, event_date, event_type, title, description, report_file_path, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Timeline event added!', 'success')
    return redirect(url_for('patient_timeline'))

if __name__ == '__main__':
    app.run(debug=True)