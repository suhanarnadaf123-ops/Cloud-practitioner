from flask import Flask, render_template, request, redirect, session
import mysql.connector
from mysql.connector import pooling

app = Flask(__name__)
app.secret_key = "secretkey"

dbconfig = {
    "host": "telesupporthub.cpu6q8g46i2l.ap-south-1.rds.amazonaws.com",
    "user": "admin",
    "password": "YOUR-PASSWORD",
    "database": "telesupporthub",
    "port": 3306
}

pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **dbconfig)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form['mobile']
        email = request.form['email']
        password = request.form['password']
        address = request.form['address']

        db = pool.get_connection()
        cursor = db.cursor()
        query = """
        INSERT INTO customers(name,mobile,email,password,address)
        VALUES(%s,%s,%s,%s,%s)
        """
        values = (name,mobile,email,password,address)
        cursor.execute(query, values)
        db.commit()
        cursor.close()
        db.close()

        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = pool.get_connection()
        cursor = db.cursor()
        query = "SELECT * FROM customers WHERE email=%s AND password=%s"
        cursor.execute(query,(email,password))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            session['user'] = user[1]
            session['customer_id'] = user[0]
            session['role'] = 'customer'
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid email or password.")

    return render_template('login.html')

@app.route('/agent', methods=['GET','POST'])
def agent_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = pool.get_connection()
        cursor = db.cursor()
        query = "SELECT * FROM agents WHERE email=%s AND password=%s"
        try:
            cursor.execute(query,(email,password))
            agent = cursor.fetchone()
        except:
            agent = None
        cursor.close()
        db.close()

        if agent:
            session['agent'] = agent[1]
            session['agent_id'] = agent[0]
            session['role'] = 'agent'
            return redirect('/view_ticket')
        else:
            return render_template('agent_login.html', error="Invalid agent credentials.")

    return render_template('agent_login.html')

@app.route('/dashboard')
def dashboard():
    if 'customer_id' not in session:
        return redirect('/login')
    return render_template('dashboard.html')

@app.route('/raise_ticket', methods=['GET','POST'])
def raise_ticket():
    if 'customer_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        description = request.form['description']
        plan_type = request.form['plan_type']
        priority = request.form['priority']

        db = pool.get_connection()
        cursor = db.cursor()
        query = """
        INSERT INTO tickets(customer_id,description,plan_type,priority)
        VALUES(%s,%s,%s,%s)
        """
        values = (
            session['customer_id'],
            description,
            plan_type,
            priority
        )
        cursor.execute(query, values)
        db.commit()
        cursor.close()
        db.close()

        return redirect('/dashboard')

    return render_template('raise_ticket.html')

@app.route('/ticket_history', methods=['GET'])
def ticket_history():
    if 'customer_id' not in session:
        return redirect('/login')

    db = pool.get_connection()
    cursor = db.cursor(dictionary=True)
    try:
        query = "SELECT * FROM tickets WHERE customer_id = %s"
        cursor.execute(query, (session['customer_id'],))
        tickets = cursor.fetchall()
    except:
        tickets = []
    cursor.close()
    db.close()

    return render_template('ticket_history.html', tickets=tickets)

@app.route('/choose_category', methods=['GET'])
def choose_category():
    if 'customer_id' not in session:
        return redirect('/login')

    db = pool.get_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()
    except:
        categories = []
    cursor.close()
    db.close()

    return render_template('choose_category.html', categories=categories)

@app.route('/buy_service', methods=['POST'])
def buy_service():
    if 'customer_id' not in session:
        return redirect('/login')
        
    service_id = request.form.get('service_id')
    
    db = pool.get_connection()
    cursor = db.cursor()
    try:
        query = "INSERT INTO orders(customer_id, service_id) VALUES(%s, %s)"
        cursor.execute(query, (session['customer_id'], service_id))
        db.commit()
    except:
        pass
    cursor.close()
    db.close()

    return redirect('/dashboard')

@app.route('/view_ticket', methods=['GET', 'POST'])
def view_ticket():
    if 'agent_id' not in session:
        return redirect('/agent')

    db = pool.get_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM tickets")
        tickets = cursor.fetchall()
    except:
        tickets = []
    cursor.close()
    db.close()

    return render_template('view_ticket.html', tickets=tickets)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)