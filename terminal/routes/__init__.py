from .pausas import configure_pausas_activas_routes
from .login import configure_login_routes
from .camaras import configure_camaras_routes
from .notificacion import configure_notificacion_routes
from .videos import configure_videos_routes
from .usuarios import configure_usuarios_routes
from .alertas import configure_alertas_routes

def configure_all_routes(app):
    configure_videos_routes(app)
    configure_notificacion_routes(app)
    configure_camaras_routes(app)
    configure_usuarios_routes(app)
    configure_alertas_routes(app)
    configure_login_routes(app)
    configure_pausas_activas_routes(app)