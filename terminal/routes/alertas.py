from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from database import execute_query
from datetime import datetime, timedelta
import json

def configure_alertas_routes(app):
    @app.route('/alertas')
    def alertas_index():
        """Muestra la lista de alertas de postura con filtros y paginación"""
        try:
            # Parámetros de paginación
            page = request.args.get('page', 1, type=int)
            per_page = 20
            
            # Parámetros de filtrado
            id_camara = request.args.get('camara', type=int)
            tipo_angulo = request.args.get('tipo_angulo')
            nivel_alerta = request.args.get('nivel_alerta')
            fecha = request.args.get('fecha')
            
            # Construir consulta base
            query = '''
                SELECT a.*, 
                       c.nombre as nombre_camara, 
                       c.ubicacion,
                       TO_CHAR(a.fecha, 'DD/MM/YYYY HH24:MI:SS') as fecha_formateada
                FROM alertas a
                LEFT JOIN camaras c ON a.id_camara = c.id
                WHERE 1=1
            '''
            params = []
            
            # Aplicar filtros
            if id_camara:
                query += ' AND a.id_camara = %s'
                params.append(id_camara)
            
            if tipo_angulo:
                query += ' AND a.tipo_angulo = %s'
                params.append(tipo_angulo)
            
            if nivel_alerta:
                query += ' AND a.nivel_alerta = %s'
                params.append(nivel_alerta)
            
            if fecha:
                try:
                    fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
                    query += ' AND date(a.fecha) = date(%s)'  # CORREGIDO: quité el "date" duplicado
                    params.append(fecha_obj.strftime('%Y-%m-%d'))
                except ValueError:
                    flash('Formato de fecha inválido. Use YYYY-MM-DD', 'error')
            
            # Contar total para paginación
            count_query = 'SELECT COUNT(*) as count FROM (' + query + ') as subquery'
            count_result = execute_query(count_query, params, fetch=True)
            
            if count_result and len(count_result) > 0:
                total = int(count_result[0]['count']) 
            else:
                total = 0
            
            # Obtener conteos por nivel de alerta
            counts_query = '''
                SELECT 
                    COUNT(*) FILTER (WHERE nivel_alerta = 'CRITICAL') as critical,
                    COUNT(*) FILTER (WHERE nivel_alerta = 'WARNING') as warning
                FROM alertas
            '''
            counts_result = execute_query(counts_query, fetch=True)
            
            counts = {'CRITICAL': 0, 'WARNING': 0}
            if counts_result and len(counts_result) > 0:
                counts_row = counts_result[0]
                if counts_row['critical'] is not None:
                    counts['CRITICAL'] = int(counts_row['critical'])
                if counts_row['warning'] is not None:
                    counts['WARNING'] = int(counts_row['warning'])
            
            # Obtener estadísticas de tipos de ángulos problemáticos
            angulos_stats_query = '''
                SELECT 
                    tipo_angulo,
                    COUNT(*) as total,
                    AVG(valor_angulo) as promedio,
                    MIN(valor_angulo) as minimo,
                    MAX(valor_angulo) as maximo
                FROM alertas 
                GROUP BY tipo_angulo 
                ORDER BY total DESC
            '''
            angulos_stats_result = execute_query(angulos_stats_query, fetch=True)
            
            angulos_stats = []
            if angulos_stats_result:
                for row in angulos_stats_result:
                    angulos_stats.append({
                        'tipo_angulo': row['tipo_angulo'],
                        'total': int(row['total']),
                        'promedio': float(row['promedio']) if row['promedio'] is not None else 0,
                        'minimo': float(row['minimo']) if row['minimo'] is not None else 0,
                        'maximo': float(row['maximo']) if row['maximo'] is not None else 0
                    })
            
            # Ordenar y paginar
            query += ' ORDER BY a.fecha DESC LIMIT %s OFFSET %s'
            params.extend([per_page, (page - 1) * per_page])
            
            alertas_result = execute_query(query, params, fetch=True)
            
            # Procesar alertas para formatear fechas
            alertas = []
            if alertas_result:
                for alerta in alertas_result:
                    # Convertir a diccionario y asegurar que todos los campos estén presentes
                    alerta_dict = {}
                    for key in alerta.keys():
                        alerta_dict[key] = alerta[key]
                    
                    # Asegurar que tenemos fecha_formateada
                    if 'fecha_formateada' not in alerta_dict or not alerta_dict['fecha_formateada']:
                        fecha_obj = alerta_dict.get('fecha')
                        if isinstance(fecha_obj, datetime):
                            alerta_dict['fecha_formateada'] = fecha_obj.strftime('%d/%m/%Y %H:%M:%S')
                        else:
                            alerta_dict['fecha_formateada'] = str(fecha_obj) if fecha_obj else 'N/A'
                    
                    alertas.append(alerta_dict)
            
            # Obtener lista de cámaras para el filtro
            camaras_result = execute_query('SELECT id, nombre FROM camaras ORDER BY nombre', fetch=True)
            camaras = list(camaras_result) if camaras_result else []
            
            # Obtener tipos de ángulos únicos para el filtro
            tipos_angulo_result = execute_query(
                'SELECT DISTINCT tipo_angulo FROM alertas ORDER BY tipo_angulo', 
                fetch=True
            )
            tipos_angulo = [row['tipo_angulo'] for row in tipos_angulo_result] if tipos_angulo_result else []
            
            return render_template('alertas/index.html',
                                alertas=alertas,
                                camaras=camaras,
                                tipos_angulo=tipos_angulo,
                                page=page,
                                per_page=per_page,
                                total=total,
                                counts=counts,
                                angulos_stats=angulos_stats,
                                filtros={
                                    'camara': id_camara,
                                    'tipo_angulo': tipo_angulo,
                                    'nivel_alerta': nivel_alerta,
                                    'fecha': fecha
                                })
            
        except Exception as e:
            app.logger.error(f"Error al listar alertas: {str(e)}")
            flash('Error al cargar la lista de alertas', 'error')
            return redirect(url_for('index'))

    @app.route('/alertas/estadisticas')
    def alertas_estadisticas():
        """Endpoint para estadísticas de alertas (para gráficos)"""
        try:
            # Alertas por día (últimos 7 días)
            alertas_por_dia_result = execute_query('''
                SELECT 
                    date(fecha) as dia,
                    nivel_alerta,
                    COUNT(*) as cantidad
                FROM alertas 
                WHERE fecha >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY dia, nivel_alerta
                ORDER BY dia DESC
            ''', fetch=True) or []
            
            # Convertir a tipos nativos
            alertas_por_dia = []
            for row in alertas_por_dia_result:
                dia = row['dia']
                if hasattr(dia, 'strftime'):
                    dia_str = dia.strftime('%Y-%m-%d')
                else:
                    dia_str = str(dia)
                
                alertas_por_dia.append({
                    'dia': dia_str,
                    'nivel_alerta': row['nivel_alerta'],
                    'cantidad': int(row['cantidad'])
                })
            
            # Top ángulos problemáticos
            top_angulos_result = execute_query('''
                SELECT 
                    tipo_angulo,
                    COUNT(*) as total
                FROM alertas
                GROUP BY tipo_angulo
                ORDER BY total DESC
                LIMIT 10
            ''', fetch=True) or []
            
            top_angulos = []
            for row in top_angulos_result:
                top_angulos.append({
                    'tipo_angulo': row['tipo_angulo'],
                    'total': int(row['total'])
                })
            
            # Alertas por cámara
            alertas_por_camara_result = execute_query('''
                SELECT 
                    c.nombre,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE a.nivel_alerta = 'CRITICAL') as critical,
                    COUNT(*) FILTER (WHERE a.nivel_alerta = 'WARNING') as warning
                FROM alertas a
                JOIN camaras c ON a.id_camara = c.id
                GROUP BY c.id, c.nombre
                ORDER BY total DESC
            ''', fetch=True) or []
            
            alertas_por_camara = []
            for row in alertas_por_camara_result:
                alertas_por_camara.append({
                    'camara': row['nombre'],
                    'total': int(row['total']),
                    'critical': int(row['critical']) if row['critical'] is not None else 0,
                    'warning': int(row['warning']) if row['warning'] is not None else 0
                })
            
            return jsonify({
                'alertas_por_dia': alertas_por_dia,
                'top_angulos': top_angulos,
                'alertas_por_camara': alertas_por_camara
            })
            
        except Exception as e:
            app.logger.error(f"Error en estadísticas: {str(e)}")
            return jsonify({'error': 'Error al cargar estadísticas'}), 500

    @app.route('/alertas/limpiar', methods=['POST'])
    def limpiar_alertas():
        """Elimina alertas antiguas (más de 30 días)"""
        try:
            # Primero contar cuántas se van a eliminar
            count_result = execute_query(
                "SELECT COUNT(*) as count FROM alertas WHERE fecha < CURRENT_DATE - INTERVAL '30 days'",
                fetch=True
            )
            
            eliminadas = int(count_result[0]['count']) if count_result and count_result[0] else 0
            
            # Luego eliminarlas
            if eliminadas > 0:
                execute_query(
                    "DELETE FROM alertas WHERE fecha < CURRENT_DATE - INTERVAL '30 days'"
                )
            
            flash(f'Se eliminaron {eliminadas} alertas antiguas', 'success')
            
        except Exception as e:
            app.logger.error(f"Error limpiando alertas: {str(e)}")
            flash('Error al limpiar alertas antiguas', 'error')
        
        return redirect(url_for('alertas_index'))

    @app.route('/alertas/<int:id>/eliminar', methods=['POST'])
    def eliminar_alerta(id):
        """Elimina una alerta específica"""
        try:
            execute_query('DELETE FROM alertas WHERE id = %s', (id,))
            flash('Alerta eliminada correctamente', 'success')
            
        except Exception as e:
            app.logger.error(f"Error eliminando alerta {id}: {str(e)}")
            flash('Error al eliminar la alerta', 'error')
        
        return redirect(url_for('alertas_index'))