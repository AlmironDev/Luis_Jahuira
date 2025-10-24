from flask import Flask
from database import init_db
from routes import configure_all_routes
from services.camera_manager import camera_manager

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Inicializar base de datos
init_db()
camera_manager.start() 

# Configurar todas las rutas
configure_all_routes(app)


if __name__ == "__main__":
    # Especificar host y puerto explícitamente
    app.run(host="0.0.0.0", port=5000, debug=False)
