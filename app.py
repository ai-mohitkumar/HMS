from pathlib import Path
import io
import os
import sqlite3
import socket
import threading
import webbrowser

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from models import (
    calculate_wellness_score,
    check_medication_interactions,
    create_ai_insight,
    create_bill,
    create_caretaker,
    create_checkup,
    create_community,
    create_community_post,
    create_diet_meal,
    create_diet_plan,
    create_emergency_contact,
    create_hospitality,
    create_patient,
    create_quiz,
    create_quiz_question,
    create_user_role,
    delete_bill,
    delete_checkup,
    delete_hospitality,
    delete_patient,
    delete_vital,
    generate_otp,
    get_ai_insights,
    get_bill,
    get_bills,
    get_caretakers,
    get_checkup,
    get_checkups,
    get_communities,
    get_community_posts,
    get_conn,
    get_diet_meals,
    get_diet_plans,
    get_emergency_contacts,
    get_hospitality_record,
    get_hospitality,
    get_patient,
    get_patients,
    get_quiz_questions,
    get_quizzes,
    get_user_by_phone,
    get_user_roles,
    get_vital,
    get_wellness_scores,
    init_db,
    join_community,
    save_quiz_attempt,
    update_patient,
    update_bill,
    update_checkup,
    update_hospitality,
    update_vital,
    verify_otp,
)
from notification_utils import (
    send_appointment_reminder,
    send_bill_notification,
    send_checkup_results,
    send_comprehensive_patient_data_email,
    send_patient_report_email,
    send_report_to_admin,
    send_reports_to_all_patients,
)
from report_utils import generate_health_report, generate_patient_bill


BASE_DIR = Path(__file__).resolve().parent
STATIC_FILES = {
    "styles.css",
    "app.js",
    "login-styles.css",
    "professional-login-styles.css",
}

init_db()
app = Flask(__name__)
CORS(app)


def ensure_user_auth_columns():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users)")
    columns = {row["name"] for row in cur.fetchall()}

    if "email" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if "password" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN password TEXT")
    if "name" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN name TEXT")
    if "phone" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN phone TEXT")
    if "is_verified" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")

    cur.execute(
        """
        UPDATE users
        SET email = COALESCE(email, 'user' || id || '@hms.local'),
            password = COALESCE(password, 'demo123'),
            name = COALESCE(name, 'User ' || id),
            phone = COALESCE(phone, '+910000000' || printf('%03d', id))
        """
    )
    conn.commit()
    conn.close()


