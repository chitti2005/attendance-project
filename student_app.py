from flask import Flask, render_template, request, redirect, url_for, flash
import csv, datetime, os
app = Flask(__name__)
app.secret_key = "student_secret"

def load_students():
    students = {}
    with open('students.csv', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            students[row['RollNo']] = {"pin": row['PIN'], "name": row['Name']}
    return students

def has_attended_today(roll):
    today = datetime.date.today().isoformat()
    if not os.path.exists('attendance.csv'):
        return False
    with open('attendance.csv', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Date'] == today and row['RollNo'] == roll:
                return True
    return False

def save_attendance(roll, ip, subject):
    students = load_students()
    name = students[roll]["name"]
    now = datetime.datetime.now()
    file_exists = os.path.exists('attendance.csv')
    with open('attendance.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date','Time','RollNo','Name','IP','Subject'])
        writer.writerow([now.date(), now.strftime("%H:%M:%S"), roll, name, ip, subject])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    roll = request.form.get('roll').strip()
    pin = request.form.get('pin').strip()
    students = load_students()

    if roll not in students:
        flash("❌ Roll number not found")
        return redirect(url_for('index'))

    if students[roll]["pin"] != pin:
        flash("❌ Wrong PIN")
        return redirect(url_for('index'))

    if has_attended_today(roll):
        flash("⚠️ Already marked today")
        return redirect(url_for('index'))

    subject = request.form.get("subject")
    save_attendance(roll, request.remote_addr, subject)
    flash("✅ Attendance marked")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)  # Student server on port 5001
