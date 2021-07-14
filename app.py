from os import name
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from werkzeug import wrappers
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)
app.debug = True

# config MySQL
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = ""
app.config['MYSQL_DB'] = "myflaskapp"
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)

# Index


@app.route('/')
def index():
    return render_template('homepage.html')

# Blog Posts


@app.route('/posts')
def posts():
    # Creating cursor
    cursor = mysql.connection.cursor()

    result = cursor.execute("SELECT * FROM posts")

    posts = cursor.fetchall()

    if result > 0:
        return render_template('posts.html', posts=posts)
    else:
        msg = 'No posts found'
        return render_template('posts.html', msg=msg)
    # Close
    cursor.close()

# Post By Id


@app.route('/post/<string:id>/')
def post(id):
    # Creating cursor
    cursor = mysql.connection.cursor()

    result = cursor.execute("SELECT * FROM posts WHERE id=%s", [id])

    post = cursor.fetchone()

    return render_template('post.html', post=post)


# Regiser Form
class RegisterForm(Form):
    username = StringField('Usernme', [validators.length(min=4, max=40)])
    password = PasswordField('Password', [validators.DataRequired(
    ), validators.EqualTo('confirm', message='Passwords Incorrect')])
    confirm = PasswordField('Confirm Your Password')

# Register


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create curosr
        cur = mysql.connection.cursor()
        # Execute query
        cur.execute("INSERT INTO users(username,password) VALUES(%s, %s)",
                    (username, password))

        # commit to DB
        mysql.connection.commit()

        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        cursor = mysql.connection.cursor()

        # get user by username
        result = cursor.execute(
            "SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cursor.fetchone()
            password = data['password']

            # Compare passwrods
            if sha256_crypt.verify(password_candidate, password):
                # passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are logged in!', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # close connection
            cursor.close()
        else:
            error = 'username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# To check if user logged in


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('No Access, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard


@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get users only articles
    user = session.get("username")
    result = cur.execute(
        "SELECT * FROM posts WHERE author = %s", [user])

    posts = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', posts=posts)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    # close connection
    cur.close()


# Article form class


class PostForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])


# Add Article
@ app.route('/add_post', methods=['GET', 'POST'])
@ is_logged_in
def add_post():
    form = PostForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO posts(title,body,author)VALUES(%s,%s,%s)",
                    (title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        # Close Connection
        cur.close()

        flash('Post Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_post.html', form=form)

# Edit Article


@app.route('/edit_post/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_post(id):
    # Create cursor
    cursor = mysql.connection.cursor()

    # get article by id
    result = cursor.execute("SELECT * FROM posts WHERE id=%s", [id])

    article = cursor.fetchone()

    # get form
    form = PostForm(request.form)

    # populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cursor = mysql.connection.cursor()

        # Execute
        cursor.execute(
            "UPDATE posts SET title = %s, body = %s WHERE id = %s", (title, body, id))

        # Commit to DB
        mysql.connection.commit()

        # Close Connection
        cursor.close()

        flash('Post Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_post.html', form=form)


# Delete article
@app.route('/delete_post/<string:id>', methods=['POST'])
@is_logged_in
def delete_post(id):
    # crete cursor
    cur = mysql.connection.cursor()

    # execute
    cur.execute("DELETE FROM posts WHERE id=%s", [id])

    # Commit to DB
    mysql.connection.commit()

    # Close Connection
    cur.close()

    flash('Post Deleted', 'success')

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.secret_key = '101secret_key'
    app.run()
