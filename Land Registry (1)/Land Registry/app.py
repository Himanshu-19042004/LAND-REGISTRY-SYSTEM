from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def get_db_connection():
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Helper to check if user is logged in
def is_logged_in():
    return 'user_id' in session

# Helper to check if user is admin
def is_admin():
    return session.get('role') == 'admin'

# Context processor to inject user details to templates
@app.context_processor
def inject_user():
    return dict(
        logged_in=is_logged_in(),
        username=session.get('username'),
        role=session.get('role'),
        full_name=session.get('full_name')
    )

# HOME PAGE
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch general statistics for stats counter cards
    stats = {}
    try:
        stats['total_records'] = cursor.execute('SELECT COUNT(*) FROM land_records').fetchone()[0]
        stats['total_area'] = cursor.execute('SELECT SUM(area) FROM land_records').fetchone()[0] or 0.0
        stats['total_value'] = cursor.execute('SELECT SUM(market_value) FROM land_records').fetchone()[0] or 0.0
        stats['verified_count'] = cursor.execute("SELECT COUNT(*) FROM land_records WHERE registry_status = 'Verified'").fetchone()[0]
        stats['pending_count'] = cursor.execute("SELECT COUNT(*) FROM land_records WHERE registry_status = 'Pending'").fetchone()[0]
        stats['disputed_count'] = cursor.execute("SELECT COUNT(*) FROM land_records WHERE registry_status = 'Disputed'").fetchone()[0]
        
        # Format total area and value nicely
        stats['total_area'] = round(stats['total_area'], 2)
        stats['total_value_cr'] = round(stats['total_value'] / 10000000.0, 2)  # Convert to Crores
    except sqlite3.Error as e:
        print("Database error:", e)
        stats = {
            'total_records': 0, 'total_area': 0.0, 'total_value_cr': 0.0,
            'verified_count': 0, 'pending_count': 0, 'disputed_count': 0
        }
    
    # Fetch 5 most recent records
    recent_records = []
    try:
        recent_records = cursor.execute('SELECT * FROM land_records ORDER BY id DESC LIMIT 5').fetchall()
    except sqlite3.Error as e:
        print("Database error:", e)
        
    conn.close()
    return render_template('index.html', stats=stats, recent_records=recent_records)

# SEARCH PAGE
@app.route('/search', methods=['GET'])
def search():
    owner = request.args.get('owner', '').strip()
    khasra = request.args.get('khasra', '').strip()
    khata = request.args.get('khata', '').strip()
    location = request.args.get('location', '').strip()
    status = request.args.get('status', '').strip()
    
    query = 'SELECT * FROM land_records WHERE 1=1'
    params = []
    
    if owner:
        query += ' AND owner_name LIKE ?'
        params.append(f'%{owner}%')
    if khasra:
        query += ' AND khasra_number LIKE ?'
        params.append(f'%{khasra}%')
    if khata:
        query += ' AND khata_number LIKE ?'
        params.append(f'%{khata}%')
    if location:
        query += ' AND (village LIKE ? OR district LIKE ?)'
        params.append(f'%{location}%')
        params.append(f'%{location}%')
    if status:
        query += ' AND registry_status = ?'
        params.append(status)
        
    conn = get_db_connection()
    records = []
    try:
        records = conn.execute(query, params).fetchall()
        print(f"Search Query: {query} | Params: {params} | Found {len(records)} records")
    except sqlite3.Error as e:
        print(f"Search Error: {e}")
        flash(f"Database error during search: {e}", "danger")
    
    # Get all distinct villages/districts for filters list
    districts = []
    try:
        districts = [row[0] for row in conn.execute('SELECT DISTINCT district FROM land_records').fetchall()]
    except sqlite3.Error:
        pass
        
    conn.close()
    
    return render_template('search.html', 
                           records=records, 
                           districts=districts,
                           filters={
                               'owner': owner,
                               'khasra': khasra,
                               'khata': khata,
                               'location': location,
                               'status': status
                           })

