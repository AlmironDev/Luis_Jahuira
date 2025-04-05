from flask import render_template, request, redirect, url_for, flash, abort
from database import get_db_connection
from datetime import datetime

def configure_notificacion_routes(app):
    
    @app.route('/notificaciones')
    def notificacion_index():
        """Muestra el listado de notificaciones con paginación"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 10
            conn = get_db_connection()
            
            # Obtener notificaciones con información de usuario y cámara
            notificaciones = conn.execute('''
                SELECT n.id, n.mensaje, n.tipo, n.leida, 
                       strftime('%d/%m/%Y %H:%M', n.fecha) as fecha_formateada,
                       u.nombre as usuario_nombre,
                       c.nombre as camara_nombre
                FROM notificaciones n
                LEFT JOIN usuarios u ON n.id_usuario = u.id
                LEFT JOIN camaras c ON n.id_camara = c.id
                ORDER BY n.fecha DESC
                LIMIT ? OFFSET ?
            ''', (per_page, (page - 1) * per_page)).fetchall()
            
            total = conn.execute('SELECT COUNT(*) FROM notificaciones').fetchone()[0]
            conn.close()
            
            return render_template('notificacion/index.html', 
                                notificaciones=notificaciones,
                                page=page,
                                per_page=per_page,
                                total=total)
            
        except Exception as e:
            app.logger.error(f"Error al listar notificaciones: {str(e)}")
            flash('Error al cargar las notificaciones', 'error')
            return redirect(url_for('index'))

    @app.route('/notificaciones/marcar_leida/<int:id>', methods=['POST'])
    def notificacion_marcar_leida(id):
        """Marca una notificación como leída"""
        if request.method != 'POST':
            abort(405)
            
        try:
            conn = get_db_connection()
            conn.execute('UPDATE notificaciones SET leida = 1 WHERE id = ?', (id,))
            conn.commit()
            conn.close()
            return '', 204  # Respuesta vacía para AJAX
        except Exception as e:
            app.logger.error(f"Error al marcar notificación {id} como leída: {str(e)}")
            return '', 500

    @app.route('/notificaciones/add', methods=['GET', 'POST'])
    def notificacion_add():
        """Agrega una nueva notificación"""
        conn = get_db_connection()
        
        try:
            if request.method == 'POST':
                mensaje = request.form.get('mensaje', '').strip()
                tipo = request.form.get('tipo', 'info')
                id_usuario = request.form.get('id_usuario')
                id_camara = request.form.get('id_camara')

                if not mensaje:
                    flash('El mensaje es obligatorio', 'error')
                else:
                    conn.execute('''
                        INSERT INTO notificaciones 
                        (mensaje, tipo, id_usuario, id_camara, fecha) 
                        VALUES (?, ?, ?, ?, ?)
                    ''', (mensaje, tipo, id_usuario, id_camara, datetime.now()))
                    
                    conn.commit()
                    flash('Notificación creada correctamente', 'success')
                    return redirect(url_for('notificacion_index'))

            # Obtener datos para los selects
            usuarios = conn.execute('SELECT id, nombre FROM usuarios').fetchall()
            camaras = conn.execute('SELECT id, nombre FROM camaras').fetchall()
            
            return render_template('notificacion/add.html',
                                usuarios=usuarios,
                                camaras=camaras)
                                
        except Exception as e:
            app.logger.error(f"Error al agregar notificación: {str(e)}")
            flash('Error al crear la notificación', 'error')
            return render_template('notificacion/add.html',
                                usuarios=usuarios,
                                camaras=camaras)
        finally:
            conn.close()

    @app.route('/notificaciones/edit/<int:id>', methods=['GET', 'POST'])
    def notificacion_edit(id):
        """Edita una notificación existente"""
        conn = get_db_connection()
        
        try:
            notificacion = conn.execute('''
                SELECT n.*, u.nombre as usuario_nombre, c.nombre as camara_nombre
                FROM notificaciones n
                LEFT JOIN usuarios u ON n.id_usuario = u.id
                LEFT JOIN camaras c ON n.id_camara = c.id
                WHERE n.id = ?
            ''', (id,)).fetchone()

            if notificacion is None:
                abort(404)

            if request.method == 'POST':
                mensaje = request.form.get('mensaje', '').strip()
                tipo = request.form.get('tipo', 'info')
                id_usuario = request.form.get('id_usuario')
                id_camara = request.form.get('id_camara')

                if not mensaje:
                    flash('El mensaje es obligatorio', 'error')
                else:
                    conn.execute('''
                        UPDATE notificaciones SET
                            mensaje = ?, tipo = ?, id_usuario = ?, id_camara = ?
                        WHERE id = ?
                    ''', (mensaje, tipo, id_usuario, id_camara, id))
                    
                    conn.commit()
                    flash('Notificación actualizada correctamente', 'success')
                    return redirect(url_for('notificacion_index'))

            # Obtener datos para los selects
            usuarios = conn.execute('SELECT id, nombre FROM usuarios').fetchall()
            camaras = conn.execute('SELECT id, nombre FROM camaras').fetchall()
            
            return render_template('notificacion/edit.html',
                                notificacion=notificacion,
                                usuarios=usuarios,
                                camaras=camaras)
                                
        except Exception as e:
            app.logger.error(f"Error al editar notificación {id}: {str(e)}")
            flash('Error al actualizar la notificación', 'error')
            return redirect(url_for('notificacion_index'))
        finally:
            conn.close()

    @app.route('/notificaciones/delete/<int:id>', methods=['POST'])
    def notificacion_delete(id):
        """Elimina una notificación"""
        if request.method != 'POST':
            abort(405)
            
        try:
            conn = get_db_connection()
            conn.execute('DELETE FROM notificaciones WHERE id = ?', (id,))
            conn.commit()
            flash('Notificación eliminada correctamente', 'success')
        except Exception as e:
            app.logger.error(f"Error al eliminar notificación {id}: {str(e)}")
            flash('Error al eliminar la notificación', 'error')
        finally:
            conn.close()
            
        return redirect(url_for('notificacion_index'))