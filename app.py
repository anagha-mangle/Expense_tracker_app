from flask import Flask, flash, render_template,redirect, session, url_for,request
from models import Transaction, db, User
from werkzeug.security import generate_password_hash , check_password_hash
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash("invalid email or password, please try again", 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    current_month = datetime.now().month
    current_year = datetime.now().year
    transactions = Transaction.query.filter_by(user_id=user.id).filter(db.extract('month', Transaction.date) == current_month,
        db.extract('year', Transaction.date) == current_year).all()

    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_expenses = sum(t.amount for t in transactions if t.amount < 0)
    balance = total_income + total_expenses

    budget_status = "within" if total_expenses <= user.budget else "over"

    return render_template('dashboard.html', user=user,total_income=total_income, total_expenses=total_expenses, balance=balance, transactions=transactions,budget_status=budget_status)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'user_id' not in session:
        flash('Please log in to add a transaction.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    amount = float(request.form['amount'])
    category = request.form['category']
    description = request.form['description']
    transaction_type = request.form['transaction_type'] 

    if transaction_type == 'income':
        amount = abs(amount)  # Ensure the amount is positive for income
    elif transaction_type == 'expense':
        amount = -abs(amount) 

    # Create and add a new transaction
    new_transaction = Transaction(amount=amount, category=category, description=description, user_id=user.id)
    db.session.add(new_transaction)
    db.session.commit()

    flash('Transaction added successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user session
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        age = request.form['age']
        password = request.form['password']
        budget = float(request.form['budget'])

        hashed_password = generate_password_hash(password)

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('email is already regsitered. please use another email','danger')
            return redirect(url_for('signup'))
        new_user = User(username=username, email=email, phone=phone, age=age, password=hashed_password, budget=budget)
        

        db.session.add(new_user)
        db.session.commit()

        flash('account created successfully! you can login now ','success')

        return redirect(url_for('login'))
    return render_template('signup.html')



if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True) 