# GET RECORD BY ID (AJAX detail view)
@app.route('/record/<int:record_id>', methods=['GET'])
def get_record(record_id):
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM land_records WHERE id = ?', (record_id,)).fetchone()
    conn.close()
    if record:
        return jsonify(dict(record))
    return jsonify({'error': 'Record not found'}), 404

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            flash(f"Welcome back, {user['full_name']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('login.html')

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        role = request.form.get('role', 'user') # 'user' or 'admin'
        
        if not username or not password or not full_name or not email:
            flash('All fields are required.', 'warning')
            return render_template('register.html')
            
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO users (username, password, role, full_name, email)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, hashed_password, role, full_name, email))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another.', 'danger')
        except sqlite3.Error as e:
            flash(f'An error occurred: {e}', 'danger')
        finally:
            conn.close()
            
    return render_template('register.html')

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    flash('You have logged out successfully.', 'info')
    return redirect(url_for('index'))

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        flash('Please login to access the dashboard.', 'warning')
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Dynamic statistics for Admin/User Dashboard
    stats = {}
    records = []
    
    try:
        stats['total_records'] = cursor.execute('SELECT COUNT(*) FROM land_records').fetchone()[0]
        stats['total_area'] = round(cursor.execute('SELECT SUM(area) FROM land_records').fetchone()[0] or 0.0, 2)
        stats['total_value'] = round((cursor.execute('SELECT SUM(market_value) FROM land_records').fetchone()[0] or 0.0) / 10000000.0, 2)
        stats['verified_count'] = cursor.execute("SELECT COUNT(*) FROM land_records WHERE registry_status = 'Verified'").fetchone()[0]
        stats['pending_count'] = cursor.execute("SELECT COUNT(*) FROM land_records WHERE registry_status = 'Pending'").fetchone()[0]
        stats['disputed_count'] = cursor.execute("SELECT COUNT(*) FROM land_records WHERE registry_status = 'Disputed'").fetchone()[0]
        stats['transferred_count'] = cursor.execute("SELECT COUNT(*) FROM land_records WHERE registry_status = 'Transferred'").fetchone()[0]
        
        # Load land records list
        records = cursor.execute('SELECT * FROM land_records ORDER BY id DESC').fetchall()
    except sqlite3.Error as e:
        flash(f"Database error on dashboard: {e}", 'danger')
        
    conn.close()
    return render_template('dashboard.html', stats=stats, records=records)

# DASHBOARD CHARTS DATA (AJAX JSON endpoint)
@app.route('/api/dashboard/chart-data')
def dashboard_chart_data():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Land Type distribution (Count & Sum Area)
    type_data = []
    try:
        type_rows = cursor.execute('SELECT land_type, COUNT(*), SUM(area) FROM land_records GROUP BY land_type').fetchall()
        type_data = [{'type': r[0], 'count': r[1], 'area': round(r[2], 2)} for r in type_rows]
    except sqlite3.Error:
        pass
        
    # 2. District wise distribution
    district_data = []
    try:
        dist_rows = cursor.execute('SELECT district, COUNT(*), SUM(market_value) FROM land_records GROUP BY district').fetchall()
        district_data = [{'district': r[0], 'count': r[1], 'value': round(r[2]/10000000.0, 2)} for r in dist_rows] # Value in Crores
    except sqlite3.Error:
        pass
        
    conn.close()
    return jsonify({
        'land_types': type_data,
        'districts': district_data
    })

