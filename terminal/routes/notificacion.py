from flask import render_template, request, redirect, url_for, flash, abort
from database import execute_query
from datetime import datetime

def configure_notificacion_routes(app):
    
    @app.route('/notificaciones')
    def notificacion_index():
        """Muestra el listado de notificaciones con paginación"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 10
            
            # Obtener notificaciones con información de usuario y cámara
            notificaciones = execute_query('''
                SELECT n.id, n.mensaje, n.tipo, n.leida, 
                       TO_CHAR(n.fecha, 'DD/MM/YYYY HH24:MI') as fecha_formateada,
                       u.nombre as usuario_nombre,
                       c.nombre as camara_nombre
                FROM notificaciones n
                LEFT JOIN usuarios u ON n.id_usuario = u.id
                LEFT JOIN camaras c ON n.id_camara = c.id
                ORDER BY n.fecha DESC
                LIMIT %s OFFSET %s
            ''', (per_page, (page - 1) * per_page), fetch=True)
            
            total_result = execute_query('SELECT COUNT(*) as count FROM notificaciones', fetch=True)
            total = total_result[0]['count'] if total_result else 0
            
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
            execute_query('UPDATE notificaciones SET leida = true WHERE id = %s', (id,))
            return '', 204  # Respuesta vacía para AJAX
        except Exception as e:
            app.logger.error(f"Error al marcar notificación {id} como leída: {str(e)}")
            return '', 500

    @app.route('/notificaciones/add', methods=['GET', 'POST'])
    def notificacion_add():
        """Agrega una nueva notificación"""
        try:
            # Obtener datos para los selects
            usuarios = execute_query('SELECT id, nombre FROM usuarios', fetch=True)
            camaras = execute_query('SELECT id, nombre FROM camaras', fetch=True)
            
            if request.method == 'POST':
                mensaje = request.form.get('mensaje', '').strip()
                tipo = request.form.get('tipo', 'info')
                id_usuario = request.form.get('id_usuario')
                id_camara = request.form.get('id_camara')

                if not mensaje:
                    flash('El mensaje es obligatorio', 'error')
                else:
                    # Convertir id_usuario e id_camara a None si están vacíos
                    id_usuario = id_usuario if id_usuario else None
                    id_camara = id_camara if id_camara else None
                    
                    execute_query('''
                        INSERT INTO notificaciones 
                        (mensaje, tipo, id_usuario, id_camara, fecha) 
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (mensaje, tipo, id_usuario, id_camara, datetime.now()))
                    
                    flash('Notificación creada correctamente', 'success')
                    return redirect(url_for('notificacion_index'))

            return render_template('notificacion/add.html',
                                usuarios=usuarios,
                                camaras=camaras)
                                
        except Exception as e:
            app.logger.error(f"Error al agregar notificación: {str(e)}")
            flash('Error al crear la notificación', 'error')
            return render_template('notificacion/add.html',
                                usuarios=usuarios,
                                camaras=camaras)

    @app.route('/notificaciones/edit/<int:id>', methods=['GET', 'POST'])
    def notificacion_edit(id):
        """Edita una notificación existente"""
        try:
            notificacion_result = execute_query('''
                SELECT n.*, u.nombre as usuario_nombre, c.nombre as camara_nombre
                FROM notificaciones n
                LEFT JOIN usuarios u ON n.id_usuario = u.id
                LEFT JOIN camaras c ON n.id_camara = c.id
                WHERE n.id = %s
            ''', (id,), fetch=True)

            if not notificacion_result:
                abort(404)

            notificacion = notificacion_result[0]

            # Obtener datos para los selects
            usuarios = execute_query('SELECT id, nombre FROM usuarios', fetch=True)
            camaras = execute_query('SELECT id, nombre FROM camaras', fetch=True)

            if request.method == 'POST':
                mensaje = request.form.get('mensaje', '').strip()
                tipo = request.form.get('tipo', 'info')
                id_usuario = request.form.get('id_usuario')
                id_camara = request.form.get('id_camara')

                if not mensaje:
                    flash('El mensaje es obligatorio', 'error')
                else:
                    # Convertir id_usuario e id_camara a None si están vacíos
                    id_usuario = id_usuario if id_usuario else None
                    id_camara = id_camara if id_camara else None
                    
                    execute_query('''
                        UPDATE notificaciones SET
                            mensaje = %s, tipo = %s, id_usuario = %s, id_camara = %s
                        WHERE id = %s
                    ''', (mensaje, tipo, id_usuario, id_camara, id))
                    
                    flash('Notificación actualizada correctamente', 'success')
                    return redirect(url_for('notificacion_index'))

            return render_template('notificacion/edit.html',
                                notificacion=notificacion,
                                usuarios=usuarios,
                                camaras=camaras)
                                
        except Exception as e:
            app.logger.error(f"Error al editar notificación {id}: {str(e)}")
            flash('Error al actualizar la notificación', 'error')
            return redirect(url_for('notificacion_index'))

    @app.route('/notificaciones/delete/<int:id>', methods=['POST'])
    def notificacion_delete(id):
        """Elimina una notificación"""
        if request.method != 'POST':
            abort(405)
            
        try:
            execute_query('DELETE FROM notificaciones WHERE id = %s', (id,))
            flash('Notificación eliminada correctamente', 'success')
        except Exception as e:
            app.logger.error(f"Error al eliminar notificación {id}: {str(e)}")
            flash('Error al eliminar la notificación', 'error')
            
        return redirect(url_for('notificacion_index'))