
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
import csv, datetime, os

app = Flask(__name__)
app.secret_key = "secret123"   # needed for flash messages

@app.route('/download')
def download():
    if os.path.exists('attendance.csv'):
        return send_file('attendance.csv', as_attachment=True)
    else:
        flash("⚠️ No attendance yet")
        return redirect(url_for('teacher'))

app = Flask(__name__)
app.secret_key = "secret123"   # needed for flash messages

@app.route('/')
def index():
    return render_template('index.html')

def load_students():
    students = {}
    with open('students.csv', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            students[row['RollNo']] = row['PIN']
    return students


def save_attendance(roll, ip, subject="General"):
    students = load_students()
    name = "Unknown"
    with open('students.csv', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['RollNo'] == roll:
                name = row['Name']
                break

    file_exists = os.path.exists('attendance.csv')
    now = datetime.datetime.now()
    with open('attendance.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Time', 'RollNo', 'Name', 'IP', 'Subject'])
        writer.writerow([now.date(), now.strftime("%H:%M:%S"), roll, name, ip, subject])

# Check if a student has already marked attendance today
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

@app.route('/submit', methods=['POST'])
def submit():
    roll = request.form.get('roll').strip()
    pin = request.form.get('pin').strip()
    students = load_students()

    if roll not in students:
        flash("❌ Roll number not found")
        return redirect(url_for('index'))

    if students[roll] != pin:
        flash("❌ Wrong PIN")
        return redirect(url_for('index'))

    if has_attended_today(roll):
        flash("⚠️ Already marked today")
        return redirect(url_for('index'))

    save_attendance(roll, request.remote_addr, subject="Math")
    flash("✅ Attendance marked for Roll No " + roll)
    return redirect(url_for('index'))

@app.route('/teacher')
def teacher():
    rows = []
    if os.path.exists('attendance.csv'):
        with open('attendance.csv', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    return render_template('teacher.html', rows=rows)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)


