
import psycopg2 as pg
from flask import g
from math import ceil

DB_NAME = 'DBS2017_new'
PAGE_SIZE = 20


def get_purchases(user, page):
    cur = get_cur()
    cur.execute(
        'select tea.id, tea.name, count(purchase.*) as purchases from tea '
        'join purchase on tea.id = purchase.tea_id '
        'join account on purchase.account_id = account.id '
        'where username = %s group by tea.id '
        'order by purchases desc, tea.id',
        (user,)
    )
    cur.scroll(page * PAGE_SIZE)
    rows = cur.fetchmany(PAGE_SIZE)
    return rows


def get_purchases_pages(user):
    cur = get_cur()
    cur.execute(
        'select count(*) from tea '
        'join purchase on tea.id = purchase.tea_id '
        'join account on purchase.account_id = account.id '
        'where username = %s',
        (user,)
    )
    row = cur.fetchone()
    return ceil(row[0] / PAGE_SIZE)


def get_teas(page, category):
    cur = get_cur()
    cur.execute(
        'select tea.id, tea.name, count(purchase.*) as count from tea '
        'left join purchase on tea.id = purchase.tea_id '
        'left join account on purchase.account_id = account.id '
        'left join variety on tea.variety_id = variety.id '
        'left join category on variety.category_id = category.id '
        'where lower(category.name) = lower(%s) '
        'group by tea.id order by count desc, tea.id',
        (category,)
    )
    cur.scroll(page * PAGE_SIZE)
    rows = cur.fetchmany(PAGE_SIZE)
    return rows


def search_teas(page, query):
    cur = get_cur()
    cur.execute(
        'select tea.id, tea.name, count(purchase.*) as count from tea '
        'left join purchase on tea.id = purchase.tea_id '
        'left join account on purchase.account_id = account.id '
        'left join variety on tea.variety_id = variety.id '
        'left join category on variety.category_id = category.id '
        'where tea.name ilike %s '
        'group by tea.id order by count desc, tea.id',
        ('%{}%'.format(query),)
    )
    cur.scroll(page * PAGE_SIZE)
    rows = cur.fetchmany(PAGE_SIZE)
    return rows


def get_all_teas(page):
    cur = get_cur()
    cur.execute(
        'select tea.id, tea.name, count(purchase.*) as count from tea '
        'left join purchase on tea.id = purchase.tea_id '
        'left join account on purchase.account_id = account.id '
        'left join variety on tea.variety_id = variety.id '
        'left join category on variety.category_id = category.id '
        'group by tea.id order by count desc, tea.id'
    )
    cur.scroll(page * PAGE_SIZE)
    rows = cur.fetchmany(PAGE_SIZE)
    return rows


def get_teas_pages(category):
    cur = get_cur()
    cur.execute(
        'select count(*) from tea '
        'join variety on tea.variety_id = variety.id '
        'join category on variety.category_id = category.id '
        'where category.name ilike %s ',
        (category if category else '%',)
    )
    row = cur.fetchone()
    return ceil(row[0] / PAGE_SIZE)


def get_categories():
    cur = get_cur()
    cur.execute(
        'select id, name from category'
    )
    rows = cur.fetchall()
    return rows


def get_tea(tea_id):
    cur = get_cur()
    cur.execute(
        'select tea.name, category.name, variety.name, '
        'origin.name, origin_country.name, '
        'vendor.name, vendor_country.name from tea '
        'join variety on tea.variety_id = variety.id '
        'join category on variety.category_id = category.id '
        'join origin on tea.origin_id = origin.id '
        'join country as origin_country '
        'on origin.country_id = origin_country.id '
        'join vendor on tea.vendor_id = vendor.id '
        'join country as vendor_country '
        'on vendor.country_id = vendor_country.id '
        'where tea.id = %s',
        (tea_id,)
    )
    row = cur.fetchone()
    return row


def get_tastings(user, tea_id):
    cur = get_cur()
    cur.execute(
        'select tasting.id, happened, notes, '
        'array_agg(flavor.name) from tasting '
        'join account on tasting.account_id = account.id '
        'left join tasting_flavor on tasting.id = tasting_flavor.tasting_id '
        'left join flavor on tasting_flavor.flavor_id = flavor.id '
        'where tea_id = %s and username = %s '
        'group by tasting.id order by happened',
        (tea_id, user)
    )
    rows = cur.fetchall()
    return rows


def create_tasting(user, tea_id, date, notes, flavors):
    cur = get_cur()
    db = get_db()
    cur.execute(
        'insert into tasting (account_id, tea_id, happened, notes) '
        'values ((select id from account where username = %s), %s, %s, %s)'
        'returning tasting.id',
        (user, tea_id, date, notes)
    )
    tasting = cur.fetchone()[0]
    for flavor in flavors:
        cur.execute(
            'insert into tasting_flavor (tasting_id, flavor_id) '
            'values (%s, (select id from flavor where lower(%s) = lower(name) limit 1))',
            (tasting, flavor)
        )
    db.commit()


def update_tasting(tasting, date, notes):
    cur = get_cur()
    db = get_db()
    cur.execute(
        'update tasting set happened = %s, notes = %s '
        'where id = %s',
        (date, notes, tasting)
    )
    db.commit()


def delete_tasting(tasting):
    cur = get_cur()
    db = get_db()
    cur.execute(
        'delete from tasting where id = %s',
        (tasting,)
    )
    db.commit()


def connect_db():
    return pg.connect(dbname=DB_NAME, user='flask', password='flask')


def get_db():
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db


def get_cur():
    if not hasattr(g, 'cur'):
        g.cur = get_db().cursor()
    return g.cur


def close_db():
    if hasattr(g, 'db'):
        g.db.close()


def check_user(username):
    cur = get_cur()
    cur.execute(
        'select username from account where username = %s',
        (username,)
    )
    row = cur.fetchone()
    return row