# ADD RECORD (Admin only)
@app.route('/admin/add', methods=['GET', 'POST'])
def add_record():
    if not is_logged_in():
        flash('Access Denied. Authentication required.', 'danger')
        return redirect(url_for('login'))
    if not is_admin():
        flash('Access Denied. Administrator privileges required.', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        owner_name = request.form.get('owner_name', '').strip()
        khasra_number = request.form.get('khasra_number', '').strip()
        khata_number = request.form.get('khata_number', '').strip()
        area = request.form.get('area', '').strip()
        market_value = request.form.get('market_value', '').strip()
        village = request.form.get('village', '').strip()
        district = request.form.get('district', '').strip()
        land_type = request.form.get('land_type', 'Agricultural')
        registry_status = request.form.get('registry_status', 'Pending')
        registration_date = request.form.get('registration_date', '').strip()
        remarks = request.form.get('remarks', '').strip()
        
        father_husband_name = request.form.get('father_husband_name', '').strip()
        aadhaar_id = request.form.get('aadhaar_id', '').strip()
        mobile_number = request.form.get('mobile_number', '').strip()
        survey_number = request.form.get('survey_number', '').strip()
        tehsil = request.form.get('tehsil', '').strip()
        state = request.form.get('state', '').strip()
        pin_code = request.form.get('pin_code', '').strip()
        
        # Validations
        if not all([owner_name, father_husband_name, aadhaar_id, mobile_number, khasra_number, khata_number, survey_number, area, market_value, village, tehsil, district, state, pin_code, registration_date]):
            flash('Please fill in all required fields.', 'warning')
            return render_template('crud.html', record=None)
            
        try:
            area = float(area)
            market_value = float(market_value)
            if area <= 0 or market_value <= 0:
                raise ValueError
        except ValueError:
            flash('Area and Market Value must be positive numeric values.', 'warning')
            return render_template('crud.html', record=request.form)
            
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO land_records (
                    owner_name, father_husband_name, aadhaar_id, mobile_number, 
                    khasra_number, khata_number, survey_number, area, market_value, 
                    village, tehsil, district, state, pin_code, 
                    land_type, registry_status, registration_date, remarks
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (owner_name, father_husband_name, aadhaar_id, mobile_number, khasra_number, khata_number, survey_number, area, market_value, village, tehsil, district, state, pin_code, land_type, registry_status, registration_date, remarks))
            conn.commit()
            flash('Land record registered successfully!', 'success')
            return redirect(url_for('dashboard'))
        except sqlite3.Error as e:
            flash(f'Failed to add record: {e}', 'danger')
        finally:
            conn.close()
            
    return render_template('crud.html', record=None)

# EDIT RECORD (Admin only)
@app.route('/admin/edit/<int:record_id>', methods=['GET', 'POST'])
def edit_record(record_id):
    if not is_logged_in():
        flash('Access Denied. Authentication required.', 'danger')
        return redirect(url_for('login'))
    if not is_admin():
        flash('Access Denied. Administrator privileges required.', 'danger')
        return redirect(url_for('dashboard'))
        
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM land_records WHERE id = ?', (record_id,)).fetchone()
    
    if not record:
        conn.close()
        flash('Record not found.', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        owner_name = request.form.get('owner_name', '').strip()
        khasra_number = request.form.get('khasra_number', '').strip()
        khata_number = request.form.get('khata_number', '').strip()
        area = request.form.get('area', '').strip()
        market_value = request.form.get('market_value', '').strip()
        village = request.form.get('village', '').strip()
        district = request.form.get('district', '').strip()
        land_type = request.form.get('land_type', 'Agricultural')
        registry_status = request.form.get('registry_status', 'Pending')
        registration_date = request.form.get('registration_date', '').strip()
        remarks = request.form.get('remarks', '').strip()
        
        father_husband_name = request.form.get('father_husband_name', '').strip()
        aadhaar_id = request.form.get('aadhaar_id', '').strip()
        mobile_number = request.form.get('mobile_number', '').strip()
        survey_number = request.form.get('survey_number', '').strip()
        tehsil = request.form.get('tehsil', '').strip()
        state = request.form.get('state', '').strip()
        pin_code = request.form.get('pin_code', '').strip()
        
        # Validations
        if not all([owner_name, father_husband_name, aadhaar_id, mobile_number, khasra_number, khata_number, survey_number, area, market_value, village, tehsil, district, state, pin_code, registration_date]):
            flash('Please fill in all required fields.', 'warning')
            return render_template('crud.html', record=record)
            
        try:
            area = float(area)
            market_value = float(market_value)
            if area <= 0 or market_value <= 0:
                raise ValueError
        except ValueError:
            flash('Area and Market Value must be positive numeric values.', 'warning')
            return render_template('crud.html', record=request.form, is_edit=True, record_id=record_id)
            
        try:
            conn.execute('''
                UPDATE land_records
                SET owner_name = ?, father_husband_name = ?, aadhaar_id = ?, mobile_number = ?, 
                    khasra_number = ?, khata_number = ?, survey_number = ?, area = ?, market_value = ?, 
                    village = ?, tehsil = ?, district = ?, state = ?, pin_code = ?, 
                    land_type = ?, registry_status = ?, registration_date = ?, remarks = ?
                WHERE id = ?
            ''', (owner_name, father_husband_name, aadhaar_id, mobile_number, khasra_number, khata_number, survey_number, area, market_value, village, tehsil, district, state, pin_code, land_type, registry_status, registration_date, remarks, record_id))
            conn.commit()
            flash('Land record updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        except sqlite3.Error as e:
            flash(f'Failed to update record: {e}', 'danger')
        finally:
            conn.close()
            
    conn.close()
    return render_template('crud.html', record=record, is_edit=True, record_id=record_id)

# DELETE RECORD (Admin only)
@app.route('/admin/delete/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    if not is_logged_in():
        flash('Access Denied. Authentication required.', 'danger')
        return redirect(url_for('login'))
    if not is_admin():
        flash('Access Denied. Administrator privileges required.', 'danger')
        return redirect(url_for('dashboard'))
        
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM land_records WHERE id = ?', (record_id,))
        conn.commit()
        flash('Record deleted successfully.', 'success')
    except sqlite3.Error as e:
        flash(f'Failed to delete record: {e}', 'danger')
    finally:
        conn.close()
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
