from flask import Flask, render_template, request
import pandas as pd
import os
import psycopg2

app = Flask(__name__)

# ---------------- DATABASE CONNECTION ----------------

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def create_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS submitted_data (
            id SERIAL PRIMARY KEY,
            phone VARCHAR(20),
            card_code VARCHAR(50),
            benefit_code VARCHAR(50)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

create_table()

# ---------------- HOME ----------------

@app.route('/')
def home():
    return render_template('form1.html')

# ---------------- CUSTOMER VERIFICATION ----------------

@app.route('/check_customer', methods=['POST'])
def check_customer():
    card_code = request.form['card_code'].strip()

    if not os.path.exists('KBF1JJ.xlsx'):
        return "<h3>KBF1JJ.xlsx file not found</h3>"

    df = pd.read_excel('KBF1JJ.xlsx', engine='openpyxl')
    df.columns = df.columns.str.strip().str.lower()

    if 'card code' not in df.columns:
        return "<h3>'card code' column missing</h3>"

    df['card code'] = df['card code'].astype(str).str.strip()
    customer = df[df['card code'] == card_code]

    if customer.empty:
        return "<h3 style='color:red'>Customer doesn't exist</h3><a href='/'>Go Back</a>"

    return render_template(
        'customer_details.html',
        customer=customer.iloc[0].to_dict()
    )

# ---------------- BENEFIT FORM ----------------

@app.route('/benefit_form', methods=['POST'])
def benefit_form():
    card_code = request.form['card_code']
    return render_template('benefit_form.html', card_code=card_code)

# ---------------- CHECK BENEFIT & SAVE TO DATABASE ----------------

@app.route('/check_benefit', methods=['POST'])
def check_benefit():
    phone = request.form['phone'].strip()
    card_code = request.form['card_code'].strip()
    benefit_code = request.form['benefit_code'].strip()

    if not os.path.exists('KBF26BENEFITSCHEME.xlsx'):
        return "<h3>Benefit scheme file not found</h3>"

    df = pd.read_excel('KBF26BENEFITSCHEME.xlsx', engine='openpyxl')
    df.columns = df.columns.str.strip().str.lower()

    if 'benefit code' not in df.columns:
        return "<h3>'benefit code' column missing</h3>"

    df['benefit code'] = df['benefit code'].astype(str).str.strip()
    benefit = df[df['benefit code'] == benefit_code]

    if benefit.empty:
        return "<h3 style='color:red'>Invalid Benefit Code</h3><a href='/'>Go Home</a>"

    # SAVE TO DATABASE
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO submitted_data (phone, card_code, benefit_code)
        VALUES (%s, %s, %s)
    """, (phone, card_code, benefit_code))

    conn.commit()
    cur.close()
    conn.close()

    return render_template(
        'benefit_details.html',
        phone=phone,
        card_code=card_code,
        benefit=benefit.iloc[0].to_dict()
    )

# ---------------- VIEW BENEFIT SCHEMES ----------------

@app.route('/view_benefits')
def view_benefits():
    if not os.path.exists('KBF26BENEFITSCHEME.xlsx'):
        return "<h3>Benefit scheme file not found</h3>"

    df = pd.read_excel('KBF26BENEFITSCHEME.xlsx', engine='openpyxl')
    return df.to_html(index=False)

# ---------------- VIEW SUBMITTED DATA FROM DATABASE ----------------

@app.route('/view_submitted')
def view_submitted():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT phone, card_code, benefit_code FROM submitted_data ORDER BY id DESC;")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    if not rows:
        return "No data in database"

    html = "<h2>Submitted Data</h2><table border='1'><tr><th>Phone</th><th>Card Code</th><th>Benefit Code</th></tr>"
    for row in rows:
        html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>"
    html += "</table>"

    return html

# ---------------- RUN ----------------

if __name__ == '__main__':
    app.run()
