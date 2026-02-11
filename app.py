from flask import Flask, render_template, request
import pandas as pd
import os
import psycopg2

app = Flask(__name__)

# ---------------- DATABASE CONNECTION ----------------

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def create_table():
    conn = get_connection()
    cur = conn.cursor()

    # Submitted data table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS submitted_data (
            id SERIAL PRIMARY KEY,
            phone VARCHAR(20),
            card_code VARCHAR(50),
            benefit_code VARCHAR(50)
        );
    """)

    # Customer master table (KBF1JJ)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            card_code VARCHAR(50) UNIQUE,
            name VARCHAR(100),
            amount_paid VARCHAR(50),
            status VARCHAR(50)
        );
    """)

    # Benefit master table (KBF26BENEFITSCHEME)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS benefits (
            id SERIAL PRIMARY KEY,
            benefit_code VARCHAR(50) UNIQUE,
            benefit_name VARCHAR(100),
            description TEXT
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

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT card_code, name, amount_paid, status
        FROM customers
        WHERE card_code = %s
    """, (card_code,))

    customer = cur.fetchone()

    cur.close()
    conn.close()

    if not customer:
        return "<h3 style='color:red'>Customer doesn't exist</h3><a href='/'>Go Back</a>"

    customer_data = {
        "card code": customer[0],
        "name": customer[1],
        "amount paid": customer[2],
        "status": customer[3]
    }

    return render_template(
        'customer_details.html',
        customer=customer_data
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

    conn = get_connection()
    cur = conn.cursor()

    # Check if benefit exists
    cur.execute("""
        SELECT benefit_code, benefit_name, description
        FROM benefits
        WHERE benefit_code = %s
    """, (benefit_code,))

    benefit = cur.fetchone()

    if not benefit:
        cur.close()
        conn.close()
        return "<h3 style='color:red'>Invalid Benefit Code</h3><a href='/'>Go Home</a>"

    # Save submission
    cur.execute("""
        INSERT INTO submitted_data (phone, card_code, benefit_code)
        VALUES (%s, %s, %s)
    """, (phone, card_code, benefit_code))

    conn.commit()
    cur.close()
    conn.close()

    benefit_data = {
        "benefit code": benefit[0],
        "benefit name": benefit[1],
        "description": benefit[2]
    }

    return render_template(
        'benefit_details.html',
        phone=phone,
        card_code=card_code,
        benefit=benefit_data
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
@app.route('/load_master_data')
def load_master_data():
    conn = get_connection()
    cur = conn.cursor()

    # Load customers from Excel
    if os.path.exists('KBF1JJ.xlsx'):
        df = pd.read_excel('KBF1JJ.xlsx', engine='openpyxl')
        df.columns = df.columns.str.strip().str.lower()

        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO customers (card_code, name, amount_paid, status)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (card_code) DO NOTHING;
            """, (
                str(row['card code']),
                str(row['name']),
                str(row['amount paid']),
                str(row['status'])
            ))

    # Load benefits from Excel
    if os.path.exists('KBF26BENEFITSCHEME.xlsx'):
        df2 = pd.read_excel('KBF26BENEFITSCHEME.xlsx', engine='openpyxl')
        df2.columns = df2.columns.str.strip().str.lower()

        for _, row in df2.iterrows():
            cur.execute("""
                INSERT INTO benefits (benefit_code, benefit_name, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (benefit_code) DO NOTHING;
            """, (
                str(row['benefit code']),
                str(row.get('benefit name', '')),
                str(row.get('description', ''))
            ))

    conn.commit()
    cur.close()
    conn.close()

    return "Master data loaded successfully!"

if __name__ == '__main__':
    app.run()





