 # backend/models.py
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "hms.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # users (mobile number authentication)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT,
      phone TEXT UNIQUE NOT NULL,
      otp_code TEXT,
      otp_expires TEXT,
      is_verified INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # patients (new)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patients (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      dob TEXT,
      gender TEXT,
      phone TEXT,
      email TEXT,
      address TEXT,
      emergency_contact TEXT,
      emergency_phone TEXT,
      medical_history TEXT,
      allergies TEXT,
      blood_type TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # caretakers (new)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS caretakers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      patient_id INTEGER,
      name TEXT NOT NULL,
      relationship TEXT,
      phone TEXT,
      email TEXT,
      address TEXT,
      FOREIGN KEY (patient_id) REFERENCES patients (id)
    )""")

    # hospitality (new)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS hospitality (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      patient_id INTEGER,
      admission_date TEXT,
      discharge_date TEXT,
      room_number TEXT,
      room_type TEXT,
      services TEXT,
      daily_rate REAL,
      total_charges REAL DEFAULT 0,
      status TEXT DEFAULT 'active',
      FOREIGN KEY (patient_id) REFERENCES patients (id)
    )""")

    # checkups (expanded vitals)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS checkups (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      patient_id INTEGER,
      test_type TEXT NOT NULL,
      test_name TEXT,
      value TEXT,
      unit TEXT,
      reference_range TEXT,
      result_status TEXT,
      notes TEXT,
      performed_by TEXT,
      timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (patient_id) REFERENCES patients (id)
    )""")

    # bills (new)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bills (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      patient_id INTEGER,
      bill_date TEXT DEFAULT CURRENT_TIMESTAMP,
      itemized_charges TEXT, -- JSON string of charges
      subtotal REAL,
      tax_rate REAL DEFAULT 0.1,
      tax_amount REAL,
      total_amount REAL,
      payment_status TEXT DEFAULT 'pending',
      notes TEXT,
      FOREIGN KEY (patient_id) REFERENCES patients (id)
    )""")

    # vitals (existing, keeping for backward compatibility)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vitals (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      type TEXT,
      value TEXT,
      unit TEXT,
      timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # symptoms
    cur.execute("""
    CREATE TABLE IF NOT EXISTS symptoms (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      name TEXT,
      system TEXT,
      severity INTEGER,
      notes TEXT,
      timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # medications
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medications (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      name TEXT,
      dose TEXT,
      schedule TEXT,
      start_date TEXT,
      end_date TEXT,
      notes TEXT
    )""")

    # appointments
    cur.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      doctor TEXT,
      datetime TEXT,
      type TEXT,
      notes TEXT
    )""")

    # user_roles (for RBAC)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_roles (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      role TEXT NOT NULL,
      permissions TEXT, -- JSON array of permissions
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # two_factor_auth
    cur.execute("""
    CREATE TABLE IF NOT EXISTS two_factor_auth (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      secret_key TEXT NOT NULL,
      backup_codes TEXT, -- JSON array of backup codes
      enabled INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # user_preferences (for themes, notifications, etc.)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_preferences (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      preference_key TEXT NOT NULL,
      preference_value TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # encrypted_data (for HIPAA compliance)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS encrypted_data (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      data_type TEXT NOT NULL, -- 'medical_history', 'symptoms', etc.
      encrypted_data TEXT NOT NULL,
      encryption_key_id TEXT NOT NULL,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # ai_models (for storing trained models)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ai_models (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      model_name TEXT NOT NULL,
      model_type TEXT NOT NULL, -- 'diagnosis', 'risk_assessment', etc.
      model_data TEXT, -- Serialized model or API endpoint
      accuracy_score REAL,
      trained_at TEXT DEFAULT CURRENT_TIMESTAMP,
      is_active INTEGER DEFAULT 1
    )""")

    # chatbot_conversations
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chatbot_conversations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      session_id TEXT NOT NULL,
      message TEXT NOT NULL,
      response TEXT NOT NULL,
      intent TEXT,
      confidence REAL,
      timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # smart_schedules
    cur.execute("""
    CREATE TABLE IF NOT EXISTS smart_schedules (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      schedule_type TEXT NOT NULL, -- 'medication', 'appointment', 'checkup'
      item_id INTEGER, -- Foreign key to respective table
      scheduled_time TEXT NOT NULL,
      reminder_time TEXT,
      priority INTEGER DEFAULT 1,
      status TEXT DEFAULT 'active',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # wearable_data
    cur.execute("""
    CREATE TABLE IF NOT EXISTS wearable_data (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      device_type TEXT NOT NULL, -- 'fitbit', 'apple_watch', etc.
      device_id TEXT,
      data_type TEXT NOT NULL, -- 'heart_rate', 'steps', 'sleep', etc.
      data_value TEXT, -- JSON data
      timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # voice_commands
    cur.execute("""
    CREATE TABLE IF NOT EXISTS voice_commands (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      command_text TEXT NOT NULL,
      command_type TEXT NOT NULL, -- 'navigation', 'data_entry', 'query'
      action_taken TEXT,
      success INTEGER DEFAULT 1,
      timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # communities
    cur.execute("""
    CREATE TABLE IF NOT EXISTS communities (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      description TEXT,
      category TEXT,
      moderator_id INTEGER,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (moderator_id) REFERENCES users (id)
    )""")

    # community_members
    cur.execute("""
    CREATE TABLE IF NOT EXISTS community_members (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      community_id INTEGER,
      user_id INTEGER,
      joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (community_id) REFERENCES communities (id),
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # community_posts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS community_posts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      community_id INTEGER,
      user_id INTEGER,
      title TEXT NOT NULL,
      content TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (community_id) REFERENCES communities (id),
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # health_quizzes
    cur.execute("""
    CREATE TABLE IF NOT EXISTS health_quizzes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      description TEXT,
      category TEXT,
      difficulty TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # quiz_questions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS quiz_questions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      quiz_id INTEGER,
      question TEXT NOT NULL,
      options TEXT, -- JSON array of options
      correct_answer INTEGER,
      explanation TEXT,
      FOREIGN KEY (quiz_id) REFERENCES health_quizzes (id)
    )""")

    # quiz_attempts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS quiz_attempts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      quiz_id INTEGER,
      score INTEGER,
      total_questions INTEGER,
      completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id),
      FOREIGN KEY (quiz_id) REFERENCES health_quizzes (id)
    )""")

    # ai_insights
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ai_insights (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      insight_type TEXT,
      insight_data TEXT, -- JSON
      risk_level TEXT,
      recommendations TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # wellness_scores
    cur.execute("""
    CREATE TABLE IF NOT EXISTS wellness_scores (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      score INTEGER,
      factors TEXT, -- JSON of contributing factors
      calculated_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # emergency_contacts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS emergency_contacts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      name TEXT NOT NULL,
      relationship TEXT,
      phone TEXT NOT NULL,
      email TEXT,
      priority INTEGER DEFAULT 1,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # medication_interactions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medication_interactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      medication1 TEXT NOT NULL,
      medication2 TEXT NOT NULL,
      interaction_type TEXT,
      description TEXT,
      severity TEXT
    )""")

    # diet_plans
    cur.execute("""
    CREATE TABLE IF NOT EXISTS diet_plans (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      plan_name TEXT NOT NULL,
      description TEXT,
      daily_calories INTEGER,
      macronutrients TEXT, -- JSON
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )""")

    # diet_meals
    cur.execute("""
    CREATE TABLE IF NOT EXISTS diet_meals (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      diet_plan_id INTEGER,
      meal_type TEXT, -- breakfast, lunch, dinner, snack
      meal_name TEXT NOT NULL,
      ingredients TEXT, -- JSON
      nutritional_info TEXT, -- JSON
      instructions TEXT,
      FOREIGN KEY (diet_plan_id) REFERENCES diet_plans (id)
    )""")




    conn.commit()
    conn.close()

# Helper functions for new models
def create_patient(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO patients (name, dob, gender, phone, email, address,
                           emergency_contact, emergency_phone, medical_history,
                           allergies, blood_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['name'], data.get('dob'), data.get('gender'), data.get('phone'),
          data.get('email'), data.get('address'), data.get('emergency_contact'),
          data.get('emergency_phone'), data.get('medical_history'),
          data.get('allergies'), data.get('blood_type')))
    patient_id = cur.lastrowid
    conn.commit()
    conn.close()
    return patient_id

def get_patients():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients ORDER BY created_at DESC")
    patients = cur.fetchall()
    conn.close()
    return [dict(row) for row in patients]

def get_patient(patient_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = cur.fetchone()
    conn.close()
    return dict(patient) if patient else None

def update_patient(patient_id, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE patients
        SET name = ?, dob = ?, gender = ?, phone = ?, email = ?, address = ?,
            emergency_contact = ?, emergency_phone = ?, medical_history = ?,
            allergies = ?, blood_type = ?
        WHERE id = ?
    """, (
        data['name'], data.get('dob'), data.get('gender'), data.get('phone'),
        data.get('email'), data.get('address'), data.get('emergency_contact'),
        data.get('emergency_phone'), data.get('medical_history'),
        data.get('allergies'), data.get('blood_type'), patient_id
    ))
    updated = cur.rowcount
    conn.commit()
    conn.close()
    return updated > 0

def delete_patient(patient_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted > 0

def create_caretaker(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO caretakers (patient_id, name, relationship, phone, email, address)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data['patient_id'], data['name'], data.get('relationship'),
          data.get('phone'), data.get('email'), data.get('address')))
    caretaker_id = cur.lastrowid
    conn.commit()
    conn.close()
    return caretaker_id

def get_caretakers(patient_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM caretakers WHERE patient_id = ?", (patient_id,))
    caretakers = cur.fetchall()
    conn.close()
    return [dict(row) for row in caretakers]

def create_hospitality(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO hospitality (patient_id, admission_date, room_number, room_type,
                               services, daily_rate)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data['patient_id'], data['admission_date'], data.get('room_number'),
          data.get('room_type'), data.get('services'), data.get('daily_rate', 0)))
    hospitality_id = cur.lastrowid
    conn.commit()
    conn.close()
    return hospitality_id

def get_hospitality(patient_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hospitality WHERE patient_id = ? ORDER BY admission_date DESC", (patient_id,))
    hospitality = cur.fetchall()
    conn.close()
    return [dict(row) for row in hospitality]

def get_hospitality_record(hospitality_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hospitality WHERE id = ?", (hospitality_id,))
    hospitality = cur.fetchone()
    conn.close()
    return dict(hospitality) if hospitality else None

def update_hospitality(hospitality_id, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE hospitality
        SET patient_id = ?, admission_date = ?, discharge_date = ?, room_number = ?,
            room_type = ?, services = ?, daily_rate = ?, status = ?
        WHERE id = ?
    """, (
        data['patient_id'], data.get('admission_date'), data.get('discharge_date'),
        data.get('room_number'), data.get('room_type'), data.get('services'),
        data.get('daily_rate', 0), data.get('status'), hospitality_id
    ))
    updated = cur.rowcount
    conn.commit()
    conn.close()
    return updated > 0

def delete_hospitality(hospitality_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM hospitality WHERE id = ?", (hospitality_id,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted > 0

def create_checkup(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO checkups (patient_id, test_type, test_name, value, unit,
                            reference_range, result_status, notes, performed_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['patient_id'], data['test_type'], data.get('test_name'),
          data.get('value'), data.get('unit'), data.get('reference_range'),
          data.get('result_status'), data.get('notes'), data.get('performed_by')))
    checkup_id = cur.lastrowid
    conn.commit()
    conn.close()
    return checkup_id

def get_checkups(patient_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM checkups WHERE patient_id = ? ORDER BY timestamp DESC", (patient_id,))
    checkups = cur.fetchall()
    conn.close()
    return [dict(row) for row in checkups]

def get_checkup(checkup_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM checkups WHERE id = ?", (checkup_id,))
    checkup = cur.fetchone()
    conn.close()
    return dict(checkup) if checkup else None

def update_checkup(checkup_id, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE checkups
        SET patient_id = ?, test_type = ?, test_name = ?, value = ?, unit = ?,
            reference_range = ?, result_status = ?, notes = ?, performed_by = ?
        WHERE id = ?
    """, (
        data['patient_id'], data['test_type'], data.get('test_name'),
        data.get('value'), data.get('unit'), data.get('reference_range'),
        data.get('result_status'), data.get('notes'), data.get('performed_by'),
        checkup_id
    ))
    updated = cur.rowcount
    conn.commit()
    conn.close()
    return updated > 0

def delete_checkup(checkup_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM checkups WHERE id = ?", (checkup_id,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted > 0

def create_bill(data):
    conn = get_conn()
    cur = conn.cursor()
    # Calculate tax and total
    subtotal = data['subtotal']
    tax_rate = data.get('tax_rate', 0.1)
    tax_amount = subtotal * tax_rate
    total_amount = subtotal + tax_amount

    cur.execute("""
        INSERT INTO bills (patient_id, itemized_charges, subtotal, tax_rate,
                         tax_amount, total_amount, payment_status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['patient_id'], data.get('itemized_charges'), subtotal, tax_rate,
          tax_amount, total_amount, data.get('payment_status', 'pending'),
          data.get('notes')))
    bill_id = cur.lastrowid
    conn.commit()
    conn.close()
    return bill_id

def get_bills(patient_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bills WHERE patient_id = ? ORDER BY bill_date DESC", (patient_id,))
    bills = cur.fetchall()
    conn.close()
    return [dict(row) for row in bills]

def get_bill(bill_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bills WHERE id = ?", (bill_id,))
    bill = cur.fetchone()
    conn.close()
    return dict(bill) if bill else None

def update_bill(bill_id, data):
    conn = get_conn()
    cur = conn.cursor()
    subtotal = data['subtotal']
    tax_rate = data.get('tax_rate', 0.1)
    tax_amount = subtotal * tax_rate
    total_amount = subtotal + tax_amount

    cur.execute("""
        UPDATE bills
        SET patient_id = ?, bill_date = ?, itemized_charges = ?, subtotal = ?,
            tax_rate = ?, tax_amount = ?, total_amount = ?, payment_status = ?, notes = ?
        WHERE id = ?
    """, (
        data['patient_id'], data.get('bill_date'), data.get('itemized_charges'),
        subtotal, tax_rate, tax_amount, total_amount, data.get('payment_status'),
        data.get('notes'), bill_id
    ))
    updated = cur.rowcount
    conn.commit()
    conn.close()
    return updated > 0

def delete_bill(bill_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted > 0

def get_vital(vital_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vitals WHERE id = ?", (vital_id,))
    vital = cur.fetchone()
    conn.close()
    return dict(vital) if vital else None

def update_vital(vital_id, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE vitals
        SET type = ?, value = ?, unit = ?
        WHERE id = ?
    """, (data['type'], str(data['value']), data.get('unit', ''), vital_id))
    updated = cur.rowcount
    conn.commit()
    conn.close()
    return updated > 0

def delete_vital(vital_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM vitals WHERE id = ?", (vital_id,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted > 0

# Helper functions for new advanced features
def create_user_role(user_id, role):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO user_roles (user_id, role) VALUES (?, ?)", (user_id, role))
    role_id = cur.lastrowid
    conn.commit()
    conn.close()
    return role_id

def get_user_roles(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT role FROM user_roles WHERE user_id = ?", (user_id,))
    roles = cur.fetchall()
    conn.close()
    return [row['role'] for row in roles]

def create_community(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO communities (name, description, category, moderator_id)
        VALUES (?, ?, ?, ?)
    """, (data['name'], data.get('description'), data.get('category'), data.get('moderator_id')))
    community_id = cur.lastrowid
    conn.commit()
    conn.close()
    return community_id

def get_communities():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM communities ORDER BY created_at DESC")
    communities = cur.fetchall()
    conn.close()
    return [dict(row) for row in communities]

def join_community(community_id, user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO community_members (community_id, user_id) VALUES (?, ?)", (community_id, user_id))
    conn.commit()
    conn.close()

def create_community_post(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO community_posts (community_id, user_id, title, content)
        VALUES (?, ?, ?, ?)
    """, (data['community_id'], data['user_id'], data['title'], data['content']))
    post_id = cur.lastrowid
    conn.commit()
    conn.close()
    return post_id

def get_community_posts(community_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT cp.*, u.name as author_name
        FROM community_posts cp
        JOIN users u ON cp.user_id = u.id
        WHERE cp.community_id = ?
        ORDER BY cp.created_at DESC
    """, (community_id,))
    posts = cur.fetchall()
    conn.close()
    return [dict(row) for row in posts]

def create_quiz(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO health_quizzes (title, description, category, difficulty)
        VALUES (?, ?, ?, ?)
    """, (data['title'], data.get('description'), data.get('category'), data.get('difficulty')))
    quiz_id = cur.lastrowid
    conn.commit()
    conn.close()
    return quiz_id

def get_quizzes():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM health_quizzes ORDER BY created_at DESC")
    quizzes = cur.fetchall()
    conn.close()
    return [dict(row) for row in quizzes]

def create_quiz_question(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO quiz_questions (quiz_id, question, options, correct_answer, explanation)
        VALUES (?, ?, ?, ?, ?)
    """, (data['quiz_id'], data['question'], data['options'], data['correct_answer'], data.get('explanation')))
    question_id = cur.lastrowid
    conn.commit()
    conn.close()
    return question_id

def get_quiz_questions(quiz_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM quiz_questions WHERE quiz_id = ? ORDER BY id", (quiz_id,))
    questions = cur.fetchall()
    conn.close()
    return [dict(row) for row in questions]

def save_quiz_attempt(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO quiz_attempts (user_id, quiz_id, score, total_questions)
        VALUES (?, ?, ?, ?)
    """, (data['user_id'], data['quiz_id'], data['score'], data['total_questions']))
    attempt_id = cur.lastrowid
    conn.commit()
    conn.close()
    return attempt_id

def create_ai_insight(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ai_insights (user_id, insight_type, insight_data, risk_level, recommendations)
        VALUES (?, ?, ?, ?, ?)
    """, (data['user_id'], data['insight_type'], data.get('insight_data'), data.get('risk_level'), data.get('recommendations')))
    insight_id = cur.lastrowid
    conn.commit()
    conn.close()
    return insight_id

def get_ai_insights(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ai_insights WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    insights = cur.fetchall()
    conn.close()
    return [dict(row) for row in insights]

def calculate_wellness_score(user_id):
    # Simple wellness score calculation based on recent data
    conn = get_conn()
    cur = conn.cursor()

    # Get recent vitals (last 30 days)
    cur.execute("""
        SELECT COUNT(*) as vital_count,
               AVG(CASE WHEN type = 'Blood Pressure' THEN CAST(SUBSTR(value, 1, INSTR(value, '/') - 1) AS INTEGER) END) as avg_bp
        FROM vitals
        WHERE user_id = ? AND timestamp > datetime('now', '-30 days')
    """, (user_id,))
    vitals_data = cur.fetchone()

    # Get symptom severity average
    cur.execute("""
        SELECT AVG(severity) as avg_severity, COUNT(*) as symptom_count
        FROM symptoms
        WHERE user_id = ? AND timestamp > datetime('now', '-30 days')
    """, (user_id,))
    symptoms_data = cur.fetchone()

    # Get medication adherence (simplified)
    cur.execute("SELECT COUNT(*) as med_count FROM medications WHERE user_id = ?", (user_id,))
    meds_data = cur.fetchone()

    conn.close()

    # Calculate score (0-100)
    score = 100
    if vitals_data['vital_count'] < 5: score -= 20  # Less monitoring
    if symptoms_data['avg_severity'] and symptoms_data['avg_severity'] > 5: score -= symptoms_data['avg_severity'] * 2
    if meds_data['med_count'] > 0: score += 10  # Taking medications regularly

    score = max(0, min(100, score))

    # Save wellness score
    factors = {
        'vitals_tracked': vitals_data['vital_count'],
        'avg_symptom_severity': symptoms_data['avg_severity'] or 0,
        'medications_count': meds_data['med_count']
    }

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO wellness_scores (user_id, score, factors)
        VALUES (?, ?, ?)
    """, (user_id, score, str(factors)))
    conn.commit()
    conn.close()

    return score

def get_wellness_scores(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM wellness_scores WHERE user_id = ? ORDER BY calculated_at DESC LIMIT 10", (user_id,))
    scores = cur.fetchall()
    conn.close()
    return [dict(row) for row in scores]

def create_emergency_contact(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO emergency_contacts (user_id, name, relationship, phone, email, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data['user_id'], data['name'], data.get('relationship'), data['phone'], data.get('email'), data.get('priority', 1)))
    contact_id = cur.lastrowid
    conn.commit()
    conn.close()
    return contact_id

def get_emergency_contacts(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM emergency_contacts WHERE user_id = ? ORDER BY priority", (user_id,))
    contacts = cur.fetchall()
    conn.close()
    return [dict(row) for row in contacts]

def check_medication_interactions(medications):
    # Simple interaction checking - in real app, this would use a comprehensive database
    interactions = []
    for i, med1 in enumerate(medications):
        for med2 in medications[i+1:]:
            # Check for known interactions (simplified example)
            if ('aspirin' in med1.lower() and 'warfarin' in med2.lower()) or \
               ('warfarin' in med1.lower() and 'aspirin' in med2.lower()):
                interactions.append({
                    'medication1': med1,
                    'medication2': med2,
                    'severity': 'high',
                    'description': 'Increased risk of bleeding'
                })
    return interactions

def create_diet_plan(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO diet_plans (user_id, plan_name, description, daily_calories, macronutrients)
        VALUES (?, ?, ?, ?, ?)
    """, (data['user_id'], data['plan_name'], data.get('description'), data.get('daily_calories'), data.get('macronutrients')))
    plan_id = cur.lastrowid
    conn.commit()
    conn.close()
    return plan_id

def get_diet_plans(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM diet_plans WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    plans = cur.fetchall()
    conn.close()
    return [dict(row) for row in plans]

def create_diet_meal(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO diet_meals (diet_plan_id, meal_type, meal_name, ingredients, nutritional_info, instructions)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data['diet_plan_id'], data['meal_type'], data['meal_name'], data.get('ingredients'), data.get('nutritional_info'), data.get('instructions')))
    meal_id = cur.lastrowid
    conn.commit()
    conn.close()
    return meal_id

def get_diet_meals(plan_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM diet_meals WHERE diet_plan_id = ? ORDER BY meal_type", (plan_id,))
    meals = cur.fetchall()
    conn.close()
    return [dict(row) for row in meals]

# RBAC and Security Functions
def assign_user_role(user_id, role, permissions=None):
    conn = get_conn()
    cur = conn.cursor()
    permissions_json = str(permissions) if permissions else None
    cur.execute("INSERT INTO user_roles (user_id, role, permissions) VALUES (?, ?, ?)",
                (user_id, role, permissions_json))
    role_id = cur.lastrowid
    conn.commit()
    conn.close()
    return role_id

def check_user_permission(user_id, required_permission):
    roles = get_user_roles(user_id)
    if 'admin' in roles:
        return True

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT permissions FROM user_roles WHERE user_id = ?", (user_id,))
    permissions_data = cur.fetchall()
    conn.close()

    for row in permissions_data:
        if row['permissions']:
            permissions = eval(row['permissions'])  # Simple eval for demo
            if required_permission in permissions:
                return True
    return False

# Two-Factor Authentication Functions
def setup_2fa(user_id):
    import pyotp
    secret = pyotp.random_base32()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO two_factor_auth (user_id, secret_key) VALUES (?, ?)", (user_id, secret))
    conn.commit()
    conn.close()
    return secret

def verify_2fa(user_id, token):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT secret_key FROM two_factor_auth WHERE user_id = ? AND enabled = 1", (user_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        import pyotp
        totp = pyotp.TOTP(row['secret_key'])
        return totp.verify(token)
    return False

# Encryption Functions (Simplified for demo)
def encrypt_data(data, key_id="default"):
    # In production, use proper encryption like Fernet
    encrypted = data[::-1]  # Simple reverse for demo
    return encrypted, key_id

def decrypt_data(encrypted_data, key_id):
    # In production, use proper decryption
    decrypted = encrypted_data[::-1]  # Simple reverse for demo
    return decrypted

def store_encrypted_data(user_id, data_type, data):
    encrypted_data, key_id = encrypt_data(data)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO encrypted_data (user_id, data_type, encrypted_data, encryption_key_id)
        VALUES (?, ?, ?, ?)
    """, (user_id, data_type, encrypted_data, key_id))
    conn.commit()
    conn.close()

# AI and ML Functions
def generate_ai_insight(user_id, symptoms, vitals):
    # Simple rule-based AI for demo
    risk_level = "low"
    recommendations = []

    # Check for high-risk symptoms
    high_risk_symptoms = ['chest pain', 'difficulty breathing', 'severe headache']
    for symptom in symptoms:
        if any(hr_symptom in symptom.lower() for hr_symptom in high_risk_symptoms):
            risk_level = "high"
            recommendations.append("Seek immediate medical attention")

    # Check vitals
    for vital in vitals:
        if vital['type'] == 'Blood Pressure':
            systolic = int(vital['value'].split('/')[0])
            if systolic > 180:
                risk_level = "high"
                recommendations.append("Monitor blood pressure closely")

    if not recommendations:
        recommendations.append("Continue regular health monitoring")

    insight_data = {
        'symptoms_analyzed': len(symptoms),
        'vitals_analyzed': len(vitals),
        'risk_factors': []
    }

    create_ai_insight({
        'user_id': user_id,
        'insight_type': 'health_assessment',
        'insight_data': str(insight_data),
        'risk_level': risk_level,
        'recommendations': '; '.join(recommendations)
    })

    return risk_level, recommendations

def predict_diagnosis(symptoms):
    # Simple pattern matching for demo
    diagnosis = "General health check recommended"

    if 'fever' in symptoms and 'cough' in symptoms:
        diagnosis = "Possible respiratory infection"
    elif 'headache' in symptoms and 'nausea' in symptoms:
        diagnosis = "Possible migraine or gastrointestinal issue"
    elif 'chest pain' in symptoms:
        diagnosis = "URGENT: Possible cardiac issue - seek immediate care"

    return diagnosis

# Chatbot Functions
def process_chatbot_message(user_id, message, session_id):
    # Simple rule-based chatbot
    response = "I'm here to help with your health questions. Please consult a healthcare professional for medical advice."

    message_lower = message.lower()

    if 'appointment' in message_lower:
        response = "I can help you schedule an appointment. Would you like me to check available times?"
    elif 'symptom' in message_lower or 'pain' in message_lower:
        response = "Please describe your symptoms in detail. Remember, I'm not a substitute for professional medical advice."
    elif 'medication' in message_lower:
        response = "For medication questions, please consult your healthcare provider or pharmacist."
    elif 'emergency' in message_lower:
        response = "If this is a medical emergency, please call emergency services immediately (911 in the US)."

    # Store conversation
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO chatbot_conversations (user_id, session_id, message, response, intent, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, session_id, message, response, 'general', 0.8))
    conn.commit()
    conn.close()

    return response

# Smart Scheduling Functions
def create_smart_schedule(user_id, schedule_type, item_id, scheduled_time, priority=1):
    # Calculate reminder time (30 minutes before)
    from datetime import datetime
    scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
    reminder_time = scheduled_time  # Simplified - just use scheduled time

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO smart_schedules (user_id, schedule_type, item_id, scheduled_time, reminder_time, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, schedule_type, item_id, scheduled_time, reminder_time, priority))
    schedule_id = cur.lastrowid
    conn.commit()
    conn.close()
    return schedule_id

def get_upcoming_reminders(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM smart_schedules
        WHERE user_id = ? AND status = 'active' AND reminder_time > datetime('now')
        ORDER BY reminder_time ASC LIMIT 10
    """, (user_id,))
    reminders = cur.fetchall()
    conn.close()
    return [dict(row) for row in reminders]

# Wearable Integration Functions
def store_wearable_data(user_id, device_type, device_id, data_type, data_value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO wearable_data (user_id, device_type, device_id, data_type, data_value)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, device_type, device_id, data_type, str(data_value)))
    conn.commit()
    conn.close()

def get_wearable_data(user_id, data_type=None, limit=100):
    conn = get_conn()
    cur = conn.cursor()
    if data_type:
        cur.execute("""
            SELECT * FROM wearable_data
            WHERE user_id = ? AND data_type = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (user_id, data_type, limit))
    else:
        cur.execute("""
            SELECT * FROM wearable_data
            WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (user_id, limit))
    data = cur.fetchall()
    conn.close()
    return [dict(row) for row in data]

# Voice Command Functions
def log_voice_command(user_id, command_text, command_type, action_taken, success=True):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO voice_commands (user_id, command_text, command_type, action_taken, success)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, command_text, command_type, action_taken, 1 if success else 0))
    conn.commit()
    conn.close()

# User Preferences Functions
def set_user_preference(user_id, key, value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO user_preferences (user_id, preference_key, preference_value, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, key, str(value)))
    conn.commit()
    conn.close()

def get_user_preference(user_id, key):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT preference_value FROM user_preferences WHERE user_id = ? AND preference_key = ?", (user_id, key))
    row = cur.fetchone()
    conn.close()
    return row['preference_value'] if row else None

# OTP Authentication Functions
def generate_otp(phone):
    import random
    otp = str(random.randint(100000, 999999))
    expires = datetime.now().isoformat()  # OTP expires timestamp (already a string)

    conn = get_conn()
    cur = conn.cursor()
    # Check if user exists
    cur.execute("SELECT id FROM users WHERE phone = ?", (phone,))
    user = cur.fetchone()

    if user:
        # Update existing user
        cur.execute("UPDATE users SET otp_code = ?, otp_expires = ? WHERE phone = ?",
                   (otp, expires, phone))
        user_id = user['id']
    else:
        # Create new user
        cur.execute("INSERT INTO users (phone, otp_code, otp_expires) VALUES (?, ?, ?)",
                   (phone, otp, expires))
        user_id = cur.lastrowid

    conn.commit()
    conn.close()
    return otp, user_id

def verify_otp(phone, otp):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, otp_code, otp_expires, is_verified FROM users WHERE phone = ?", (phone,))
    user = cur.fetchone()
    conn.close()

    if not user:
        return False, "User not found"

    if user['otp_code'] != otp:
        return False, "Invalid OTP"

    expires = datetime.fromisoformat(user['otp_expires'])
    if datetime.now() > expires:
        return False, "OTP expired"

    # Mark as verified
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = 1, otp_code = NULL, otp_expires = NULL WHERE phone = ?",
               (phone,))
    conn.commit()
    conn.close()

    return True, user['id']

def get_user_by_phone(phone):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE phone = ?", (phone,))
    user = cur.fetchone()
    conn.close()
    return dict(user) if user else None

# Emergency SOS Functions
def trigger_emergency_sos(user_id):
    # Get emergency contacts
    contacts = get_emergency_contacts(user_id)

    # Get user location (would need GPS integration)
    location = "Location tracking not implemented in demo"

    # In production, this would send SMS/emails and call emergency services
    notifications = []
    for contact in contacts:
        notifications.append(f"Emergency alert sent to {contact['name']} at {contact['phone']}")

    return {
        'status': 'emergency_triggered',
        'contacts_notified': len(contacts),
        'location': location,
        'notifications': notifications
    }
