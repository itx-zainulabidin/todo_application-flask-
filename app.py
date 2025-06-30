from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'a secret_key'

# Configure DB
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'todos.db')
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy=True)

# Todo Model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    # discription = db.Column(db.String(500), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created, please login')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('todos'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/todos', methods=['GET', 'POST'])
def todos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        content = request.form['content']
        new_todo = Todo(content=content, user_id=session['user_id'])
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for('todos'))

    user_todos = Todo.query.filter_by(user_id=session['user_id']).order_by(Todo.date_created.desc()).all()
    return render_template('todos.html', todos=user_todos)

@app.route('/delete/<int:id>')
def delete(id):
    todo = Todo.query.get_or_404(id)
    if todo.user_id != session['user_id']:
        return redirect(url_for('todos'))
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('todos'))

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    todo = Todo.query.get_or_404(id)
    if todo.user_id != session['user_id']:
        return redirect(url_for('todos'))
    if request.method == 'POST':
        todo.content = request.form['content']
        db.session.commit()
        return redirect(url_for('todos'))
    return render_template('update.html', todo=todo)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,port=100)