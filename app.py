from flask import Flask, render_template, request
import pandas as pd
import os
import psycopg2
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


app = Flask(__name__)

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

    try:
        df = pd.read_excel('KBF1JJ.xlsx', engine='openpyxl')
    except Exception as e:
        return f"<h3>Error reading KBF1JJ.xlsx: {e}</h3>"

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    if 'card code' not in df.columns:
        return "<h3>'card code' column missing in KBF1JJ.xlsx</h3>"

    df['card code'] = df['card code'].astype(str).str.strip()
    customer = df[df['card code'] == card_code]

    if customer.empty:
        return "<h3 style='color:red'>Customer doesn't exist</h3><a href='/'>Go Back</a>"

    customer_data = customer.iloc[0].to_dict()

    return render_template(
        'customer_details.html',
        customer=customer_data
    )


# ---------------- BENEFIT FORM ----------------
@app.route('/benefit_form', methods=['POST'])
def benefit_form():
    card_code = request.form['card_code']
    return render_template('benefit_form.html', card_code=card_code)


# ---------------- CHECK BENEFIT & SAVE ----------------
@app.route('/check_benefit', methods=['POST'])
def check_benefit():
    phone = request.form['phone'].strip()
    card_code = request.form['card_code'].strip()
    benefit_code = request.form['benefit_code'].strip()

    if not os.path.exists('KBF26BENEFITSCHEME.xlsx'):
        return "<h3>Benefit scheme file not found</h3>"

    try:
        df = pd.read_excel('KBF26BENEFITSCHEME.xlsx', engine='openpyxl')
    except Exception as e:
        return f"<h3>Error reading benefit scheme file: {e}</h3>"

    df.columns = df.columns.str.strip().str.lower()

    if 'benefit code' not in df.columns:
        return "<h3>'benefit code' column missing in scheme file</h3>"

    df['benefit code'] = df['benefit code'].astype(str).str.strip()
    benefit = df[df['benefit code'] == benefit_code]

    if benefit.empty:
        return "<h3 style='color:red'>Invalid Benefit Code</h3><a href='/'>Go Home</a>"

    benefit_data = benefit.iloc[0].to_dict()

    # Final data to save
    final_data = {
        'phone': phone,
        'card code': card_code,
        **benefit_data
    }

    output_file = 'submitted_data.xlsx'
    new_df = pd.DataFrame([final_data])

    try:
        if os.path.exists(output_file):
            old_df = pd.read_excel(output_file, engine='openpyxl')
            new_df = pd.concat([old_df, new_df], ignore_index=True)

        new_df.to_excel(output_file, index=False, engine='openpyxl')

    except PermissionError:
        return """
        <h3 style='color:red'>
        submitted_data.xlsx is currently OPEN in Excel.<br>
        Please close the file and try again.
        </h3>
        <a href='/'>Go Home</a>
        """

    return render_template(
        'benefit_details.html',
        phone=phone,
        card_code=card_code,
        benefit=final_data
    )


# ---------------- VIEW BENEFIT SCHEMES ----------------
@app.route('/view_benefits')
def view_benefits():
    if not os.path.exists('KBF26BENEFITSCHEME.xlsx'):
        return "<h3>Benefit scheme file not found</h3>"

    df = pd.read_excel('KBF26BENEFITSCHEME.xlsx', engine='openpyxl')
    return df.to_html(index=False)
@app.route('/view_submitted')
def view_submitted():
    import os
    if not os.path.exists('submitted_data.xlsx'):
        return "No data found"

    df = pd.read_excel('submitted_data.xlsx', engine='openpyxl')
    return df.to_html(index=False)
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
 

# ---------------- RUN APP ----------------
if __name__ == '__main__':
    app.run()



