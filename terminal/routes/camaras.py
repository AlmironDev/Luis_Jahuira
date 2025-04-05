from flask import render_template, request, redirect, url_for, flash, abort
from database import get_db_connection
import validators  # You'll need to install python-validators package
from werkzeug.security import generate_password_hash

def configure_camaras_routes(app):
    @app.route('/camaras')
    def camaras_index():
        """Muestra la lista de todas las cámaras registradas con paginación"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 10
            
            conn = get_db_connection()
            
            # Get total count for pagination
            total = conn.execute('SELECT COUNT(*) FROM camaras').fetchone()[0]
            
            # Get paginated results
            camaras = conn.execute('''
                SELECT id, nombre, url, ubicacion, 
                       strftime('%d/%m/%Y %H:%M', fecha_instalacion) as fecha_instalacion,
                       activa, descripcion
                FROM camaras
                ORDER BY fecha_instalacion DESC
                LIMIT ? OFFSET ?
            ''', (per_page, (page - 1) * per_page)).fetchall()
            
            conn.close()
            
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
        """Agrega una nueva cámara al sistema con validación mejorada"""
        if request.method == 'POST':
            try:
                # Get and validate form data
                nombre = request.form.get('nombre', '').strip()
                url = request.form.get('url', '').strip()
                ubicacion = request.form.get('ubicacion', '').strip()
                descripcion = request.form.get('descripcion', '').strip()
                
                # Validate required fields
                if not nombre or not url:
                    flash('Nombre y URL son campos obligatorios', 'error')
                    return render_template('camaras/add.html', 
                                          form_data=request.form)
                
                # Validate URL format
                if not validators.url(url):
                    flash('La URL proporcionada no es válida', 'error')
                    return render_template('camaras/add.html', 
                                          form_data=request.form)
                
                # Parse numeric parameters with defaults
                try:
                    angulo_min = int(request.form.get('angulo_min', 45))
                    angulo_max = int(request.form.get('angulo_max', 135))
                    hombros_min = float(request.form.get('hombros_min', 0.5))
                    hombros_max = float(request.form.get('hombros_max', 1.5))
                    manos_min = int(request.form.get('manos_min', 30))
                    manos_max = int(request.form.get('manos_max', 150))
                except ValueError:
                    flash('Los valores numéricos no son válidos', 'error')
                    return render_template('camaras/add.html', 
                                          form_data=request.form)
                
                activa = 1 if request.form.get('activa') else 0

                conn = get_db_connection()
                
                # Check for duplicate URL
                existing = conn.execute(
                    'SELECT 1 FROM camaras WHERE url = ?', 
                    (url,)
                ).fetchone()
                
                if existing:
                    flash('Ya existe una cámara con esta URL', 'error')
                    conn.close()
                    return render_template('camaras/add.html', 
                                        form_data=request.form)
                
                # Insert new camera
                conn.execute('''
                    INSERT INTO camaras (
                        nombre, url, ubicacion, descripcion,
                        angulo_min, angulo_max,
                        hombros_min, hombros_max, 
                        manos_min, manos_max, 
                        activa
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    nombre, url, ubicacion, descripcion,
                    angulo_min, angulo_max,
                    hombros_min, hombros_max,
                    manos_min, manos_max,
                    activa
                ))
                
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
                return render_template('camaras/add.html', 
                                      form_data=request.form)

        return render_template('camaras/add.html')

    @app.route('/camaras/edit/<int:id>', methods=['GET', 'POST'])
    def camaras_edit(id):
        """Edita los datos de una cámara existente con validación mejorada"""
        try:
            conn = get_db_connection()
            camara = conn.execute('SELECT * FROM camaras WHERE id = ?', (id,)).fetchone()
            
            if camara is None:
                conn.close()
                abort(404)

            if request.method == 'POST':
                # Get and validate form data
                nombre = request.form.get('nombre', '').strip()
                url = request.form.get('url', '').strip()
                ubicacion = request.form.get('ubicacion', '').strip()
                descripcion = request.form.get('descripcion', '').strip()
                
                # Validate required fields
                if not nombre or not url:
                    flash('Nombre y URL son campos obligatorios', 'error')
                    return render_template('camaras/edit.html', 
                                         camara=camara)
                
                # Validate URL format
                if not validators.url(url):
                    flash('La URL proporcionada no es válida', 'error')
                    return render_template('camaras/edit.html', 
                                         camara=camara)
                
                # Parse numeric parameters with defaults
                try:
                    angulo_min = int(request.form.get('angulo_min', 45))
                    angulo_max = int(request.form.get('angulo_max', 135))
                    hombros_min = float(request.form.get('hombros_min', 0.5))
                    hombros_max = float(request.form.get('hombros_max', 1.5))
                    manos_min = int(request.form.get('manos_min', 30))
                    manos_max = int(request.form.get('manos_max', 150))
                except ValueError:
                    flash('Los valores numéricos no son válidos', 'error')
                    return render_template('camaras/edit.html', 
                                         camara=camara)
                
                activa = 1 if request.form.get('activa') else 0

                # Check for duplicate URL (excluding current camera)
                existing = conn.execute(
                    'SELECT 1 FROM camaras WHERE url = ? AND id != ?', 
                    (url, id)
                ).fetchone()
                
                if existing:
                    flash('Ya existe otra cámara con esta URL', 'error')
                    return render_template('camaras/edit.html', 
                                        camara=camara)
                
                # Update camera
                conn.execute('''
                    UPDATE camaras SET
                        nombre = ?, url = ?, ubicacion = ?, descripcion = ?,
                        angulo_min = ?, angulo_max = ?,
                        hombros_min = ?, hombros_max = ?,
                        manos_min = ?, manos_max = ?,
                        activa = ?
                    WHERE id = ?
                ''', (
                    nombre, url, ubicacion, descripcion,
                    angulo_min, angulo_max,
                    hombros_min, hombros_max,
                    manos_min, manos_max,
                    activa, id
                ))
                
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

    @app.route('/camaras/toggle/<int:id>', methods=['POST'])
    def camaras_toggle(id):
        """Activa/desactiva una cámara con confirmación"""
        if request.method != 'POST':
            abort(405)  # Method Not Allowed
            
        try:
            conn = get_db_connection()
            camara = conn.execute(
                'SELECT id, activa, nombre FROM camaras WHERE id = ?', 
                (id,)
            ).fetchone()
            
            if not camara:
                conn.close()
                flash('La cámara no existe', 'error')
                return redirect(url_for('camaras_index'))
            
            new_status = 0 if camara['activa'] else 1
            conn.execute(
                'UPDATE camaras SET activa = ? WHERE id = ?', 
                (new_status, id)
            )
            conn.commit()
            conn.close()
            
            estado = "activada" if new_status else "desactivada"
            flash(f'Cámara "{camara["nombre"]}" {estado} correctamente', 'success')
            return redirect(url_for('camaras_index'))
            
        except Exception as e:
            app.logger.error(f"Error al cambiar estado de cámara {id}: {str(e)}")
            flash('Error al cambiar el estado de la cámara', 'error')
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return redirect(url_for('camaras_index'))