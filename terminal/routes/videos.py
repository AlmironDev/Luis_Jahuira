from flask import render_template, request, redirect, url_for, flash, abort, jsonify, Response
import numpy as np
from database import get_db_connection
from services.video_streamer import VideoStreamer
import time
from datetime import datetime

from services.camera_manager import camera_manager
video_streamer = VideoStreamer()
import cv2
def configure_videos_routes(app):
    @app.route('/video')
    def video_index():
        """Muestra todas las cámaras en modo visualización"""
        try:
            conn = get_db_connection()
            camaras = conn.execute('''
                SELECT id, nombre, url 
                FROM camaras
                ORDER BY nombre
            ''').fetchall()
            conn.close()
            
            return render_template('video/index.html', camaras=camaras)
            
        except Exception as e:
            app.logger.error(f"Error al cargar vista de video: {str(e)}")
            flash('Error al cargar las cámaras en modo video', 'error')
            return redirect(url_for('index'))


    @app.route('/video/config/<int:camera_id>')
    def video_config(camera_id):
        """Muestra la configuración de una cámara específica."""
        try:
            conn = get_db_connection()
            camara = conn.execute('''
                SELECT id, nombre, url,
                       muslo_rodilla_pie, espalda_cadera_muslo,
                       hombros_brazos, espalda_cuello_cabeza,
                       manos_muneca
                FROM camaras
                WHERE id = ?
            ''', (camera_id,)).fetchone()
            conn.close()

            if not camara:
                abort(404)

            camara_dict = dict(camara)
            camara_dict.setdefault('activa', True)
            camara_dict.setdefault('max_neck_angle', 45)
            camara_dict.setdefault('min_leg_angle', 160)

            return render_template('video/config.html', camara=camara_dict)
        except Exception as e:
            app.logger.error(f"Error al cargar configuración de cámara {camera_id}: {str(e)}")
            flash('Error al cargar la configuración de la cámara', 'error')
            return redirect(url_for('video_index'))

    @app.route('/video_feed/<int:camera_id>')
    def video_feed(camera_id):
        def generate():
            while True:
                frame = camera_manager.get_frame(camera_id)  # ← Ahora devuelve frame CON MediaPipe
                if frame is None:
                    # Frame de espera
                    wait_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(wait_frame, "Cargando camara...", (50, 240), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    _, buffer = cv2.imencode('.jpg', wait_frame)
                else:
                    # Frame procesado con MediaPipe
                    _, buffer = cv2.imencode('.jpg', frame)
                
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n'
                )
                time.sleep(0.03)  # Control de FPS

        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
        
    @app.route('/api/update_angles/<int:camera_id>', methods=['POST'])
    def update_camera_angles(camera_id):
        """Actualiza los parámetros de configuración"""
        try:
            data = request.get_json()
            
            # Validar datos recibidos
            required_fields = [
                'muslo_rodilla_pie', 'espalda_cadera_muslo',
                'hombros_brazos', 'espalda_cuello_cabeza',
                'manos_muneca'
            ]
            
            if not all(field in data for field in required_fields):
                return jsonify({'success': False, 'error': 'Datos incompletos'}), 400
            
            # Actualizar la configuración en el video streamer
            video_streamer.update_posture_config({
                'muslo_rodilla_pie': int(data['muslo_rodilla_pie']),
                'espalda_cadera_muslo': int(data['espalda_cadera_muslo']),
                'hombros_brazos': float(data['hombros_brazos']),
                'espalda_cuello_cabeza': float(data['espalda_cuello_cabeza']),
                'manos_muneca': int(data['manos_muneca']),
            })
            
            # Actualizar la base de datos
            conn = get_db_connection()
            conn.execute('''
                UPDATE camaras SET
                    muslo_rodilla_pie = ?,
                    espalda_cadera_muslo = ?,
                    hombros_brazos = ?,
                    espalda_cuello_cabeza = ?,
                    manos_muneca = ?
                WHERE id = ?
            ''', (
                data['muslo_rodilla_pie'],
                data['espalda_cadera_muslo'],
                data['hombros_brazos'],
                data['espalda_cuello_cabeza'],
                data['manos_muneca'],
                camera_id
            ))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True})
            
        except Exception as e:
            app.logger.error(f"Error al actualizar ángulos: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
