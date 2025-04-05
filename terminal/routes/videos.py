from flask import render_template, request, redirect, url_for, flash, abort
from database import get_db_connection

def configure_videos_valida_routes(app):
    @app.route('/videos')
    def videos_index():
        conn = get_db_connection()
        videos = conn.execute('SELECT * FROM camaras').fetchall()
        conn.close()
        return render_template('videos/index.html', videos=videos)


