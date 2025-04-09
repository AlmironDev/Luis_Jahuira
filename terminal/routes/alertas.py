from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from database import get_db_connection
from datetime import datetime, timedelta
import json

def configure_alertas_routes(app):
    @app.route('/alertas')
    def alertas_index():
        """Muestra la lista de alertas con filtros y paginación"""
        try:
            # Parámetros de paginación
            page = request.args.get('page', 1, type=int)
            per_page = 20
            
            # Parámetros de filtrado
            id_camara = request.args.get('camara', type=int)
            tipo = request.args.get('tipo')
            severidad = request.args.get('severidad')
            resuelta = request.args.get('resuelta', type=int)  # 0 o 1
            dias = request.args.get('dias', type=int)
            
            conn = get_db_connection()
            
            # Construir consulta base
            query = '''
                SELECT a.*, c.nombre as nombre_camara, c.ubicacion
                FROM alertas a
                LEFT JOIN camaras c ON a.id_camara = c.id
                WHERE 1=1
            '''
            params = []
            
            # Aplicar filtros
            if id_camara:
                query += ' AND a.id_camara = ?'
                params.append(id_camara)
            
            if tipo:
                query += ' AND a.tipo = ?'
                params.append(tipo)
            
            if severidad:
                query += ' AND a.severidad = ?'
                params.append(severidad)
            
            if resuelta is not None:
                query += ' AND a.resuelta = ?'
                params.append(resuelta)
            
            if dias:
                fecha_limite = datetime.now() - timedelta(days=dias)
                query += ' AND a.fecha >= ?'
                params.append(fecha_limite.strftime('%Y-%m-%d %H:%M:%S'))
            
            # Contar total para paginación
            count_query = 'SELECT COUNT(*) FROM (' + query + ')'
            total = conn.execute(count_query, params).fetchone()[0]
            
            # Ordenar y paginar
            query += ' ORDER BY a.fecha DESC LIMIT ? OFFSET ?'
            params.extend([per_page, (page - 1) * per_page])
            
            alertas = conn.execute(query, params).fetchall()
            
            # Obtener lista de cámaras para el filtro
            camaras = conn.execute('SELECT id, nombre FROM camaras ORDER BY nombre').fetchall()
            
            conn.close()
            
            return render_template('alertas/index.html',
                                alertas=alertas,
                                camaras=camaras,
                                page=page,
                                per_page=per_page,
                                total=total,
                                filtros={
                                    'camara': id_camara,
                                    'tipo': tipo,
                                    'severidad': severidad,
                                    'resuelta': resuelta,
                                    'dias': dias
                                })
            
        except Exception as e:
            app.logger.error(f"Error al listar alertas: {str(e)}")
            flash('Error al cargar la lista de alertas', 'error')
            return redirect(url_for('index'))
