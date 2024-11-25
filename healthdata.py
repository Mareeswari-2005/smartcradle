from flask import Flask, request, render_template_string, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ehealth.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

# Encryption Key (store securely in production)
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "doctor", "patient", "admin"

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(50), nullable=False)
    encrypted_data = db.Column(db.Text, nullable=False)

# HTML Templates
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>E-Healthcare System</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; padding: 20px; }
        h1 { color: #333; }
        form { margin-bottom: 20px; }
        label { display: inline-block; width: 150px; }
        button { background-color: #4CAF50; color: white; border: none; padding: 5px 10px; cursor: pointer; }
        button:hover { background-color: #45a049; }
    </style>
</head>
<body>
    <h1>Secure E-Healthcare System</h1>
    <h2>Register</h2>
    <form method="POST" action="/register">
        <label>Username:</label><input type="text" name="username" required><br>
        <label>Password:</label><input type="password" name="password" required><br>
        <label>Role:</label>
        <select name="role">
            <option value="doctor">Doctor</option>
            <option value="patient">Patient</option>
            <option value="admin">Admin</option>
        </select><br>
        <button type="submit">Register</button>
    </form>

    <h2>Add Record</h2>
    <form method="POST" action="/add_record">
        <label>Patient Name:</label><input type="text" name="patient_name" required><br>
        <label>Data:</label><input type="text" name="data" required><br>
        <button type="submit">Add Record</button>
    </form>

    <h2>Search</h2>
    <form method="POST" action="/search">
        <label>Keyword:</label><input type="text" name="keyword" required><br>
        <label>Role:</label>
        <select name="role">
            <option value="doctor">Doctor</option>
            <option value="patient">Patient</option>
            <option value="admin">Admin</option>
        </select><br>
        <button type="submit">Search</button>
    </form>
</body>
</html>
"""

SEARCH_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Search Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; padding: 20px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Search Results</h1>
    <ul>
        {% for result in results %}
        <li>Patient: {{ result.patient_name }}, Data: {{ result.data }}</li>
        {% endfor %}
    </ul>
    <a href="/">Go Back</a>
</body>
</html>
"""

# Routes
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
    role = request.form['role']
    user = User(username=username, password=password, role=role)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_record', methods=['POST'])
def add_record():
    patient_name = request.form['patient_name']
    data = request.form['data']
    encrypted_data = cipher_suite.encrypt(data.encode()).decode()
    record = Record(patient_name=patient_name, encrypted_data=encrypted_data)
    db.session.add(record)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']
    role = request.form['role']
    # Filter results based on role
    if role == "doctor" or role == "admin":
        results = Record.query.filter(Record.patient_name.contains(keyword)).all()
        decrypted_results = [{
            "patient_name": r.patient_name,
            "data": cipher_suite.decrypt(r.encrypted_data.encode()).decode()
        } for r in results]
        return render_template_string(SEARCH_HTML, results=decrypted_results)
    else:
        return "Unauthorized"

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
