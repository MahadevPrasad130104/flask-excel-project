from flask import Flask, render_template, request, redirect
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS submitted_data (
            id SERIAL PRIMARY KEY,
            phone VARCHAR(20),
            card_code VARCHAR(50),
            benefit_code VARCHAR(50)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            card_code VARCHAR(50) UNIQUE,
            name VARCHAR(100),
            amount_paid VARCHAR(50),
            status VARCHAR(50)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS benefits (
            id SERIAL PRIMARY KEY,
            benefit_code VARCHAR(50) UNIQUE,
            vessel_type VARCHAR(100),
            vessel_description TEXT,
            vessel_weight VARCHAR(50),
            mutton VARCHAR(50),
            chicken VARCHAR(50),
            egg_dozen VARCHAR(50)
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


# ---------------- CUSTOMER CHECK ----------------

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

    return render_template('customer_details.html', customer=customer_data)


# ---------------- BENEFIT FORM ----------------

@app.route('/benefit_form', methods=['POST'])
def benefit_form():
    card_code = request.form['card_code']
    return render_template('benefit_form.html', card_code=card_code)


# ---------------- CHECK BENEFIT ----------------

@app.route('/check_benefit', methods=['POST'])
def check_benefit():
    phone = request.form['phone'].strip()
    card_code = request.form['card_code'].strip()
    benefit_code = request.form['benefit_code'].strip()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT benefit_code,
               vessel_type,
               vessel_description,
               vessel_weight,
               mutton,
               chicken,
               egg_dozen
        FROM benefits
        WHERE benefit_code = %s
    """, (benefit_code,))

    benefit = cur.fetchone()

    if not benefit:
        cur.close()
        conn.close()
        return "<h3 style='color:red'>Invalid Benefit Code</h3><a href='/'>Go Home</a>"

    cur.execute("""
        INSERT INTO submitted_data (phone, card_code, benefit_code)
        VALUES (%s, %s, %s)
    """, (phone, card_code, benefit_code))

    conn.commit()
    cur.close()
    conn.close()

    benefit_data = {
        "benefit code": benefit[0],
        "vessel type": benefit[1],
        "vessel description": benefit[2],
        "vessel weight": benefit[3],
        "mutton": benefit[4],
        "chicken": benefit[5],
        "egg (in dozen)": benefit[6]
    }

    return render_template(
        'benefit_details.html',
        phone=phone,
        card_code=card_code,
        benefit=benefit_data
    )


# ---------------- VIEW SUBMITTED (PROFESSIONAL UI) ----------------

@app.route('/view_submitted')
def view_submitted():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, phone, card_code, benefit_code
        FROM submitted_data
        ORDER BY id DESC;
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Submitted Records</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">

    <div class="container mt-5">
        <div class="card shadow-lg">
            <div class="card-header bg-dark text-white">
                <h4 class="mb-0">Submitted Records</h4>
            </div>
            <div class="card-body">
    """

    if not rows:
        html += "<div class='alert alert-info'>No submissions yet.</div>"
    else:
        html += """
        <table class="table table-bordered table-hover">
            <thead class="table-dark">
                <tr>
                    <th>Phone</th>
                    <th>Card Code</th>
                    <th>Benefit Code</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
        """

        for row in rows:
            html += f"""
            <tr>
                <td>{row[1]}</td>
                <td>{row[2]}</td>
                <td>{row[3]}</td>
                <td>
                    <a href="/delete/{row[0]}" 
                       class="btn btn-danger btn-sm"
                       onclick="return confirm('Are you sure you want to delete this record?')">
                       Delete
                    </a>
                </td>
            </tr>
            """

        html += "</tbody></table>"

    html += """
            </div>
        </div>
    </div>

    </body>
    </html>
    """

    return html


# ---------------- DELETE ----------------

@app.route('/delete/<int:id>')
def delete_record(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM submitted_data WHERE id = %s;", (id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect('/view_submitted')


# ---------------- VIEW BENEFITS (PROFESSIONAL UI) ----------------

@app.route('/view_benefits')
def view_benefits():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT benefit_code,
               vessel_type,
               vessel_description,
               vessel_weight,
               mutton,
               chicken,
               egg_dozen
        FROM benefits
        ORDER BY id DESC;
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Benefits Master</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">

    <div class="container mt-5">
        <div class="card shadow-lg">
            <div class="card-header bg-primary text-white">
                <h4 class="mb-0">Benefits Master Data</h4>
            </div>
            <div class="card-body">
    """

    if not rows:
        html += "<div class='alert alert-warning'>No benefits found.</div>"
    else:
        html += """
        <table class="table table-striped table-bordered">
            <thead class="table-dark">
                <tr>
                    <th>Benefit Code</th>
                    <th>Vessel Type</th>
                    <th>Description</th>
                    <th>Weight</th>
                    <th>Mutton</th>
                    <th>Chicken</th>
                    <th>Egg (Dozen)</th>
                </tr>
            </thead>
            <tbody>
        """

        for row in rows:
            html += f"""
            <tr>
                <td>{row[0]}</td>
                <td>{row[1]}</td>
                <td>{row[2]}</td>
                <td>{row[3]}</td>
                <td>{row[4]}</td>
                <td>{row[5]}</td>
                <td>{row[6]}</td>
            </tr>
            """

        html += "</tbody></table>"

    html += """
            </div>
        </div>
    </div>

    </body>
    </html>
    """

    return html


# ---------------- RUN ----------------

if __name__ == '__main__':
    app.run()
