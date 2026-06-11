import sqlite3
import os
import random
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed existing database.db")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        full_name TEXT,
        email TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS land_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_name TEXT NOT NULL,
        father_husband_name TEXT NOT NULL,
        aadhaar_id TEXT NOT NULL,
        mobile_number TEXT NOT NULL,
        khasra_number TEXT NOT NULL,
        khata_number TEXT NOT NULL,
        survey_number TEXT NOT NULL,
        area REAL NOT NULL,
        market_value REAL NOT NULL,
        village TEXT NOT NULL,
        tehsil TEXT NOT NULL,
        district TEXT NOT NULL,
        state TEXT NOT NULL,
        pin_code TEXT NOT NULL,
        land_type TEXT NOT NULL,
        registry_status TEXT NOT NULL,
        registration_date TEXT NOT NULL,
        remarks TEXT
    )
    ''')

    admin_pw = generate_password_hash('admin123')
    user_pw = generate_password_hash('user123')

    cursor.execute('''
    INSERT INTO users (username, password, role, full_name, email)
    VALUES (?, ?, ?, ?, ?)
    ''', ('admin', admin_pw, 'admin', 'Super Administrator', 'admin@landregistry.gov.in'))

    cursor.execute('''
    INSERT INTO users (username, password, role, full_name, email)
    VALUES (?, ?, ?, ?, ?)
    ''', ('user', user_pw, 'user', 'Citizen User', 'user@citizenmail.in'))

    # Generate Realistic Records Data Pools
    first_names_m = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan", "Shaurya", "Atharva", "Rajesh", "Vikram", "Amit", "Ramesh", "Anil", "Sanjay", "Suresh", "Rahul", "Rohit", "Karan", "Nikhil", "Gaurav"]
    first_names_f = ["Ananya", "Diya", "Navya", "Kavya", "Isha", "Riya", "Aarohi", "Avni", "Sunita", "Priyanka", "Meena", "Neha", "Pooja", "Sneha", "Nisha", "Swati"]
    last_names = ["Sharma", "Singh", "Patel", "Devi", "Verma", "Choudhary", "Yadav", "Gupta", "Bai", "Kumar", "Mishra", "Das", "Jain", "Bansal", "Agarwal", "Reddy", "Nair", "Iyer", "Joshi", "Deshmukh", "Patil", "Kaur", "Khatri", "Thakur", "Chauhan"]
    
    locations = [
        {"state": "Rajasthan", "district": "Jaipur", "tehsil": "Sanganer", "villages": ["Rampur", "Gokalpura", "Muhana", "Bhankrota"], "pins": ["302029", "302026", "302033"]},
        {"state": "Rajasthan", "district": "Jodhpur", "tehsil": "Mandore", "villages": ["Devpura", "Balarwa", "Magra", "Daiya"], "pins": ["342304", "342006", "342001"]},
        {"state": "Rajasthan", "district": "Udaipur", "tehsil": "Girwa", "villages": ["Kishanpura", "Sisarma", "Nai", "Badi"], "pins": ["313031", "313001", "313011"]},
        {"state": "Maharashtra", "district": "Pune", "tehsil": "Haveli", "villages": ["Khadakwasla", "Narhe", "Dhayari", "Wagholi"], "pins": ["411024", "411041", "412207"]},
        {"state": "Maharashtra", "district": "Nashik", "tehsil": "Niphad", "villages": ["Lasalgaon", "Pimpalgaon", "Saikheda", "Ozar"], "pins": ["422306", "422209", "422206"]},
        {"state": "Uttar Pradesh", "district": "Lucknow", "tehsil": "Mohanlalganj", "villages": ["Kankaha", "Sisendi", "Mow", "Bakkas"], "pins": ["226301", "226302", "226014"]},
        {"state": "Uttar Pradesh", "district": "Kanpur Nagar", "tehsil": "Ghatampur", "villages": ["Bhitargaon", "Patara", "Sausarpur", "Reuna"], "pins": ["209206", "209308", "209208"]}
    ]
    
    land_types = ["Agricultural", "Residential", "Commercial", "Industrial"]
    statuses = ["Verified", "Pending", "Disputed", "Transferred"]
    
    remarks_options = [
        "Clear title, verified physically",
        "Ancestral property partitioned through court decree",
        "Civil court dispute regarding adjacent boundaries",
        "Pending final approval from Tehsildar",
        "Property under crop mortgage loan",
        "Verified through digital satellite mapping",
        "Converted from Agricultural to Commercial usage",
        "Joint holding property, no disputes",
        "Inherited via registered succession certificate",
        ""
    ]

    dummy_records = []
    
    # Ensure known recognizable records for testing
    dummy_records.append(('Mukesh Ambani', 'Dhirubhai Ambani', 'XXXX-XXXX-9999', '+91 9876543210', '1001/A', 'KH-999', 'SUR-888', 5.5, 50000000.0, 'Malabar Hill', 'Mumbai City', 'Mumbai', 'Maharashtra', '400006', 'Residential', 'Verified', '2015-08-15', 'Premium tier verified property'))
    
    for i in range(1, 61):
        # Determine gender and names
        is_male = random.random() > 0.3
        first_name = random.choice(first_names_m) if is_male else random.choice(first_names_f)
        last_name = random.choice(last_names)
        owner_name = f"{first_name} {last_name}"
        
        # Father / Husband Name
        guardian_first = random.choice(first_names_m)
        guardian_last = last_name if is_male else random.choice(last_names)
        guardian_name = f"{guardian_first} {guardian_last}"
        
        # Identity
        aadhaar = f"XXXX-XXXX-{random.randint(1000, 9999)}"
        mobile = f"+91 {random.randint(7,9)}{random.randint(100000000, 999999999)}"
        
        # Land IDs
        khasra = f"{random.randint(10, 999)}/{random.randint(1, 9)}" if random.random() > 0.3 else str(random.randint(10, 999))
        khata = f"KH-{random.randint(100, 9999)}"
        survey = f"SUR-{random.randint(1000, 5000)}"
        
        # Value
        area = round(random.uniform(0.1, 10.0), 2)
        market_value = round(area * random.uniform(500000, 5000000), 2)
        
        # Geography
        loc = random.choice(locations)
        state = loc["state"]
        district = loc["district"]
        tehsil = loc["tehsil"]
        village = random.choice(loc["villages"])
        pincode = random.choice(loc["pins"])
        
        # Meta
        l_type = random.choice(land_types)
        status = random.choices(statuses, weights=[0.65, 0.15, 0.1, 0.1])[0]
        
        year = random.randint(2012, 2026)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        reg_date = f"{year}-{month:02d}-{day:02d}"
        
        remark = random.choice(remarks_options)

        dummy_records.append((owner_name, guardian_name, aadhaar, mobile, khasra, khata, survey, area, market_value, village, tehsil, district, state, pincode, l_type, status, reg_date, remark))

    cursor.executemany('''
    INSERT INTO land_records (
        owner_name, father_husband_name, aadhaar_id, mobile_number, 
        khasra_number, khata_number, survey_number, area, market_value, 
        village, tehsil, district, state, pin_code, 
        land_type, registry_status, registration_date, remarks
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', dummy_records)

    conn.commit()
    conn.close()
    print("Database initialized with expanded realistic schema and 61 records.")

if __name__ == '__main__':
    init_db()