def create_web_user(email, password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = ?", (email,))
    existing = cur.fetchone()
    if existing:
        conn.close()
        return dict(existing)

    phone_seed = "".join(ch for ch in email if ch.isdigit())[-10:]
    phone_value = f"+91{phone_seed.zfill(10)}"

    suffix = 0
    while True:
        candidate = phone_value if suffix == 0 else f"{phone_value}{suffix}"
        try:
            cur.execute(
                """
                INSERT INTO users (name, email, password, phone, is_verified)
                VALUES (?, ?, ?, ?, 1)
                """,
                (email.split("@")[0], email, password, candidate),
            )
            conn.commit()
            user_id = cur.lastrowid
            cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = dict(cur.fetchone())
            conn.close()
            return user
        except sqlite3.IntegrityError:
            suffix += 1


def ensure_demo_user():
    ensure_user_auth_columns()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", ("admin@hms.local",))
    user = cur.fetchone()
    if not user:
        conn.close()
        return create_web_user("admin@hms.local", "demo123")
    conn.close()
    return dict(user)


def get_local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def is_cloud_runtime():
    return bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PORT"))


@app.route("/")
def serve_index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/<path:path>")
def serve_assets(path):
    if path.startswith("api/"):
        return jsonify({"status": "error", "message": "Not found"}), 404

    if path in STATIC_FILES or (BASE_DIR / path).exists():
        return send_from_directory(BASE_DIR, path)

    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    ensure_demo_user()
    return jsonify({"status": "ok"})


@app.route("/api/vitals", methods=["POST"])
def add_vital():
    data = request.json or {}
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO vitals (user_id, type, value, unit) VALUES (?, ?, ?, ?)",
        (data.get("user_id", 1), data["type"], str(data["value"]), data.get("unit", "")),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 201


@app.route("/api/vitals/<int:user_id>", methods=["GET"])
def get_vitals(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vitals WHERE user_id=? ORDER BY timestamp DESC", (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/vitals/<int:vital_id>", methods=["PUT"])
def edit_vital(vital_id):
    data = request.json or {}
    try:
        vital = get_vital(vital_id)
        if not vital:
            return jsonify({"status": "error", "message": "Vital not found"}), 404
        update_vital(vital_id, data)
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/vitals/<int:vital_id>", methods=["DELETE"])
def remove_vital(vital_id):
    try:
        if not get_vital(vital_id):
            return jsonify({"status": "error", "message": "Vital not found"}), 404
        delete_vital(vital_id)
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/symptoms", methods=["POST"])
def add_symptom():
    data = request.json or {}
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO symptoms (user_id, name, system, severity, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data.get("user_id", 1),
            data["name"],
            data.get("system", "General"),
            int(data.get("severity", 1)),
            data.get("notes", ""),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 201


@app.route("/api/symptoms/<int:user_id>", methods=["GET"])
def get_symptoms(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM symptoms WHERE user_id=? ORDER BY timestamp DESC", (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/meds", methods=["POST"])
def add_med():
    data = request.json or {}
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO medications (user_id, name, dose, schedule, start_date, end_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("user_id", 1),
            data["name"],
            data.get("dose", ""),
            data.get("schedule", ""),
            data.get("start_date", ""),
            data.get("end_date", ""),
            data.get("notes", ""),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 201


@app.route("/api/meds/<int:user_id>", methods=["GET"])
def get_meds(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM medications WHERE user_id=? ORDER BY id DESC", (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/appointments", methods=["POST"])
def add_appt():
    data = request.json or {}
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO appointments (user_id, doctor, datetime, type, notes) VALUES (?, ?, ?, ?, ?)",
        (
            data.get("user_id", 1),
            data.get("doctor", ""),
            data.get("datetime", ""),
            data.get("type", "in-person"),
            data.get("notes", ""),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 201


@app.route("/api/appointments/<int:user_id>", methods=["GET"])
def get_appts(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM appointments WHERE user_id=? ORDER BY datetime DESC", (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/report/<int:user_id>", methods=["GET"])
def get_report(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    user = dict(row) if row is not None else {"name": "User"}

    cur.execute("SELECT * FROM vitals WHERE user_id=? ORDER BY timestamp DESC LIMIT 100", (user_id,))
    vitals = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM symptoms WHERE user_id=? ORDER BY timestamp DESC LIMIT 100", (user_id,))
    symptoms = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM medications WHERE user_id=? ORDER BY id DESC", (user_id,))
    meds = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM appointments WHERE user_id=? ORDER BY datetime DESC", (user_id,))
    appts = [dict(r) for r in cur.fetchall()]
    conn.close()

    pdf_bytes = generate_health_report(user, vitals, symptoms, meds, appts)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"hms-report-user{user_id}.pdf",
    )


@app.route("/api/patients", methods=["POST"])
def add_patient():
    data = request.json or {}
    try:
        patient_id = create_patient(data)
        return jsonify({"status": "ok", "patient_id": patient_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/patients", methods=["GET"])
def get_all_patients():
    try:
        return jsonify(get_patients())
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/patient-health-summary", methods=["GET"])
def patient_health_summary():
    try:
        patients = get_patients()
        summary = []
        for patient in patients:
            patient_id = patient["id"]
            checkups = get_checkups(patient_id)
            hospitality = get_hospitality(patient_id)

            danger_reasons = []
            if any((checkup.get("result_status") or "").lower() == "critical" for checkup in checkups):
                danger_reasons.append("Critical checkup result")
            if any((checkup.get("result_status") or "").lower() == "abnormal" for checkup in checkups):
                danger_reasons.append("Abnormal test result")
            if any((stay.get("room_type") or "").upper() in {"ICU", "CCU"} for stay in hospitality):
                danger_reasons.append("High-risk hospital room")

            status = "danger" if danger_reasons else "normal"
            summary.append({
                "patient_id": patient_id,
                "name": patient.get("name"),
                "status": status,
                "color": "red" if status == "danger" else "green",
                "reason": ", ".join(danger_reasons) if danger_reasons else "Normal health condition",
                "checkup_count": len(checkups),
            })

        return jsonify(summary)
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/patients/<int:patient_id>", methods=["GET"])
def get_single_patient(patient_id):
    try:
        patient = get_patient(patient_id)
        if patient:
            return jsonify(patient)
        return jsonify({"status": "error", "message": "Patient not found"}), 404
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/patients/<int:patient_id>", methods=["PUT"])
def edit_single_patient(patient_id):
    data = request.json or {}
    try:
        patient = get_patient(patient_id)
        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404
        update_patient(patient_id, data)
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/patients/<int:patient_id>", methods=["DELETE"])
def remove_patient(patient_id):
    try:
        if not get_patient(patient_id):
            return jsonify({"status": "error", "message": "Patient not found"}), 404
        delete_patient(patient_id)
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/caretakers", methods=["POST"])
def add_caretaker():
    data = request.json or {}
    try:
        caretaker_id = create_caretaker(data)
        return jsonify({"status": "ok", "caretaker_id": caretaker_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/caretakers/<int:patient_id>", methods=["GET"])
def get_patient_caretakers(patient_id):
    try:
        return jsonify(get_caretakers(patient_id))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/hospitality", methods=["POST"])
def add_hospitality():
    data = request.json or {}
    try:
        hospitality_id = create_hospitality(data)
        return jsonify({"status": "ok", "hospitality_id": hospitality_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/hospitality/<int:patient_id>", methods=["GET"])
def get_patient_hospitality(patient_id):
    try:
        return jsonify(get_hospitality(patient_id))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/hospitality-record/<int:hospitality_id>", methods=["PUT"])
def edit_hospitality(hospitality_id):
    data = request.json or {}
    try:
        hospitality = get_hospitality_record(hospitality_id)
        if not hospitality:
            return jsonify({"status": "error", "message": "Hospitality record not found"}), 404
        update_hospitality(hospitality_id, data)
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/hospitality-record/<int:hospitality_id>", methods=["DELETE"])
def remove_hospitality(hospitality_id):
    try:
        if not get_hospitality_record(hospitality_id):
            return jsonify({"status": "error", "message": "Hospitality record not found"}), 404
        delete_hospitality(hospitality_id)
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/checkups", methods=["POST"])
def add_checkup():
    data = request.json or {}
    try:
        checkup_id = create_checkup(data)
        return jsonify({"status": "ok", "checkup_id": checkup_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/checkups/<int:patient_id>", methods=["GET"])
def get_patient_checkups(patient_id):
    try:
        return jsonify(get_checkups(patient_id))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/checkup-record/<int:checkup_id>", methods=["PUT"])
def edit_checkup(checkup_id):
    data = request.json or {}
    try:
        checkup = get_checkup(checkup_id)
        if not checkup:
            return jsonify({"status": "error", "message": "Checkup not found"}), 404
        update_checkup(checkup_id, data)
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/checkup-record/<int:checkup_id>", methods=["DELETE"])
def remove_checkup(checkup_id):
    try:
        if not get_checkup(checkup_id):
            return jsonify({"status": "error", "message": "Checkup not found"}), 404
        delete_checkup(checkup_id)
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/bills", methods=["POST"])
def add_bill():
    data = request.json or {}
    try:
        bill_id = create_bill(data)
        return jsonify({"status": "ok", "bill_id": bill_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/bills/<int:patient_id>", methods=["GET"])
def get_patient_bills(patient_id):
    try:
        return jsonify(get_bills(patient_id))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/bill-record/<int:bill_id>", methods=["PUT"])
def edit_bill(bill_id):
    data = request.json or {}
    try:
        bill = get_bill(bill_id)
        if not bill:
            return jsonify({"status": "error", "message": "Bill not found"}), 404
        update_bill(bill_id, data)
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/bill-record/<int:bill_id>", methods=["DELETE"])
def remove_bill(bill_id):
    try:
        if not get_bill(bill_id):
            return jsonify({"status": "error", "message": "Bill not found"}), 404
        delete_bill(bill_id)
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/patient-report/<int:patient_id>", methods=["GET"])
def get_patient_report(patient_id):
    try:
        patient = get_patient(patient_id)
        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404

        pdf_bytes = generate_patient_bill(
            patient,
            get_caretakers(patient_id),
            get_hospitality(patient_id),
            get_checkups(patient_id),
            get_bills(patient_id),
        )
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"patient-report-{patient_id}.pdf",
        )
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/send-patient-report/<int:patient_id>", methods=["POST"])
def send_patient_report_notification(patient_id):
    try:
        patient = get_patient(patient_id)
        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404
        return jsonify(send_patient_report_email(patient_id, patient, {"checkups": get_checkups(patient_id)}))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/send-report-to-admin/<int:patient_id>", methods=["POST"])
def send_report_to_admin_endpoint(patient_id):
    try:
        patient = get_patient(patient_id)
        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404
        checkups = get_checkups(patient_id)
        result = send_report_to_admin(patient_id, patient, {"checkups": checkups})
        return jsonify(result)
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/send-appointment-reminder/<int:patient_id>", methods=["POST"])
def send_appointment_reminder_notification(patient_id):
    try:
        patient = get_patient(patient_id)
        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404
        return jsonify(send_appointment_reminder(patient.get("email"), patient.get("name"), request.json or {}))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/send-bill-notification/<int:patient_id>", methods=["POST"])
def send_bill_notification_endpoint(patient_id):
    try:
        patient = get_patient(patient_id)
        bills = get_bills(patient_id)
        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404
        if not bills:
            return jsonify({"status": "error", "message": "No bills found"}), 404
        return jsonify(send_bill_notification(patient.get("email"), patient.get("name"), bills[0]))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/send-checkup-results/<int:patient_id>", methods=["POST"])
def send_checkup_results_notification(patient_id):
    try:
        patient = get_patient(patient_id)
        checkups = get_checkups(patient_id)
        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404
        if not checkups:
            return jsonify({"status": "error", "message": "No checkup results found"}), 404
        for checkup in checkups:
            checkup["patient_phone"] = patient.get("phone")
        return jsonify(send_checkup_results(patient.get("email"), patient.get("name"), checkups))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/send-reports-to-all-patients", methods=["POST"])
def send_reports_to_all_patients_endpoint():
    try:
        return jsonify(send_reports_to_all_patients())
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/send-comprehensive-patient-data/<int:patient_id>", methods=["POST"])
def send_comprehensive_patient_data_endpoint(patient_id):
    try:
        patient = get_patient(patient_id)
        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404
        payload = request.json or {}
        return jsonify(
            send_comprehensive_patient_data_email(
                patient_id,
                patient,
                payload.get("include_all_data", True),
            )
        )
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/login", methods=["POST"])
def login():
    ensure_user_auth_columns()
    data = request.json or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or "demo123"
    if not email:
        return jsonify({"status": "error", "message": "Email is required"}), 400

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()

    if user:
        cur.execute(
            "UPDATE users SET password = ?, name = COALESCE(name, ?) WHERE email = ?",
            (password, email.split("@")[0], email),
        )
        conn.commit()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        user_dict = dict(cur.fetchone())
        conn.close()
        return jsonify({"status": "ok", "user": user_dict})

    conn.close()
    user_dict = create_web_user(email, password)
    return jsonify({"status": "ok", "user": user_dict})


@app.route("/api/generate-otp", methods=["POST"])
def generate_otp_endpoint():
    phone = (request.json or {}).get("phone")
    if not phone:
        return jsonify({"status": "error", "message": "Phone number required"}), 400
    try:
        generate_otp(phone)
        return jsonify({"status": "ok", "message": "OTP sent successfully"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/verify-otp", methods=["POST"])
def verify_otp_endpoint():
    data = request.json or {}
    phone = data.get("phone")
    otp = data.get("otp")
    if not phone or not otp:
        return jsonify({"status": "error", "message": "Phone and OTP required"}), 400
    try:
        success, result = verify_otp(phone, otp)
        if success:
            return jsonify({"status": "ok", "user": get_user_by_phone(phone)})
        return jsonify({"status": "error", "message": result}), 400
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/user-roles/<int:user_id>", methods=["GET"])
def get_user_roles_endpoint(user_id):
    try:
        return jsonify({"roles": get_user_roles(user_id)})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/user-roles", methods=["POST"])
def add_user_role():
    data = request.json or {}
    try:
        role_id = create_user_role(data["user_id"], data["role"])
        return jsonify({"status": "ok", "role_id": role_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/communities", methods=["GET"])
def get_all_communities():
    try:
        return jsonify(get_communities())
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/communities", methods=["POST"])
def create_community_endpoint():
    try:
        community_id = create_community(request.json or {})
        return jsonify({"status": "ok", "community_id": community_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/communities/<int:community_id>/join", methods=["POST"])
def join_community_endpoint(community_id):
    data = request.json or {}
    try:
        join_community(community_id, data["user_id"])
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/communities/<int:community_id>/posts", methods=["GET"])
def get_community_posts_endpoint(community_id):
    try:
        return jsonify(get_community_posts(community_id))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/communities/<int:community_id>/posts", methods=["POST"])
def create_community_post_endpoint(community_id):
    data = request.json or {}
    data["community_id"] = community_id
    try:
        post_id = create_community_post(data)
        return jsonify({"status": "ok", "post_id": post_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/quizzes", methods=["GET"])
def get_all_quizzes():
    try:
        return jsonify(get_quizzes())
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/quizzes", methods=["POST"])
def create_quiz_endpoint():
    try:
        quiz_id = create_quiz(request.json or {})
        return jsonify({"status": "ok", "quiz_id": quiz_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/quizzes/<int:quiz_id>/questions", methods=["GET"])
def get_quiz_questions_endpoint(quiz_id):
    try:
        return jsonify(get_quiz_questions(quiz_id))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/quizzes/<int:quiz_id>/questions", methods=["POST"])
def create_quiz_question_endpoint(quiz_id):
    data = request.json or {}
    data["quiz_id"] = quiz_id
    try:
        question_id = create_quiz_question(data)
        return jsonify({"status": "ok", "question_id": question_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/quiz-attempts", methods=["POST"])
def save_quiz_attempt_endpoint():
    try:
        attempt_id = save_quiz_attempt(request.json or {})
        return jsonify({"status": "ok", "attempt_id": attempt_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/ai-insights/<int:user_id>", methods=["GET"])
def get_user_ai_insights(user_id):
    try:
        return jsonify(get_ai_insights(user_id))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/ai-insights", methods=["POST"])
def create_ai_insight_endpoint():
    try:
        insight_id = create_ai_insight(request.json or {})
        return jsonify({"status": "ok", "insight_id": insight_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/wellness-scores/<int:user_id>", methods=["GET"])
def get_user_wellness_scores(user_id):
    try:
        return jsonify(get_wellness_scores(user_id))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/wellness-scores/<int:user_id>/calculate", methods=["POST"])
def calculate_wellness_score_endpoint(user_id):
    try:
        return jsonify({"status": "ok", "score": calculate_wellness_score(user_id)})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/emergency-contacts/<int:user_id>", methods=["GET"])
def get_user_emergency_contacts(user_id):
    try:
        return jsonify(get_emergency_contacts(user_id))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/emergency-contacts", methods=["POST"])
def create_emergency_contact_endpoint():
    try:
        contact_id = create_emergency_contact(request.json or {})
        return jsonify({"status": "ok", "contact_id": contact_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/medication-interactions", methods=["POST"])
def check_medication_interactions_endpoint():
    try:
        interactions = check_medication_interactions((request.json or {}).get("medications", []))
        return jsonify({"interactions": interactions})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/diet-plans/<int:user_id>", methods=["GET"])
def get_user_diet_plans(user_id):
    try:
        return jsonify(get_diet_plans(user_id))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/diet-plans", methods=["POST"])
def create_diet_plan_endpoint():
    try:
        plan_id = create_diet_plan(request.json or {})
        return jsonify({"status": "ok", "plan_id": plan_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/diet-plans/<int:plan_id>/meals", methods=["GET"])
def get_diet_meals_endpoint(plan_id):
    try:
        return jsonify(get_diet_meals(plan_id))
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/diet-plans/<int:plan_id>/meals", methods=["POST"])
def create_diet_meal_endpoint(plan_id):
    data = request.json or {}
    data["diet_plan_id"] = plan_id
    try:
        meal_id = create_diet_meal(data)
        return jsonify({"status": "ok", "meal_id": meal_id}), 201
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


if __name__ == "__main__":
    ensure_demo_user()
    port = int(os.environ.get("PORT", "5000"))
    debug_mode = os.environ.get("FLASK_DEBUG", "1") == "1" and not is_cloud_runtime()

    if is_cloud_runtime():
        print(f"Cloud service listening on port {port}")
    else:
        local_ip = get_local_ip()
        print(f"Local device link: http://127.0.0.1:{port}/")
        print(f"Same Wi-Fi link:   http://{local_ip}:{port}/")
        if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}/")).start()

    app.run(debug=debug_mode, host="0.0.0.0", port=port)
