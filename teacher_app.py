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
    subject_filter = session.get("subject")  # current teacher's subject or 'all'

    if os.path.exists('attendance.csv'):
        with open('attendance.csv', newline='') as f:
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
                if (not filter_date or record["date"] == filter_date):
                    if subject_filter == "all" or record["subject"].lower() == subject_filter:
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
    return jsonify(load_attendance(filter_date))

# ---------------- SUMMARY ----------------
@app.route('/summary')
def summary():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    filter_date = request.args.get("date")
    rows = load_attendance(filter_date)
    subjects = [r["subject"] for r in rows if r.get("subject")]
    counts = Counter(subjects)
    return jsonify({k.lower(): int(v) for k, v in counts.items()})

# ---------------- DOWNLOAD CSV ----------------
@app.route('/download')
def download():
    if not session.get('logged_in'):
        flash("⚠️ Please log in first")
        return redirect(url_for('login'))
    if os.path.exists('attendance.csv'):
        return send_file('attendance.csv', as_attachment=True)
    else:
        flash("⚠️ No attendance data yet")
        return redirect(url_for('dashboard'))

# ---------------- DOWNLOAD SUBJECT CSV ----------------
@app.route('/download/<subject>')
def download_subject(subject):
    if not session.get('logged_in'):
        flash("⚠️ Please log in first")
        return redirect(url_for('login'))

    rows = load_attendance()
    subject_rows = [r for r in rows if r.get("subject", "").lower() == subject.lower()]
    if not subject_rows:
        flash(f"⚠️ No attendance found for {subject.upper()}")
        return redirect(url_for('dashboard'))

    filename = f"attendance_{subject}.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date','Time','RollNo','Name','IP','Subject'])
        for r in subject_rows:
            writer.writerow([r["date"], r["time"], r["rollno"], r["name"], r["ip"], r["subject"]])
    return send_file(filename, as_attachment=True)

# ---------------- DOWNLOAD EXCEL (HOD ONLY) ----------------
@app.route('/download_excel')
def download_excel():
    if not session.get('logged_in'):
        flash("⚠️ Please log in first")
        return redirect(url_for('login'))

    if session.get("subject") != "all":
        flash("⚠️ Excel report is available only for HOD")
        return redirect(url_for('dashboard'))

    if not os.path.exists("attendance.csv"):
        flash("⚠️ No attendance data available")
        return redirect(url_for('dashboard'))

    df = pd.read_csv("attendance.csv")
    filename = "attendance_report.xlsx"
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        for subject in ["dsa", "dcn", "dbms", "atc", "ism", "evs"]:
            subject_df = df[df["Subject"].str.lower() == subject]
            if not subject_df.empty:
                subject_df.to_excel(writer, sheet_name=subject.upper(), index=False)
            else:
                pd.DataFrame(columns=df.columns).to_excel(writer, sheet_name=subject.upper(), index=False)
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
