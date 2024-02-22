from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import sqlite3

app = Flask(__name__)

DATABASE = 'forms.db'

def create_tables():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS forms
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, fields TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS form_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, form_id INTEGER, data TEXT)''')
    conn.commit()
    conn.close()

create_tables()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_form', methods=['POST'])
def save_form():
    try:
        form_title = request.form['form_title']
        field_types = request.form.getlist('field_type[]')
        field_labels = request.form.getlist('field_label[]')
        field_required = request.form.getlist('field_required[]')  # New
        # Convert '0' or '1' to boolean
        field_required = [bool(int(value)) for value in field_required]
        
        fields = [{'type': field_types[i], 'label': field_labels[i], 'required': field_required[i]} for i in range(len(field_types))]  # Modified
        fields_json = json.dumps(fields)

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO forms (title, fields) VALUES (?, ?)", (form_title, fields_json))
        form_id = c.lastrowid
        conn.commit()
        conn.close()

        return redirect(url_for('display_form', form_id=form_id))
    except Exception as e:
        return str(e)

@app.route('/display_form/<int:form_id>', methods=['GET', 'POST'])
def display_form(form_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT title, fields FROM forms WHERE id=?", (form_id,))
        form = c.fetchone()
        if form:
            form_title, fields_json = form
            fields = json.loads(fields_json)
            if request.method == 'POST':
                data = request.form.to_dict(flat=False)
                data_json = json.dumps(data)
                c.execute("INSERT INTO form_data (form_id, data) VALUES (?, ?)", (form_id, data_json))
                conn.commit()
            # Fetch form data
            c.execute("SELECT data FROM form_data WHERE form_id=?", (form_id,))
            form_data_rows = c.fetchall()
            form_data = []
            for row in form_data_rows:
                data_json = row[0]
                form_data.append(json.loads(data_json))
            conn.close()
            return render_template('display_form.html', form_title=form_title, fields=fields, form_id=form_id, form_data=form_data)
        else:
            return "Form not found"
    except Exception as e:
        return str(e)
    
@app.route('/submit_form/<int:form_id>', methods=['POST'])
def submit_form(form_id):
    try:
        data = request.form.to_dict(flat=False)
        data_json = json.dumps(data)

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO form_data (form_id, data) VALUES (?, ?)", (form_id, data_json))
        conn.commit()
        conn.close()

        return redirect(url_for('display_form_data', form_id=form_id))

    except Exception as e:
        return str(e)

@app.route('/display_form_data/<int:form_id>')
def display_form_data(form_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT data FROM form_data WHERE form_id=?", (form_id,))
        form_data_rows = c.fetchall()
        conn.close()

        form_data = []
        for row in form_data_rows:
            data_json = row[0]
            form_data.append(json.loads(data_json))

        if form_data:
            return render_template('display_form_data.html', form_data=form_data)
        else:
            return "No form data found for the specified form ID"
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(debug=True)
