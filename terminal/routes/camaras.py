import cv2
import threading
import time
from flask import jsonify, render_template, request, redirect, url_for, flash, abort
from database import get_db_connection
import validators
import re



def configure_camaras_routes(app):
    @app.route('/camaras')
    def camaras_index():
        """Muestra la lista de todas las cámaras registradas con paginación"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 10
            
            conn = get_db_connection()
            
            total = conn.execute('SELECT COUNT(*) FROM camaras').fetchone()[0]
            camaras = conn.execute('''
                SELECT id, nombre, url, ubicacion, activa,
                       strftime('%d/%m/%Y %H:%M', fecha_instalacion) as fecha_instalacion,
                       descripcion
                FROM camaras
                ORDER BY fecha_instalacion DESC
                LIMIT ? OFFSET ?
            ''', (per_page, (page - 1) * per_page)).fetchall()
            
            conn.close()
            
            print("Cámaras cargadas:", camaras)
            
            return render_template('camaras/index.html',
                                   camaras=camaras,
                                   page=page,
                                   per_page=per_page,
                                   total=total)
        except Exception as e:
            app.logger.error(f"Error al listar cámaras: {str(e)}")
            flash('Error al cargar la lista de cámaras', 'error')
            return redirect(url_for('index'))

    @app.route('/camaras/add', methods=['GET', 'POST'])
    def camaras_add():
        """Agrega una nueva cámara"""
        if request.method == 'POST':
            try:
                    
                print("Cámara request.form:", request.form)
                nombre = request.form.get('nombre', '').strip()
                url = request.form.get('url', '').strip()
                ubicacion = request.form.get('ubicacion', '').strip()
                descripcion = request.form.get('descripcion', '').strip()
                activa = int('1' in request.form.getlist('activa'))

                
                if not nombre or not url:
                    flash('Nombre y URL son campos obligatorios', 'error')
                    return render_template('camaras/add.html', form_data=request.form)
                
                if not validators.url(url):
                    flash('La URL proporcionada no es válida', 'error')
                    return render_template('camaras/add.html', form_data=request.form)

                conn = get_db_connection()
                existing = conn.execute('SELECT 1 FROM camaras WHERE url = ?', (url,)).fetchone()
                if existing:
                    flash('Ya existe una cámara con esta URL', 'error')
                    conn.close()
                    return render_template('camaras/add.html', form_data=request.form)
                
                conn.execute('''
                    INSERT INTO camaras (
                        nombre, url, ubicacion, descripcion, activa
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (nombre, url, ubicacion, descripcion, activa))
                
                conn.commit()
                conn.close()
                
                flash('Cámara agregada correctamente', 'success')
                return redirect(url_for('camaras_index'))
            except Exception as e:
                app.logger.error(f"Error al agregar cámara: {str(e)}")
                flash('Error al agregar la cámara', 'error')
                if 'conn' in locals():
                    conn.rollback()
                    conn.close()
                return render_template('camaras/add.html', form_data=request.form)
        return render_template('camaras/add.html')

    @app.route('/camaras/edit/<int:id>', methods=['GET', 'POST'])
    def camaras_edit(id):
        """Edita una cámara existente"""
        try:
            conn = get_db_connection()
            camara = conn.execute('SELECT * FROM camaras WHERE id = ?', (id,)).fetchone()
            if not camara:
                conn.close()
                abort(404)
            print("Cámara a editar:", camara)
            print("Cámara request.form:", request.form)
            
            if request.method == 'POST':
                nombre = request.form.get('nombre', '').strip()
                url = request.form.get('url', '').strip()
                ubicacion = request.form.get('ubicacion', '').strip()
                descripcion = request.form.get('descripcion', '').strip()
                activa = int('1' in request.form.getlist('activa'))


                if not nombre or not url:
                    flash('Nombre y URL son campos obligatorios', 'error')
                    return render_template('camaras/edit.html', camara=camara)
                
                if not validators.url(url):
                    flash('La URL proporcionada no es válida', 'error')
                    return render_template('camaras/edit.html', camara=camara)

                existing = conn.execute('SELECT 1 FROM camaras WHERE url = ? AND id != ?', (url, id)).fetchone()
                if existing:
                    flash('Ya existe otra cámara con esta URL', 'error')
                    return render_template('camaras/edit.html', camara=camara)
                
                conn.execute('''
                    UPDATE camaras
                    SET nombre = ?, url = ?, ubicacion = ?, descripcion = ?, activa = ?
                    WHERE id = ?
                ''', (nombre, url, ubicacion, descripcion, activa, id))
                
                conn.commit()
                conn.close()
                flash('Cámara actualizada correctamente', 'success')
                return redirect(url_for('camaras_index'))

            conn.close()
            return render_template('camaras/edit.html', camara=camara)

        except Exception as e:
            app.logger.error(f"Error al editar cámara {id}: {str(e)}")
            flash('Error al editar la cámara', 'error')
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return redirect(url_for('camaras_index'))
        
    @app.route('/camaras/toggle/<int:id>', methods=['POST'])
    def camaras_toggle(id):
        """Activa o desactiva una cámara"""
        try:
            conn = get_db_connection()
            camara = conn.execute('SELECT activa FROM camaras WHERE id = ?', (id,)).fetchone()
            if not camara:
                conn.close()
                return jsonify({"error": "Cámara no encontrada"}), 404

            activa = int('1' in request.form.getlist('activa'))


            conn.execute('UPDATE camaras SET activa = ? WHERE id = ?', (activa, id))
            conn.commit()
            conn.close()

            estado_texto = "activada" if activa else "desactivada"
            return jsonify({"success": True, "message": f"Cámara {estado_texto}"})
        except Exception as e:
            app.logger.error(f"Error al cambiar estado de cámara {id}: {str(e)}")
            return jsonify({"error": "Error interno"}), 500       
        
        
        
    @app.route('/camaras/delete/<int:id>', methods=['POST'])
    def camaras_delete(id):
        """Elimina una cámara del sistema con confirmación"""
        if request.method != 'POST':
            abort(405)  # Method Not Allowed
            
        try:
            conn = get_db_connection()
            
            # Verify camera exists
            camara = conn.execute(
                'SELECT 1 FROM camaras WHERE id = ?',
                (id,)
            ).fetchone()
            
            if not camara:
                conn.close()
                flash('La cámara no existe', 'error')
                return redirect(url_for('camaras_index'))
            
            # Check for associated notifications
            notificaciones = conn.execute(
                'SELECT COUNT(*) FROM notificaciones WHERE id_camara = ?',
                (id,)
            ).fetchone()[0]
            
            if notificaciones > 0:
                flash(f'No se puede eliminar: existen {notificaciones} notificaciones asociadas', 'error')
            else:
                conn.execute('DELETE FROM camaras WHERE id = ?', (id,))
                conn.commit()
                flash('Cámara eliminada correctamente', 'success')
            
            conn.close()
            return redirect(url_for('camaras_index'))
            
        except Exception as e:
            app.logger.error(f"Error al eliminar cámara {id}: {str(e)}")
            flash('Error al eliminar la cámara', 'error')
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return redirect(url_for('camaras_index'))


    def try_connect(ip, usuario, clave, results):
        url = f"rtsp://{usuario}:{clave}@{ip}:554/cam/realmonitor?channel=1&subtype=0"
        print("Probando conexión a:", url)
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            results.append({"ip": ip, "status": "✅ Conectada", "url": url})
        else:
            results.append({"ip": ip, "status": "❌ No responde", "url": url})
        cap.release()

    @app.route('/camaras/scan/start')
    def camaras_scan_start():
        """Escanea IPs conocidas para detectar cámaras disponibles (streaming)."""
        global scan_stop
        scan_stop = False

        def generate():
            usuario = "admin"
            clave = "admin123"
            ips = [f"192.168.18.{i}" for i in range(30, 40)]

            for ip in ips:
                if scan_stop:
                    yield f"data: {{\"status\": \"⏹ Escaneo detenido\"}}\n\n"
                    break

                url = f"rtsp://{usuario}:{clave}@{ip}:554/cam/realmonitor?channel=1&subtype=0"
                print(f"🔍 Probando conexión a: {url}")

                cap = cv2.VideoCapture(url)
                inicio = time.time()
                conectada = False

                while time.time() - inicio < 4:
                    ret, frame = cap.read()
                    if ret:
                        conectada = True
                        break
                    time.sleep(0.3)
                cap.release()

                if conectada:
                    print(f"✅ Cámara conectada: {ip}")
                    yield f"data: {{\"ip\": \"{ip}\", \"status\": \"✅ Conectada\", \"url\": \"{url}\"}}\n\n"
                else:
                    print(f"❌ No responde: {ip}")
                    yield f"data: {{\"ip\": \"{ip}\", \"status\": \"❌ No responde\", \"url\": \"{url}\"}}\n\n"
                time.sleep(0.2)

            yield f"data: {{\"status\": \"🏁 Escaneo completado\"}}\n\n"

        return app.response_class(generate(), mimetype='text/event-stream')


    @app.route('/camaras/scan/stop', methods=['POST'])
    def camaras_scan_stop():
        """Detiene la búsqueda de cámaras."""
        global scan_stop
        scan_stop = True
        print("🛑 Escaneo detenido manualmente")
        return jsonify({"stopped": True})

    @app.route('/camaras/save', methods=['POST'])
    def camaras_save():
        """Guarda una cámara detectada si no está ya registrada."""
        data = request.get_json()
        nombre = data.get('nombre', '').strip() or f"Camara_{data.get('ip', '')}"
        url = data.get('url', '').strip()
        ubicacion = data.get('ubicacion', '').strip()

        if not url or not data.get('ip'):
            return jsonify({"error": "Faltan datos"}), 400

        # Evita duplicados
        conn = get_db_connection()
        existing = conn.execute('SELECT 1 FROM camaras WHERE url = ?', (url,)).fetchone()
        if existing:
            conn.close()
            return jsonify({"error": "La cámara ya está registrada"}), 409

        conn.execute('''
            INSERT INTO camaras (nombre, url, ubicacion, descripcion)
            VALUES (?, ?, ?, ?)
        ''', (nombre, url, ubicacion, 'Detectada automáticamente'))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Cámara guardada correctamente"})
        