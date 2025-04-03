from flask import render_template, request, redirect, url_for, flash, abort
from database import get_db_connection

def configure_notificacion_routes(app):


    
    @app.route('/notificaciones')
    def notificacion_index():
        conn = get_db_connection()
        notificaciones = conn.execute('SELECT * FROM notificaciones').fetchall()
        conn.close()
        return render_template('notificacion/index.html', notificaciones=notificaciones)

    @app.route('/notificaciones/add', methods=['GET', 'POST'])
    def notificacion_add():
        if request.method == 'POST':
            mensaje = request.form['mensaje']
            tipo = request.form['tipo']

            if not mensaje or not tipo:
                flash('Mensaje y tipo son obligatorios!', 'error')
            else:
                conn = get_db_connection()
                conn.execute('INSERT INTO notificaciones (mensaje, tipo) VALUES (?, ?)', (mensaje, tipo))
                conn.commit()
                conn.close()
                flash('Notificación agregada correctamente!', 'success')
                return redirect(url_for('notificacion_index'))

        return render_template('notificacion/add.html')

    @app.route('/notificaciones/edit/<int:id>', methods=['GET', 'POST'])
    def notificacion_edit(id):
        conn = get_db_connection()
        notificacion = conn.execute('SELECT * FROM notificaciones WHERE id = ?', (id,)).fetchone()
        conn.close()

        if notificacion is None:
            abort(404)

        if request.method == 'POST':
            mensaje = request.form['mensaje']
            tipo = request.form['tipo']

            if not mensaje or not tipo:
                flash('Mensaje y tipo son obligatorios!', 'error')
            else:
                conn = get_db_connection()
                conn.execute('UPDATE notificaciones SET mensaje = ?, tipo = ? WHERE id = ?', (mensaje, tipo, id))
                conn.commit()
                conn.close()
                flash('Notificación actualizada correctamente!', 'success')
                return redirect(url_for('notificacion_index'))

        return render_template('notificacion/edit.html', notificacion=notificacion)

    @app.route('/notificaciones/delete/<int:id>')
    def notificacion_delete(id):
        conn = get_db_connection()
        conn.execute('DELETE FROM notificaciones WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        flash('Notificación eliminada correctamente!', 'success')
        return redirect(url_for('notificacion_index'))