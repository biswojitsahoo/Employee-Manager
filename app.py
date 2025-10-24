from flask import Flask, render_template, request, redirect, url_for, flash
import oracledb
 
app = Flask(__name__)
app.secret_key = "replace_this_with_a_random_secret"  # change for production

oracledb.init_oracle_client(lib_dir= r"C:\oracle\instantclient_23_9")
# ---------- CONFIGURE YOUR ORACLE THIN CONNECTION HERE ----------
DB_USER = "Username"
DB_PASS = "Password"
DB_HOST = "Your host"      # e.g., 127.0.0.1 or db.example.com
DB_PORT = 1521             # as int or string
DB_SID  = "Your SID"       # e.g., ORCL
 

dsn = oracledb.makedsn(DB_HOST, DB_PORT, sid= DB_SID)
 
# Connect to the database
connection = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)
# ----------------------------------------------------------------
 
def fetch_all_employees(search_query=None):
    cur = connection.cursor()
    if search_query:
        like_q = f"%{search_query.upper()}%"
        cur.execute("""
            SELECT EMP_ID, EMP_NAME, EMP_SAL
            FROM EMPLOYEE
            WHERE UPPER(EMP_NAME) LIKE :q
            ORDER BY EMP_ID
        """, [like_q])
    else:
        cur.execute("SELECT EMP_ID, EMP_NAME, EMP_SAL FROM EMPLOYEE ORDER BY EMP_ID")
    rows = cur.fetchall()
    cur.close()
    return rows
 
@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    employees = fetch_all_employees(q if q else None)
    return render_template('index.html', employees=employees, q=q)
 
@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        salary = request.form.get('salary','').strip()
 
        if not name or not salary:
            flash("Name and salary are required", "danger")
            return redirect(url_for('add_employee'))
 
        try:
            cur = connection.cursor()
            # Use sequence EMP_SEQ for ID (create it in SQL below)
            cur.execute("INSERT INTO EMPLOYEE (EMP_ID, EMP_NAME, EMP_SAL) VALUES (EMP_SEQ.NEXTVAL, :1, :2)",
                        (name, float(salary)))
            connection.commit()
            cur.close()
            flash("Employee added successfully", "success")
        except Exception as e:
            flash(f"Error adding employee: {e}", "danger")
        return redirect(url_for('index'))
    return render_template('add.html')
 
@app.route('/edit/<int:emp_id>', methods=['GET', 'POST'])
def edit_employee(emp_id):
    cur = connection.cursor()
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        salary = request.form.get('salary','').strip()
        if not name or not salary:
            flash("Name and salary are required", "danger")
            return redirect(url_for('edit_employee', emp_id=emp_id))
        try:
            cur.execute("UPDATE EMPLOYEE SET EMP_NAME=:1, EMP_SAL=:2 WHERE EMP_ID=:3",
                        (name, float(salary), emp_id))
            connection.commit()
            flash("Employee updated successfully", "success")
        except Exception as e:
            flash(f"Error updating employee: {e}", "danger")
        finally:
            cur.close()
        return redirect(url_for('index'))
 
    cur.execute("SELECT EMP_NAME, EMP_SAL FROM EMPLOYEE WHERE EMP_ID=:1", [emp_id])
    row = cur.fetchone()
    cur.close()
    if not row:
        flash("Employee not found", "warning")
        return redirect(url_for('index'))
    employee = {"id": emp_id, "name": row[0], "salary": row[1]}
    return render_template('edit.html', employee=employee)
 
@app.route('/delete/<int:emp_id>', methods=['POST'])
def delete_employee(emp_id):
    try:
        cur = connection.cursor()
        cur.execute("DELETE FROM EMPLOYEE WHERE EMP_ID=:1", [emp_id])
        connection.commit()
        cur.close()
        flash("Employee deleted", "success")
    except Exception as e:
        flash(f"Error deleting employee: {e}", "danger")
    return redirect(url_for('index'))
 
if __name__ == '__main__':

    app.run(debug=True)
