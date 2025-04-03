from flask import render_template, request, redirect, url_for, flash, abort
from database import get_db_connection

def configure_camaras_valida_routes(app):
    @app.route('/camaras')
    def camara_index():
        conn = get_db_connection()
        videos = conn.execute('SELECT * FROM videos').fetchall()
        conn.close()
        return render_template('camaras/index.html', videos=videos)


