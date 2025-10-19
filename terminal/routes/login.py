from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from database import get_db_connection
from functools import wraps

def configure_login_routes(app):

    @app.route('/index')
    def index():
        return render_template('index.html')

    @app.route('/')
    def init():
        return render_template('index.html')

