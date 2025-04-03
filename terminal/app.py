from flask import Flask, render_template
from database import init_db
from routes import configure_all_routes

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Inicializar base de datos
init_db()

# Configurar todas las rutas
configure_all_routes(app)
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)