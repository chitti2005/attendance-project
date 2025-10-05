from flask import Flask, render_template, send_file, flash, redirect, url_for, jsonify, request, session
import csv, os, pandas as pd
from collections import Counter

app = Flask(__name__)
app.secret_key = "teacher_secret"

# ---------------- LOAD TEACHER DATA ----------------
def load_teachers():
    if os.path.exists("teachers.csv"):
        df = pd.read_csv("teachers.csv")
        return df.to_dict(orient="records")
    return []

# ---------------- LOAD ATTENDANCE ----------------
def load_attendance(filter_date=None):
    rows = []
    subject_filter = session.get("subject")

    if subject_filter == "all":  # HOD
        subjects = ["dsa", "dcn", "dbms", "atc", "ism", "evs"]
    else:
        subjects = [subject_filter]

    for sub in subjects:
        file_name = f"attendance_{sub}.csv"
        if os.path.exists(file_name):
            with open(file_name, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    record = {
                        "date": row.get("Date", ""),
                        "time": row.get("Time", ""),
                        "rollno": row.get("RollNo", ""),
                        "name": row.get("Name", ""),
                        "ip": row.get("IP", ""),
                        "subject": row.get("Subject", "")
                    }
                    if not filter_date or record["date"] == filter_date:
                        rows.append(record)
    return rows

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username").strip().lower()
        password = request.form.get("password").strip()
        teachers = load_teachers()

        for t in teachers:
            if t["Username"].lower() == username and t["Password"] == password:
                session['logged_in'] = True
                session['teacher_name'] = t["Name"]
                session['subject'] = t["Subject"].lower()
                flash(f"✅ Welcome {t['Name']} ({t['Subject'].upper()})")
                return redirect(url_for('dashboard'))

        flash("❌ Invalid username or password")
        return redirect(url_for('login'))
    return render_template('login.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("✅ Logged out successfully.")
    return redirect(url_for('login'))

# ---------------- DASHBOARD ----------------
@app.route('/')
def dashboard():
    if not session.get('logged_in'):
        flash("⚠️ Please log in first")
        return redirect(url_for('login'))
    return render_template('teacher.html')

# ---------------- DATA ----------------
@app.route('/data')
def data():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    filter_date = request.args.get("date")
    rows = load_attendance(filter_date)
    return jsonify(rows)

# ---------------- DOWNLOAD CSV ----------------
@app.route('/download')
def download():
    if not session.get('logged_in'):
        flash("⚠️ Please log in first")
        return redirect(url_for('login'))

    subject_filter = session.get("subject")
    if subject_filter == "all":
        flash("ℹ️ HOD can use Excel report for all subjects.")
        return redirect(url_for('dashboard'))

    file_name = f"attendance_{subject_filter}.csv"
    if os.path.exists(file_name):
        return send_file(file_name, as_attachment=True)
    else:
        flash(f"⚠️ No attendance data found for {subject_filter.upper()}")
        return redirect(url_for('dashboard'))

# ---------------- DOWNLOAD EXCEL (HOD ONLY) ----------------
@app.route('/download_excel')
def download_excel():
    if not session.get('logged_in'):
        flash("⚠️ Please log in first")
        return redirect(url_for('login'))

    if session.get("subject") != "all":
        flash("⚠️ Excel report is available only for HOD")
        return redirect(url_for('dashboard'))

    filename = "attendance_report.xlsx"
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        for sub in ["dsa", "dcn", "dbms", "atc", "ism", "evs"]:
            file_name = f"attendance_{sub}.csv"
            if os.path.exists(file_name):
                df = pd.read_csv(file_name)
                df.to_excel(writer, sheet_name=sub.upper(), index=False)
            else:
                pd.DataFrame(columns=['Date','Time','RollNo','Name','IP','Subject']).to_excel(writer, sheet_name=sub.upper(), index=False)

    return send_file(filename, as_attachment=True)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
