from flask import Flask, render_template, request, redirect, url_for, flash
import csv, datetime, os

app = Flask(__name__)
app.secret_key = "student_secret"

# ---------------- LOAD STUDENTS ----------------
def load_students():
    students = {}
    if os.path.exists('students.csv'):
        with open('students.csv', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                students[row['RollNo']] = {"pin": row['PIN'], "name": row['Name']}
    return students

# ---------------- CHECK DUPLICATE ATTENDANCE ----------------
def has_attended_today(roll, subject):
    today = str(datetime.date.today())
    file_name = f"attendance_{subject.lower()}.csv"
    if not os.path.exists(file_name):
        return False

    with open(file_name, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (
                row['RollNo'].strip().lower() == roll.strip().lower()
                and row['Date'].strip() == today
                and row['Subject'].strip().lower() == subject.lower()
            ):
                return True
    return False

# ---------------- SAVE ATTENDANCE ----------------
def save_attendance(roll, ip, subject):
    students = load_students()
    name = students.get(roll, {}).get("name", "Unknown")
    now = datetime.datetime.now()
    today = str(now.date())
    subject = subject.lower()

    file_name = f"attendance_{subject}.csv"
    file_exists = os.path.exists(file_name)

    with open(file_name, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Time', 'RollNo', 'Name', 'IP', 'Subject'])
        writer.writerow([today, now.strftime("%H:%M:%S"), roll, name, ip, subject])
    return True

# ---------------- ROUTES ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    roll = request.form.get('roll').strip()
    pin = request.form.get('pin').strip()
    subject = request.form.get("subject").strip().lower()
    ip = request.remote_addr

    students = load_students()

    # Check student
    if roll not in students:
        flash("❌ Roll number not found")
        return redirect(url_for('index'))

    # Check PIN
    if students[roll]["pin"] != pin:
        flash("❌ Wrong PIN")
        return redirect(url_for('index'))

    # Check duplicate for that subject
    if has_attended_today(roll, subject):
        flash("⚠️ You have already marked attendance today for this subject.")
        return redirect(url_for('index'))

    # Save attendance
    save_attendance(roll, ip, subject)
    flash(f"✅ Attendance marked successfully for {subject.upper()}!")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
