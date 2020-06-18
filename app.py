from flask import Flask, request, render_template, redirect, flash, session, url_for, logging
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
from functools import wraps
import warnings
import os



warnings.filterwarnings("ignore")

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
db = SQLAlchemy(app)

class NewsPost(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(200), nullable = False)
    content = db.Column(db.Text, nullable = False)
    author = db.Column(db.String(100), nullable = False, default = 'Anonymous')
    category = db.Column(db.String(50), nullable = False)
    date_created = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)

    def __repr__(self):
        return 'News item ' + str(self.id)

class Users(db.Model):
    userid = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), nullable = False)
    email = db.Column(db.String(100), nullable = False)
    password = db.Column(db.String(50), nullable = False)

    def __repr__(self):
        return 'User ' + str(self.userid)

class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

class AddNews(Form):
    title = StringField('Title', [validators.Length(min=10) ])
    author = StringField('Author', [validators.Length(min=4)])
    category = SelectField('Category', choices = [('General','General'),('Life Style','Life Style'),('Sports','Sports'),('Travel','Travel')])
    content = TextAreaField('Content', [validators.length(min=10)])


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

DummyNews = [
    {
        'head': 'This is headline1',
        'content': 'This is the content',
        'author': 'Raihan',
        'category': 'General'
    },
    {
        'head': 'This is headline2',
        'content': 'This is the content',
        'author': 'Raihan',
        'category': 'General'
    },
    {
        'head': 'This is headline3',
        'content': 'This is the content',
        'author': 'Raihan',
        'category': 'General'
    }
]

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/news')
def news():
    items = NewsPost.query.all()
    return render_template('news.html', News = items)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST'and form.validate():
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))
        new = Users(username =username, email = email, password = password)
        db.session.add(new)
        db.session.commit()

        flash('You are now registered and can login','success')

        return redirect('/login')
    else:
        return render_template('register.html', form = form)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user_pass = request.form['password']

        if len(Users.query.filter_by(username=username).all()) !=0:
            password = Users.query.filter_by(username = username).all()[0].password

            if sha256_crypt.verify(user_pass, password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('news'))
            else:
                error = 'Wrong password'
                return render_template('login.html', error = error)
        else:
            error = 'Invalid username'
            return render_template('login.html', error = error)

    return render_template('login.html')

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/addnews', methods = ['GET', 'POST'])
@is_logged_in
def addnews():
    form = AddNews(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        author = form.author.data
        category = form.category.data
        content = form.content.data

        post = NewsPost(title = title, author= author, category = category, content = content)
        db.session.add(post)
        db.session.commit()

        flash('Your article has been added','success')
        return redirect(url_for('news'))
    else:
        return render_template('addnews.html', form = form)


@app.route('/edit/<int:id>', methods = ['GET', 'POST'])
@is_logged_in
def edit(id):
    if session['username'] == 'Raihan':
        edit_post = NewsPost.query.get(id)

        form = AddNews(request.form)
        form.title.data = edit_post.title
        form.author.data = edit_post.author
        form.category.data = edit_post.category
        form.content.data = edit_post.content
        if request.method == 'POST' and form.validate():
            edit_post.title = request.form['title']
            edit_post.author = request.form['author']
            edit_post.category = request.form['category']
            edit_post.content = request.form['content']

            db.session.commit()

            flash('The Edited News Article Has Been Updated','success')
            return redirect(url_for('news'))

        return render_template('edit.html',form = form)

    else:
        flash('Only Admin Is Authorized To Edit','danger')
        return redirect('/news')

@app.route('/delete/<int:id>')
@is_logged_in
def delete(id):
    if session['username'] == 'Raihan':
        post = NewsPost.query.get(id)
        db.session.delete(post)
        db.session.commit()
        
        flash('Article Deleted Successfully','success')

        return redirect(url_for('news'))
    else:
        flash('Only Admin is authorized to delete','danger')
        return redirect(url_for('news'))

@app.route('/single/<int:id>')
def single(id):
    post = NewsPost.query.get(id)
    return render_template('single.html', post = post)

@app.route('/filter/<string:cat>')
def filter(cat):
    posts = NewsPost.query.filter_by(category = cat).all()
    return render_template('news.html', News = posts)

if __name__=='__main__':
    app.secret_key = 'secret'
    app.run(debug=True)