from flask import render_template, request, redirect, url_for, flash, abort, jsonify, Response
from database import get_db_connection
from services.video_streamer import VideoStreamer
import time
from datetime import datetime
video_streamer = VideoStreamer()

def configure_videos_routes(app):
    @app.route('/video')
    def video_index():
        """Muestra todas las cámaras en modo visualización"""
        try:
            conn = get_db_connection()
            camaras = conn.execute('''
                SELECT id, nombre, url, activa 
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
        """Muestra la configuración para una cámara específica"""
        try:
            conn = get_db_connection()
            camara = conn.execute('''
                SELECT id, nombre, url, activa, 
                       angulo_min, angulo_max, 
                       hombros_min, hombros_max, 
                       manos_min, manos_max
                FROM camaras
                WHERE id = ?
            ''', (camera_id,)).fetchone()
            conn.close()
            
            if not camara:
                abort(404)
                
            # Convertir a dict y agregar valores por defecto para compatibilidad
            camara_dict = dict(camara)
            camara_dict['max_neck_angle'] = 45  # Valor fijo para el frontend
            camara_dict['min_leg_angle'] = 160  # Valor fijo para el frontend
            
            # Iniciar el stream si está activa
            if camara_dict['activa']:
                video_streamer.start_stream(camera_id, camara_dict['url'])
                
                
            return render_template('video/config.html', camara=camara_dict)
            
        except Exception as e:
            app.logger.error(f"Error al cargar configuración de cámara {camera_id}: {str(e)}")
            flash('Error al cargar la configuración de la cámara', 'error')
            return redirect(url_for('video_index'))

    @app.route('/video_feed/<int:camera_id>')
    def video_feed(camera_id):
        """Genera el feed de video para la cámara especificada"""
        def generate():
            while True:
                frame = video_streamer.get_frame(camera_id)
                if frame:
                    yield (b'--frame\r\n'
                          b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                else:
                    time.sleep(0.1)
                alertas = video_streamer.get_recent_alerts(camera_id)
                if alertas:
                    print("alertas",alertas)
                    conn = get_db_connection()
                    try:
                        for alerta in alertas:
                            fecha_formatted = datetime.strptime(alerta['timestamp_iso'], '%Y-%m-%dT%H:%M:%S.%f').strftime("'%Y-%m-%d %H:%M:%S.%f'")
                            query = f'''
                                INSERT INTO alertas (
                                    id_camara, 
                                    mensaje, 
                                    tipo, 
                                    severidad, 
                                    fecha
                                ) VALUES ({alerta['camera_id']},'{alerta['message']}', '{alerta['type_name']}', '{alerta['severity_name']}', {fecha_formatted})
                            '''
                            print("query",query)
                            conn.execute(query)
                        conn.commit()
                        print('Alertas registradas correctamente!', 'success')
                    except Exception as e:
                        print(f"Error al insertar alertas: {str(e)}")
                    finally:
                        conn.close()

        return Response(generate(),
                      mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/api/update_angles/<int:camera_id>', methods=['POST'])
    def update_camera_angles(camera_id):
        """Actualiza los parámetros de configuración"""
        try:
            data = request.get_json()
            
            # Validar datos recibidos
            required_fields = [
                'angulo_min', 'angulo_max',
                'hombros_min', 'hombros_max',
                'manos_min', 'manos_max'
            ]
            
            if not all(field in data for field in required_fields):
                return jsonify({'success': False, 'error': 'Datos incompletos'}), 400
            
            # Actualizar la configuración en el video streamer
            video_streamer.update_posture_config({
                'angulo_min': int(data['angulo_min']),
                'angulo_max': int(data['angulo_max']),
                'hombros_min': float(data['hombros_min']),
                'hombros_max': float(data['hombros_max']),
                'manos_min': int(data['manos_min']),
                'manos_max': int(data['manos_max'])
            })
            
            # Actualizar la base de datos
            conn = get_db_connection()
            conn.execute('''
                UPDATE camaras SET
                    angulo_min = ?,
                    angulo_max = ?,
                    hombros_min = ?,
                    hombros_max = ?,
                    manos_min = ?,
                    manos_max = ?
                WHERE id = ?
            ''', (
                data['angulo_min'],
                data['angulo_max'],
                data['hombros_min'],
                data['hombros_max'],
                data['manos_min'],
                data['manos_max'],
                camera_id
            ))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True})
            
        except Exception as e:
            app.logger.error(f"Error al actualizar ángulos: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/toggle_camera/<int:camera_id>', methods=['POST'])
    def toggle_camera(camera_id):
        """Activa/desactiva una cámara"""
        try:
            data = request.get_json()
            active = data.get('active', False)
            
            conn = get_db_connection()
            conn.execute('''
                UPDATE camaras SET activa = ? WHERE id = ?
            ''', (active, camera_id))
            conn.commit()
            
            # Obtener la URL de la cámara
            camara = conn.execute('SELECT url FROM camaras WHERE id = ?', (camera_id,)).fetchone()
            conn.close()
            
            # Manejar el stream según el estado
            if active:
                video_streamer.start_stream(camera_id, camara['url'])
            else:
                video_streamer.stop_stream(camera_id)
            
            return jsonify({'success': True, 'active': active})
            
        except Exception as e:
            app.logger.error(f"Error al cambiar estado de cámara: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500