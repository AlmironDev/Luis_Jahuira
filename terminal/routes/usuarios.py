from flask import render_template, request, redirect, url_for, flash, abort

from database import get_db_connection


def configure_usuarios_routes(app):
    @app.route('/usuarios')
    def usuarios_index():
        """Lista todos los usuarios registrados"""
        conn = get_db_connection()
        usuarios = conn.execute('''
            SELECT *
            FROM usuarios
            ORDER BY nombre ASC
        ''').fetchall()

        conn.close()
        return render_template('usuarios/index.html', usuarios=usuarios)

    @app.route('/usuarios/add', methods=['GET', 'POST'])
    def usuarios_add():
        """Agrega un nuevo usuario al sistema"""
        if request.method == 'POST':
            nombre = request.form.get('nombre')
            username = request.form.get('username')
            dni = request.form.get('dni')
            role = request.form.get('role', 1)
            activo = 1 if request.form.get('activo') else 0

            if not nombre or not username  or not dni:
                flash('Todos los campos son obligatorios!', 'error')
            else:
                conn = get_db_connection()
                try:
                    conn.execute('''
                        INSERT INTO usuarios (
                            nombre, username, dni, role, activo
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        nombre, 
                        username, 
                        dni,
                        role,
                        activo
                    ))
                    conn.commit()
                    flash('Usuario creado correctamente!', 'success')
                    return redirect(url_for('usuarios_index'))

                finally:
                    conn.close()

        return render_template('usuarios/add.html')

    @app.route('/usuarios/edit/<int:id>', methods=['GET', 'POST'])
    def usuarios_edit(id):
        """Edita un usuario existente"""
        conn = get_db_connection()
        usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (id,)).fetchone()
        conn.close()

        if usuario is None:
            abort(404)

        if request.method == 'POST':
            nombre = request.form.get('nombre')
            username = request.form.get('username')
            dni = request.form.get('dni')
            role = request.form.get('role', 1)
            activo = 1 if request.form.get('activo') else 0

            if not nombre or not username or not dni:
                flash('Los campos básicos son obligatorios!', 'error')
            else:
                conn = get_db_connection()
                try:
                   
                    conn.execute('''
                        UPDATE usuarios SET
                            nombre = ?, username = ?, dni = ?,
                            role = ?, activo = ?
                        WHERE id = ?
                    ''', (nombre, username, dni, role, activo, id))
                    
                    conn.commit()
                    flash('Usuario actualizado correctamente!', 'success')
                    return redirect(url_for('usuarios_index'))

                finally:
                    conn.close()

        return render_template('usuarios/edit.html', usuario=usuario)

    @app.route('/usuarios/toggle/<int:id>')
    def usuarios_toggle(id):
        """Activa/desactiva un usuario"""
        conn = get_db_connection()
        usuario = conn.execute('SELECT activo FROM usuarios WHERE id = ?', (id,)).fetchone()
        
        if usuario:
            new_status = 0 if usuario['activo'] else 1
            conn.execute('UPDATE usuarios SET activo = ? WHERE id = ?', (new_status, id))
            conn.commit()
            estado = "activado" if new_status else "desactivado"
            flash(f'Usuario {estado} correctamente', 'success')
        
        conn.close()
        return redirect(url_for('usuarios_index'))