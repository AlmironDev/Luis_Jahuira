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

            fecha = request.args.get('fecha')
            print("fecha",fecha)
            
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
            
            print("fecha",fecha)
            # if fecha:
            #     query += f" AND a.fecha = date('{fecha}')"
            if fecha:
                try:
                    # Validar y convertir el formato de fecha
                    fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
                    # Usar parámetros preparados para seguridad
                    query += ' AND date(a.fecha) = date(?)'
                    params.append(fecha_obj.strftime('%Y-%m-%d'))
                except ValueError:
                    flash('Formato de fecha inválido. Use YYYY-MM-DD', 'error')
               
            
            # Contar total para paginación
            count_query = 'SELECT COUNT(*) FROM (' + query + ')'
            
            print("count_query",count_query)
            total = conn.execute(count_query, params).fetchone()[0]
            
            # Obtener conteos por severidad (NUEVO)
            counts_query = '''
                SELECT 
                    SUM(CASE WHEN severidad = 'CRITICAL' THEN 1 ELSE 0 END) as critical,
                    SUM(CASE WHEN severidad = 'WARNING' THEN 1 ELSE 0 END) as warning,
                    SUM(CASE WHEN severidad = 'INFO' THEN 1 ELSE 0 END) as info
                FROM alertas
            '''
            counts_result = conn.execute(counts_query).fetchone()
            counts = {
                'CRITICAL': counts_result['critical'],
                'WARNING': counts_result['warning'],
                'INFO': counts_result['info']
            }
            
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
                                counts=counts,  # NUEVO: agregamos los conteos
                                filtros={
                                    'camara': id_camara,
                                    'tipo': tipo,
                                    'severidad': severidad
                                })
            
        except Exception as e:
            app.logger.error(f"Error al listar alertas: {str(e)}")
            flash('Error al cargar la lista de alertas', 'error')
            return redirect(url_for('index'))