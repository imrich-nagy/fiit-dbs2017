
from functools import wraps

import psycopg2 as pg
from flask import Flask, request, redirect, url_for, render_template, session, g


app = Flask(__name__)

app.db_name = 'DBS2017_new'
app.secret_key = (
    b't$\xcd\xc0]f\xc9\xa4vN\xafa\xc1\xcf\x82\xe4/\x8c\xcff\xd4\xee\xf1*'
)


def require_auth(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if 'user' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return decorator


@app.route('/')
def root():
    if 'user' in session:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))


@app.route('/home')
@require_auth
def home():
    return render_template(
        'home.html', user=session.get('user')
    )


@app.route('/purchases')
@require_auth
def purchases():
    cur = get_cur()
    cur.execute(
        'select name, count(purchase.*) from tea '
        'join purchase on tea.id = purchase.tea_id '
        'join account on purchase.account_id = account.id '
        'where username like %s group by tea.id order by count desc',
        (session.get('user'),)
    )
    return render_template(
        'purchases.html', user=session.get('user'), rows=cur.fetchall()
    )


def auth(username):
    cur = get_cur()
    cur.execute(
        'select username from account where username = %s',
        (username,)
    )
    row = cur.fetchone()
    return row[0] if row else None


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = request.form['username']
        if auth(user):
            session['user'] = user
            return redirect(url_for('home'))
        else:
            error = 'Unknown user.'
    return render_template(
        'login.html', user=session.get('user'), error=error
    )


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


def connect_db():
    return pg.connect(dbname=app.db_name, user='postgres')


def get_db():
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db


def get_cur():
    if not hasattr(g, 'cur'):
        g.cur = get_db().cursor()
    return g.cur


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()


if __name__ == "__main__":
    app.run()
