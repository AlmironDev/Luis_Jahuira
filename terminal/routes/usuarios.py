from flask import render_template, request, redirect, url_for, flash, abort
from database import execute_query

def configure_usuarios_routes(app):
    @app.route('/usuarios')
    def usuarios_index():
        """Lista todos los usuarios registrados"""
        usuarios = execute_query('''
            SELECT *
            FROM usuarios
            ORDER BY nombre ASC
        ''', fetch=True)

        return render_template('usuarios/index.html', usuarios=usuarios)

    @app.route('/usuarios/add', methods=['GET', 'POST'])
    def usuarios_add():
        """Agrega un nuevo usuario al sistema"""
        if request.method == 'POST':
            nombre = request.form.get('nombre')
            username = request.form.get('username')
            dni = request.form.get('dni')
            role = request.form.get('role', 1)
            activo = 'activo' in request.form

            if not nombre or not username or not dni:
                flash('Todos los campos son obligatorios!', 'error')
            else:
                try:
                    execute_query('''
                        INSERT INTO usuarios (
                            nombre, username, dni, role, activo
                        ) VALUES (%s, %s, %s, %s, %s)
                    ''', (
                        nombre, 
                        username, 
                        dni,
                        role,
                        activo
                    ))
                    flash('Usuario creado correctamente!', 'success')
                    return redirect(url_for('usuarios_index'))
                except Exception as e:
                    app.logger.error(f"Error al crear usuario: {str(e)}")
                    flash('Error al crear el usuario. Puede que el username o DNI ya existan.', 'error')

        return render_template('usuarios/add.html')

    @app.route('/usuarios/edit/<int:id>', methods=['GET', 'POST'])
    def usuarios_edit(id):
        """Edita un usuario existente"""
        usuario_result = execute_query('SELECT * FROM usuarios WHERE id = %s', (id,), fetch=True)
        
        if not usuario_result:
            abort(404)

        usuario = usuario_result[0]

        if request.method == 'POST':
            nombre = request.form.get('nombre')
            username = request.form.get('username')
            dni = request.form.get('dni')
            role = request.form.get('role', 1)
            activo = 'activo' in request.form

            if not nombre or not username or not dni:
                flash('Los campos básicos son obligatorios!', 'error')
            else:
                try:
                    execute_query('''
                        UPDATE usuarios SET
                            nombre = %s, username = %s, dni = %s,
                            role = %s, activo = %s
                        WHERE id = %s
                    ''', (nombre, username, dni, role, activo, id))
                    
                    flash('Usuario actualizado correctamente!', 'success')
                    return redirect(url_for('usuarios_index'))
                except Exception as e:
                    app.logger.error(f"Error al actualizar usuario: {str(e)}")
                    flash('Error al actualizar el usuario. Puede que el username o DNI ya existan.', 'error')

        return render_template('usuarios/edit.html', usuario=usuario)

    @app.route('/usuarios/toggle/<int:id>')
    def usuarios_toggle(id):
        """Activa/desactiva un usuario"""
        usuario_result = execute_query('SELECT activo FROM usuarios WHERE id = %s', (id,), fetch=True)
        
        if usuario_result:
            usuario = usuario_result[0]
            new_status = not usuario['activo']
            execute_query('UPDATE usuarios SET activo = %s WHERE id = %s', (new_status, id))
            
            estado = "activado" if new_status else "desactivado"
            flash(f'Usuario {estado} correctamente', 'success')
        
        return redirect(url_for('usuarios_index'))