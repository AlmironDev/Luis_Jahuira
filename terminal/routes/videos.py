from flask import render_template, request, redirect, url_for, flash, abort
from database import get_db_connection

def configure_camaras_routes(app):
    @app.route('/camaras')
    def camaras_index():
        """Muestra la lista de todas las cámaras registradas"""
        conn = get_db_connection()
        camaras = conn.execute('''
            SELECT id, nombre, url, ubicacion, 
                   strftime('%d/%m/%Y %H:%M', fecha_instalacion) as fecha_instalacion,
                   activa
            FROM camaras
            ORDER BY fecha_instalacion DESC
        ''').fetchall()
        conn.close()
        return render_template('camaras/index.html', camaras=camaras)

    @app.route('/camaras/add', methods=['GET', 'POST'])
    def camaras_add():
        """Agrega una nueva cámara al sistema"""
        if request.method == 'POST':
            nombre = request.form.get('nombre')
            url = request.form.get('url')
            ubicacion = request.form.get('ubicacion', '')
            angulo_min = request.form.get('angulo_min', 45)
            angulo_max = request.form.get('angulo_max', 135)
            hombros_min = request.form.get('hombros_min', 0.5)
            hombros_max = request.form.get('hombros_max', 1.5)
            manos_min = request.form.get('manos_min', 30)
            manos_max = request.form.get('manos_max', 150)
            activa = 1 if request.form.get('activa') else 0

            if not nombre or not url:
                flash('Nombre y URL son campos obligatorios!', 'error')
            else:
                conn = get_db_connection()
                conn.execute('''
                    INSERT INTO camaras (
                        nombre, url, ubicacion, angulo_min, angulo_max,
                        hombros_min, hombros_max, manos_min, manos_max, activa
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    nombre, url, ubicacion, angulo_min, angulo_max,
                    hombros_min, hombros_max, manos_min, manos_max, activa
                ))
                conn.commit()
                conn.close()
                flash('Cámara agregada correctamente!', 'success')
                return redirect(url_for('camaras_index'))

        return render_template('camaras/add.html')

    @app.route('/camaras/edit/<int:id>', methods=['GET', 'POST'])
    def camaras_edit(id):
        """Edita los datos de una cámara existente"""
        conn = get_db_connection()
        camara = conn.execute('SELECT * FROM camaras WHERE id = ?', (id,)).fetchone()
        conn.close()

        if camara is None:
            abort(404)

        if request.method == 'POST':
            nombre = request.form.get('nombre')
            url = request.form.get('url')
            ubicacion = request.form.get('ubicacion', '')
            angulo_min = request.form.get('angulo_min', 45)
            angulo_max = request.form.get('angulo_max', 135)
            hombros_min = request.form.get('hombros_min', 0.5)
            hombros_max = request.form.get('hombros_max', 1.5)
            manos_min = request.form.get('manos_min', 30)
            manos_max = request.form.get('manos_max', 150)
            activa = 1 if request.form.get('activa') else 0

            if not nombre or not url:
                flash('Nombre y URL son campos obligatorios!', 'error')
            else:
                conn = get_db_connection()
                conn.execute('''
                    UPDATE camaras SET
                        nombre = ?, url = ?, ubicacion = ?,
                        angulo_min = ?, angulo_max = ?,
                        hombros_min = ?, hombros_max = ?,
                        manos_min = ?, manos_max = ?,
                        activa = ?
                    WHERE id = ?
                ''', (
                    nombre, url, ubicacion, angulo_min, angulo_max,
                    hombros_min, hombros_max, manos_min, manos_max,
                    activa, id
                ))
                conn.commit()
                conn.close()
                flash('Cámara actualizada correctamente!', 'success')
                return redirect(url_for('camaras_index'))

        return render_template('camaras/edit.html', camara=camara)

    @app.route('/camaras/delete/<int:id>')
    def camaras_delete(id):
        """Elimina una cámara del sistema"""
        conn = get_db_connection()
        
        # Verificar si hay notificaciones asociadas
        notificaciones = conn.execute(
            'SELECT 1 FROM notificaciones WHERE id_camara = ? LIMIT 1',
            (id,)
        ).fetchone()
        
        if notificaciones:
            flash('No se puede eliminar: hay notificaciones asociadas a esta cámara', 'error')
        else:
            conn.execute('DELETE FROM camaras WHERE id = ?', (id,))
            conn.commit()
            flash('Cámara eliminada correctamente!', 'success')
        
        conn.close()
        return redirect(url_for('camaras_index'))

    @app.route('/camaras/toggle/<int:id>')
    def camaras_toggle(id):
        """Activa/desactiva una cámara"""
        conn = get_db_connection()
        camara = conn.execute('SELECT activa FROM camaras WHERE id = ?', (id,)).fetchone()
        
        if camara:
            new_status = 0 if camara['activa'] else 1
            conn.execute('UPDATE camaras SET activa = ? WHERE id = ?', (new_status, id))
            conn.commit()
            estado = "activada" if new_status else "desactivada"
            flash(f'Cámara {estado} correctamente', 'success')
        
        conn.close()
        return redirect(url_for('camaras_index'))