from .camaras import configure_camaras_routes
from .notificacion import configure_notificacion_routes
from .videos import configure_videos_valida_routes
from .usuarios import configure_usuarios_routes

def configure_all_routes(app):
    configure_videos_valida_routes(app)
    configure_notificacion_routes(app)
    configure_camaras_routes(app)
    configure_usuarios_routes(app)