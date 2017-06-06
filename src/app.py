from _testbuffer import staticarray
from functools import wraps

import datetime
from flask import Flask, session, request
from flask import redirect, url_for, abort
from flask import render_template, send_from_directory

from db import get_purchases, get_cur, check_user, close_db, get_tea, get_teas, \
    get_categories, get_teas_pages, get_purchases_pages, get_tastings, \
    create_tasting, update_tasting, delete_tasting, get_all_teas, search_teas

app = Flask(__name__)

app.secret_key = (
    b't$\xcd\xc0]f\xc9\xa4vN\xafa\xc1\xcf\x82\xe4/\x8c\xcff\xd4\xee\xf1*'
)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.jinja_env.keep_trailing_newline = True


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
        return home()
    else:
        return redirect(url_for('login'))


@app.route('/home')
@require_auth
def home():
    return render_template(
        'home.html', user=session.get('user')
    )


@app.route('/purchases')
@app.route('/purchase/page/<int(min=1):page>')
@require_auth
def purchases(page=1):
    rows = get_purchases(session.get('user'), page - 1)
    pages = get_purchases_pages(session.get('user'))
    return render_template(
        'purchases.html', user=session.get('user'), rows=rows,
        active_page=page, pages=pages
    )


@app.route('/tea/')
@app.route('/tea/page/<int(min=1):page>')
@app.route('/tea/category/<category>')
@app.route('/tea/category/<category>/page/<int(min=1):page>')
@require_auth
def teas(page=1, category=None):
    query = request.args.get('search')
    print(query)
    if isinstance(category, str) and str.lower(category) == 'all':
        category = None
    if query:
        rows = search_teas(page - 1, query)
    elif category:
        rows = get_teas(page - 1, category)
    else:
        rows = get_all_teas(page - 1)
    pages = get_teas_pages(category)
    if not rows:
        abort(404)
    categories = get_categories()
    return render_template(
        'teas.html', user=session.get('user'), rows=rows,
        active_category=category, categories=categories,
        active_page=page, pages=pages
    )


@app.route('/tea/<tea_id>')
@require_auth
def tea(tea_id):
    row = get_tea(tea_id)
    if not row:
        abort(404)
    (
        name, category, variety,
        origin, origin_country,
        vendor, vendor_country
    ) = row
    notes = get_tastings(session.get('user'), tea_id)
    return render_template(
        'tea.html', user=session.get('user'),
        today=datetime.date.today(),
        name=name, tea_id=tea_id, notes=notes,
        category=category, variety=variety,
        origin='{}, {}'.format(origin, origin_country),
        vendor='{} ({})'.format(vendor, vendor_country)
    )


@app.route('/note/<int:note_id>', methods=['POST'])
@require_auth
def update_note(note_id):
    if request.form.get('action') == 'update':
        update_tasting(
            note_id,
            request.form.get('date'),
            request.form.get('notes')
        )
    if request.form.get('action') == 'remove':
        delete_tasting(note_id)
    return redirect(url_for('tea', tea_id=request.args.get('tea_id')))


@app.route('/note/', methods=['POST'])
@require_auth
def create_note():
    if request.form.get('action') == 'create':
        create_tasting(
            session.get('user'),
            request.args.get('tea_id'),
            request.form.get('date'),
            request.form.get('notes'),
            [
                flavor.strip() for flavor
                in request.form.get('flavors').split('\n')
            ]
        )
    return redirect(url_for('tea', tea_id=request.args.get('tea_id')))


@app.route('/flavors')
@require_auth
def flavors():
    cur = get_cur()
    cur.execute(
        'select distinct name from flavor order by name'
    )
    return render_template(
        'flavors.html', user=session.get('user'), rows=cur.fetchall()
    )


@app.route('/test')
@app.route('/test/page/<int(min=1):page>')
def test(page=1):
    return render_template('test.html', page=page)


def auth(username):
    row = check_user(username)
    return row[0] if row else None


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = request.form['username']
        if auth(user):
            session['user'] = user
            return redirect(url_for('root'))
        else:
            error = 'User "{}" does not exist'.format(user)
    return render_template(
        'login.html', user=session.get('user'), error=error
    )


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', error=error), 404


@app.teardown_appcontext
def teardown(error):
    close_db()


if __name__ == "__main__":
    app.run()
