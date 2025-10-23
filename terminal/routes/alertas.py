from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from database import get_db_connection
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
            
            if tipo_angulo:
                query += ' AND a.tipo_angulo = ?'
                params.append(tipo_angulo)
            
            if nivel_alerta:
                query += ' AND a.nivel_alerta = ?'
                params.append(nivel_alerta)
            
            if fecha:
                try:
                    fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
                    query += ' AND date(a.fecha) = date(?)'
                    params.append(fecha_obj.strftime('%Y-%m-%d'))
                except ValueError:
                    flash('Formato de fecha inválido. Use YYYY-MM-DD', 'error')
            
            # Contar total para paginación
            count_query = 'SELECT COUNT(*) FROM (' + query + ')'
            total = conn.execute(count_query, params).fetchone()[0]
            
            # Obtener conteos por nivel de alerta
            counts_query = '''
                SELECT 
                    SUM(CASE WHEN nivel_alerta = 'CRITICAL' THEN 1 ELSE 0 END) as critical,
                    SUM(CASE WHEN nivel_alerta = 'WARNING' THEN 1 ELSE 0 END) as warning
                FROM alertas
            '''
            counts_result = conn.execute(counts_query).fetchone()
            counts = {
                'CRITICAL': counts_result['critical'] or 0,
                'WARNING': counts_result['warning'] or 0
            }
            
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
            angulos_stats = conn.execute(angulos_stats_query).fetchall()
            
            # Ordenar y paginar
            query += ' ORDER BY a.fecha DESC LIMIT ? OFFSET ?'
            params.extend([per_page, (page - 1) * per_page])
            
            alertas = conn.execute(query, params).fetchall()
            
            # Obtener lista de cámaras para el filtro
            camaras = conn.execute('SELECT id, nombre FROM camaras ORDER BY nombre').fetchall()
            
            # Obtener tipos de ángulos únicos para el filtro
            tipos_angulo = conn.execute(
                'SELECT DISTINCT tipo_angulo FROM alertas ORDER BY tipo_angulo'
            ).fetchall()
            
            conn.close()
            
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
            conn = get_db_connection()
            
            # Alertas por día (últimos 7 días)
            alertas_por_dia = conn.execute('''
                SELECT 
                    date(fecha) as dia,
                    nivel_alerta,
                    COUNT(*) as cantidad
                FROM alertas 
                WHERE fecha >= date('now', '-7 days')
                GROUP BY dia, nivel_alerta
                ORDER BY dia DESC
            ''').fetchall()
            
            # Top ángulos problemáticos
            top_angulos = conn.execute('''
                SELECT 
                    tipo_angulo,
                    COUNT(*) as total
                FROM alertas
                GROUP BY tipo_angulo
                ORDER BY total DESC
                LIMIT 10
            ''').fetchall()
            
            # Alertas por cámara
            alertas_por_camara = conn.execute('''
                SELECT 
                    c.nombre,
                    COUNT(*) as total,
                    SUM(CASE WHEN a.nivel_alerta = 'CRITICAL' THEN 1 ELSE 0 END) as critical,
                    SUM(CASE WHEN a.nivel_alerta = 'WARNING' THEN 1 ELSE 0 END) as warning
                FROM alertas a
                JOIN camaras c ON a.id_camara = c.id
                GROUP BY c.id, c.nombre
                ORDER BY total DESC
            ''').fetchall()
            
            conn.close()
            
            return jsonify({
                'alertas_por_dia': [
                    {
                        'dia': row['dia'],
                        'nivel_alerta': row['nivel_alerta'],
                        'cantidad': row['cantidad']
                    } for row in alertas_por_dia
                ],
                'top_angulos': [
                    {
                        'tipo_angulo': row['tipo_angulo'],
                        'total': row['total']
                    } for row in top_angulos
                ],
                'alertas_por_camara': [
                    {
                        'camara': row['nombre'],
                        'total': row['total'],
                        'critical': row['critical'],
                        'warning': row['warning']
                    } for row in alertas_por_camara
                ]
            })
            
        except Exception as e:
            app.logger.error(f"Error en estadísticas: {str(e)}")
            return jsonify({'error': 'Error al cargar estadísticas'}), 500

    @app.route('/alertas/limpiar', methods=['POST'])
    def limpiar_alertas():
        """Elimina alertas antiguas (más de 30 días)"""
        try:
            conn = get_db_connection()
            result = conn.execute(
                'DELETE FROM alertas WHERE fecha < datetime("now", "-30 days")'
            )
            eliminadas = result.rowcount
            conn.commit()
            conn.close()
            
            flash(f'Se eliminaron {eliminadas} alertas antiguas', 'success')
            
        except Exception as e:
            app.logger.error(f"Error limpiando alertas: {str(e)}")
            flash('Error al limpiar alertas antiguas', 'error')
        
        return redirect(url_for('alertas_index'))

    @app.route('/alertas/<int:id>/eliminar', methods=['POST'])
    def eliminar_alerta(id):
        """Elimina una alerta específica"""
        try:
            conn = get_db_connection()
            conn.execute('DELETE FROM alertas WHERE id = ?', (id,))
            conn.commit()
            conn.close()
            
            flash('Alerta eliminada correctamente', 'success')
            
        except Exception as e:
            app.logger.error(f"Error eliminando alerta {id}: {str(e)}")
            flash('Error al eliminar la alerta', 'error')
        
        return redirect(url_for('alertas_index'))