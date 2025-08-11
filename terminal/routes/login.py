from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from database import get_db_connection
from functools import wraps

def configure_login_routes(app):

    @app.route('/index')
    def index():
        return render_template('index.html')

    @app.route('/')
    def init():
        return render_template('login.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Maneja el inicio de sesión de usuarios"""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                flash('Usuario y contraseña son obligatorios', 'error')
                return redirect(url_for('login'))

            conn = get_db_connection()
            try:
                user = conn.execute(
                    'SELECT * FROM usuarios WHERE username = ?', (username,)
                ).fetchone()

                # Validar si existe el usuario
                if user is None:
                    flash('Usuario o contraseña incorrectos', 'error')
                    return redirect(url_for('login'))

                # Verificar la contraseña hasheada
                if not check_password_hash(user['password'], password):
                    flash('Usuario o contraseña incorrectos', 'error')
                    return redirect(url_for('login'))

                # Verificar si el usuario está activo
                if not user['activo']:
                    flash('Tu cuenta está desactivada', 'error')
                    return redirect(url_for('login'))

                # Guardar información del usuario en la sesión
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']

                flash('Has iniciado sesión correctamente', 'success')
                return redirect(url_for('index'))

            except Exception as e:
                flash(f'Ocurrió un error: {str(e)}', 'error')
                return redirect(url_for('login'))

            finally:
                conn.close()

        # Si es GET, mostrar el formulario de login
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        """Cierra la sesión del usuario"""
        session.clear()
        flash('Has cerrado sesión correctamente', 'success')
        return redirect(url_for('login'))


def login_required(role=None):
    """Decorador para requerir login y opcionalmente un rol específico"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Por favor inicia sesión para acceder a esta página', 'error')
                return redirect(url_for('login'))

            if role and session.get('role') != role:
                flash('No tienes permisos para acceder a esta página', 'error')
                return redirect(url_for('index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
