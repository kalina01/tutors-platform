from pathlib import Path
from flask import session, abort, redirect, request
from werkzeug.exceptions import HTTPException
from app import app


DB_PATH = Path.cwd() / 'db.sqlite3'


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@app.errorhandler(HTTPException)
def error_handler(error):
    code = error.code

    if code == 401:
        return redirect(f'/login?next={error.description["next"]}')

    return error


def login_required(func):
    def wrapper(*args, **kwargs):
        user = session.get('user')
        if user is None:
            abort(401, {'msg': 'Login is required.', 'next': request.path})
        return func(*args, user=user, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


def admin_only(func):
    def wrapper(*args, **kwargs):
        user = session.get('user')
        if user is None:
            abort(401, {'msg': 'Login is required.', 'next': request.path})
        if not user['is_admin']:
            abort(403, {'msg': 'You are not have enough permissions.'})
        return func(*args, user=user, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper
