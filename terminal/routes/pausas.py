import os
from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from database import get_db_connection
from datetime import datetime, time

def configure_pausas_activas_routes(app):
    
    # Configuración para subida de imágenes
    UPLOAD_FOLDER = 'static/uploads/pausas'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB máximo

    # Crear directorio si no existe
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route('/pausas_activas')
    def pausas_activas_index():
        """Muestra el listado de pausas activas programadas"""
        try:
            conn = get_db_connection()
            
            # Obtener pausas con información de usuario
            pausas = conn.execute('''
                SELECT pa.id, pa.mensaje, pa.imagen, pa.hora_pausa, pa.dias_semana, pa.activa,
                       strftime('%H:%M', pa.hora_pausa) as hora_formateada,
                       u.nombre as usuario_nombre
                FROM pausas_activas pa
                JOIN usuarios u ON pa.id_usuario = u.id
                ORDER BY pa.hora_pausa
            ''').fetchall()
            
            conn.close()
            
            return render_template('pausas_activas/index.html', pausas=pausas)
            
        except Exception as e:
            app.logger.error(f"Error al listar pausas activas: {str(e)}")
            flash('Error al cargar las pausas activas', 'error')
            return redirect(url_for('index'))

    @app.route('/pausas_activas/add', methods=['GET', 'POST'])
    def pausas_activas_add():
        """Agrega una nueva pausa activa programada"""
        conn = get_db_connection()
        
        try:
            if request.method == 'POST':
                mensaje = request.form.get('mensaje', '').strip()
                hora_pausa = request.form.get('hora_pausa')
                dias_semana = ','.join(request.form.getlist('dias_semana'))  # Obtener días seleccionados
                id_usuario = request.form.get('id_usuario')
                imagen = None

                # Procesar archivo de imagen
                if 'imagen' in request.files:
                    file = request.files['imagen']
                    if file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        imagen = filename

                if not mensaje or not hora_pausa or not id_usuario:
                    flash('Mensaje, hora y usuario son obligatorios', 'error')
                elif not dias_semana:
                    flash('Debe seleccionar al menos un día de la semana', 'error')
                else:
                    # Validar formato de hora
                    try:
                        datetime.strptime(hora_pausa, '%H:%M')
                    except ValueError:
                        flash('Formato de hora inválido. Use HH:MM', 'error')
                        return redirect(url_for('pausas_activas_add'))

                    conn.execute('''
                        INSERT INTO pausas_activas 
                        (mensaje, imagen, hora_pausa, dias_semana, id_usuario) 
                        VALUES (?, ?, ?, ?, ?)
                    ''', (mensaje, imagen, hora_pausa, dias_semana, id_usuario))
                    
                    conn.commit()
                    flash('Pausa activa programada correctamente', 'success')
                    return redirect(url_for('pausas_activas_index'))

            # Obtener lista de usuarios
            usuarios = conn.execute('SELECT id, nombre FROM usuarios').fetchall()
            
            return render_template('pausas_activas/add.html', usuarios=usuarios)
                                
        except Exception as e:
            app.logger.error(f"Error al agregar pausa activa: {str(e)}")
            flash('Error al programar la pausa activa', 'error')
            return render_template('pausas_activas/add.html', usuarios=usuarios)
        finally:
            conn.close()

    @app.route('/pausas_activas/edit/<int:id>', methods=['GET', 'POST'])
    def pausas_activas_edit(id):
        """Edita una pausa activa existente"""
        conn = get_db_connection()
        
        try:
            pausa = conn.execute('''
                SELECT pa.*, u.nombre as usuario_nombre
                FROM pausas_activas pa
                JOIN usuarios u ON pa.id_usuario = u.id
                WHERE pa.id = ?
            ''', (id,)).fetchone()

            if pausa is None:
                print(404)

            if request.method == 'POST':
                mensaje = request.form.get('mensaje', '').strip()
                hora_pausa = request.form.get('hora_pausa')
                dias_semana = ','.join(request.form.getlist('dias_semana'))  # Obtener días seleccionados
                id_usuario = request.form.get('id_usuario')
                activa = 1 if request.form.get('activa') else 0
                eliminar_imagen = request.form.get('eliminar_imagen')
                imagen = pausa['imagen']

                # Procesar archivo de imagen
                if 'imagen' in request.files:
                    file = request.files['imagen']
                    if file.filename != '' and allowed_file(file.filename):
                        # Eliminar imagen anterior si existe
                        if imagen and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], imagen)):
                            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], imagen))
                        
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        imagen = filename
                    elif eliminar_imagen:
                        # Eliminar imagen si se marcó la opción
                        if imagen and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], imagen)):
                            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], imagen))
                        imagen = None

                if not mensaje or not hora_pausa or not id_usuario:
                    flash('Mensaje, hora y usuario son obligatorios', 'error')
                elif not dias_semana:
                    flash('Debe seleccionar al menos un día de la semana', 'error')
                else:
                    try:
                        datetime.strptime(hora_pausa, '%H:%M')
                    except ValueError:
                        flash('Formato de hora inválido. Use HH:MM', 'error')
                        return redirect(url_for('pausas_activas_edit', id=id))

                    conn.execute('''
                        UPDATE pausas_activas SET
                            mensaje = ?, imagen = ?, hora_pausa = ?, 
                            dias_semana = ?, id_usuario = ?, activa = ?
                        WHERE id = ?
                    ''', (mensaje, imagen, hora_pausa, dias_semana, id_usuario, activa, id))
                    
                    conn.commit()
                    flash('Pausa activa actualizada correctamente', 'success')
                    return redirect(url_for('pausas_activas_index'))

            usuarios = conn.execute('SELECT id, nombre FROM usuarios').fetchall()
            
            # Convertir días seleccionados a lista para los checkboxes
            dias_seleccionados = pausa['dias_semana'].split(',') if pausa['dias_semana'] else []
            
            return render_template('pausas_activas/edit.html',
                                pausa=pausa,
                                usuarios=usuarios,
                                dias_seleccionados=dias_seleccionados)
                                
        except Exception as e:
            app.logger.error(f"Error al editar pausa activa {id}: {str(e)}")
            flash('Error al actualizar la pausa activa', 'error')
            return redirect(url_for('pausas_activas_index'))
        finally:
            conn.close()

    @app.route('/pausas_activas/delete/<int:id>', methods=['POST'])
    def pausas_activas_delete(id):
        """Elimina una pausa activa programada"""
        if request.method != 'POST':
            print(405)
            
        try:
            conn = get_db_connection()
            
            # Obtener imagen asociada para eliminarla
            pausa = conn.execute('SELECT imagen FROM pausas_activas WHERE id = ?', (id,)).fetchone()
            
            if pausa and pausa['imagen'] and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], pausa['imagen'])):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], pausa['imagen']))
            
            conn.execute('DELETE FROM pausas_activas WHERE id = ?', (id,))
            conn.commit()
            flash('Pausa activa eliminada correctamente', 'success')
        except Exception as e:
            app.logger.error(f"Error al eliminar pausa activa {id}: {str(e)}")
            flash('Error al eliminar la pausa activa', 'error')
        finally:
            conn.close()
            
        return redirect(url_for('pausas_activas_index'))