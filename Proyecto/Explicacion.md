# Documentación del Sistema Hotelero 

##  Descripción General
Sistema completo de gestión hotelera con API RESTful (Flask + DynamoDB) e interfaz web moderna.

##  Endpoints de la API

### 1. Endpoints CRUD Estándar

#### GET `/datos/<tabla>` - Listar datos con paginación
```python
@app.route('/datos/<tabla>', methods=['GET'])
def listar_datos(tabla):
    """Listar todos los datos de una tabla con paginación"""
    if tabla not in TABLES:
        return jsonify({"error": "Tabla no encontrada"}), 404
    
    table_info = TABLES[tabla]
    table = table_info['table']
    
    limit = request.args.get('limit', default=50, type=int)
    last_key = request.args.get('last_key', default=None)
    
    try:
        scan_params = {'Limit': limit}
        
        if last_key:
            scan_params['ExclusiveStartKey'] = json.loads(last_key)
        
        response = table.scan(**scan_params)
        items = response.get('Items', [])
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        items_serializables = convertir_para_json(items)
        
        result = {
            "items": items_serializables,
            "count": len(items),
            "has_more": last_evaluated_key is not None
        }
        
        if last_evaluated_key:
            last_key_serializable = convertir_para_json(last_evaluated_key)
            result["last_key"] = json.dumps(last_key_serializable, cls=DecimalEncoder)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```
#### GET `/datos/<tabla>/<id>` - Obtener dato específico
```python
@app.route('/datos/<tabla>/<id>', methods=['GET'])
def obtener_dato(tabla, id):
    """Obtener un dato específico por ID"""
    if tabla not in TABLES:
        return jsonify({"error": "Tabla no encontrada"}), 404
    
    table_info = TABLES[tabla]
    table = table_info['table']
    search_key = table_info['search_key']
    
    try:
        if tabla in ['clientes', 'limpiadores']:
            if not id.startswith(f"{tabla.upper()}#"):
                id = f"{tabla.upper()}#{id}"
        
        items = buscar_por_atributo(table, search_key, id)
        
        if len(items) > 0:
            return jsonify(items[0])
        else:
            return jsonify({"error": "No encontrado"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```
#### POST `/datos/<tabla>` - Crear nuevo dato
```python
@app.route('/datos/<tabla>', methods=['POST'])
def crear_dato(tabla):
    """Crear un nuevo dato"""
    if tabla not in TABLES:
        return jsonify({"error": "Tabla no encontrada"}), 404
    
    table_info = TABLES[tabla]
    table = table_info['table']
    data = request.get_json()
    
    if 'PK' not in data:
        if tabla == 'reservas':
            reserva_id = data.get('idReserva', f"R{str(uuid.uuid4())[:8].upper()}")
            data['PK'] = f"RESERVA#{data.get('fechaInicio', '2025-01-01')}#{reserva_id}"
            data['SK'] = 'METADATOS'
            data['idReserva'] = reserva_id
        elif tabla == 'clientes':
            cliente_id = data.get('idCliente', f"C{str(uuid.uuid4())[:8].upper()}")
            data['PK'] = f"CLIENTE#{cliente_id}"
            data['SK'] = 'PERFIL'
            data['idCliente'] = cliente_id
        elif tabla == 'limpiadores':
            limpiador_id = data.get('idEmpleado', f"L{str(uuid.uuid4())[:8].upper()}")
            data['PK'] = f"PERSONALLIMPIEZA#{limpiador_id}"
            data['SK'] = 'PERFIL'
            data['idEmpleado'] = limpiador_id
        elif tabla == 'habitaciones':
            habitacion_num = data.get('numeroHabitacion', '100')
            data['PK'] = f"HABITACIONES#{habitacion_num}"
            data['SK'] = 'CONFIGURACION'
        elif tabla == 'asignaciones':
            fecha = data.get('fecha', '2025-01-01').split(' ')[0]
            id_limpiador = data.get('idLimpiador', 'L001')
            id_reserva = data.get('idReserva', 'R001')
            data['PK'] = f"ASIGNACIONES#{fecha}"
            data['SK'] = f"PERSONALLIMPIEZA#{id_limpiador}#{id_reserva}"
        elif tabla == 'agenda':
            fecha = data.get('fecha', '2025-01-01')
            zona = data.get('zona', 'NORTE')
            hora = data.get('franjaHoraria', '08:00-09:00').split('-')[0]
            data['PK'] = f"AGENDALIMPIEZA#{fecha}"
            data['SK'] = f"ZONA#{zona}#{hora}"
    
    try:
        for key, value in data.items():
            if isinstance(value, (int, float)):
                data[key] = Decimal(str(value))
        
        table.put_item(Item=data)
        
        return jsonify({
            "message": "Creado exitosamente",
            "data": data
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

#### PUT `/datos/<tabla>/<id>` - Actualizar dato existente
```python
@app.route('/datos/<tabla>/<id>', methods=['PUT'])
def actualizar_dato(tabla, id):
    """Actualizar un dato existente"""
    if tabla not in TABLES:
        return jsonify({"error": "Tabla no encontrada"}), 404
    
    table_info = TABLES[tabla]
    table = table_info['table']
    search_key = table_info['search_key']
    
    try:
        if tabla in ['clientes', 'limpiadores']:
            if not id.startswith(f"{tabla.upper()}#"):
                id = f"{tabla.upper()}#{id}"
        
        items = buscar_por_atributo(table, search_key, id)
        
        if len(items) == 0:
            return jsonify({"error": "No encontrado"}), 404
        
        existing_item = items[0]
        pk_value = existing_item.get('PK')
        sk_value = existing_item.get('SK')
        
        data = request.get_json()
        data['PK'] = pk_value
        if sk_value:
            data['SK'] = sk_value
        
        for key, value in data.items():
            if isinstance(value, (int, float)):
                data[key] = Decimal(str(value))
        
        table.put_item(Item=data)
        
        return jsonify({
            "message": "Actualizado exitosamente",
            "id": id
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```
#### DELETE `/datos/<tabla>/<id>` - Eliminar dato
```python
@app.route('/datos/<tabla>/<id>', methods=['DELETE'])
def eliminar_dato(tabla, id):
    """Eliminar un dato"""
    if tabla not in TABLES:
        return jsonify({"error": "Tabla no encontrada"}), 404
    
    table_info = TABLES[tabla]
    table = table_info['table']
    search_key = table_info['search_key']
    
    try:
        if tabla in ['clientes', 'limpiadores']:
            if not id.startswith(f"{tabla.upper()}#"):
                id = f"{tabla.upper()}#{id}"
        
        items = buscar_por_atributo(table, search_key, id)
        
        if len(items) == 0:
            return jsonify({"error": "No encontrado"}), 404
        
        existing_item = items[0]
        pk_value = existing_item.get('PK')
        sk_value = existing_item.get('SK')
        
        if sk_value:
            table.delete_item(Key={'PK': pk_value, 'SK': sk_value})
        else:
            table.delete_item(Key={'PK': pk_value})
        
        return jsonify({
            "message": "Eliminado exitosamente",
            "id": id
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```
### 2. Endpoint de Consulta Compleja 
```python
@app.route('/reporte_complejo', methods=['GET'])
def reporte_complejo():
    """
    CONSULTA COMPLEJA: Reporte integrado del sistema hotelero
    Combina datos de múltiples tablas:
    1. Reservas VIP activas (prioridad ALTA/MEDIA, duración ≥ 3 días)
    2. Personal calificado disponible (calificación > 4.0)
    3. Habitaciones de lujo (SUITE, PRESIDENCIAL)
    4. Estadísticas consolidadas
    """
    try:
        resultados = {
            "reporte_generado": datetime.now().isoformat(),
            "resumen": {},
            "reservas_vip": [],
            "personal_calificado": [],
            "habitaciones_lujo": [],
            "estadisticas": {}
        }
        
        
        try:
            reservas_response = table_reservas.scan(
                FilterExpression=Attr('estado').eq('CONFIRMADA')
            )
            
            reservas_items = convertir_para_json(reservas_response.get('Items', []))
            
            for reserva in reservas_items:
                try:
                    prioridad = reserva.get('prioridad', '').upper()
                    if prioridad not in ['ALTA', 'MEDIA']:
                        continue
                    
                    fecha_inicio_str = reserva.get('fechaInicio', '')
                    fecha_fin_str = reserva.get('fechaFin', '')
                    
                    if fecha_inicio_str and fecha_fin_str:
                        try:
                            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
                            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
                            duracion = (fecha_fin - fecha_inicio).days
                            
                            if duracion >= 3:
                                monto_total = reserva.get('montoTotal', 0)
                                if isinstance(monto_total, Decimal):
                                    monto_total = float(monto_total)
                                
                                reserva_info = {
                                    'idReserva': reserva.get('idReserva', ''),
                                    'idCliente': reserva.get('idCliente', ''),
                                    'nombreCliente': reserva.get('nombreCliente', ''),
                                    'duracion_estadia': duracion,
                                    'fechaInicio': fecha_inicio_str,
                                    'fechaFin': fecha_fin_str,
                                    'montoTotal': monto_total,
                                    'numeroHabitacion': reserva.get('numeroHabitacion', ''),
                                    'prioridad': prioridad,
                                    'estadoPago': reserva.get('estadoPago', '')
                                }
                                resultados['reservas_vip'].append(reserva_info)
                        except:
                            continue
                except:
                    continue
        except:
            resultados['reservas_vip'] = []
        
        
        try:
            limpiadores_response = table_limpiadores.scan(
                FilterExpression=Attr('estadoActual').eq('DISPONIBLE')
            )
            
            limpiadores_items = convertir_para_json(limpiadores_response.get('Items', []))
            
            for limpiador in limpiadores_items:
                try:
                    calificacion = limpiador.get('calificacionPromedio', 0)
                    if isinstance(calificacion, Decimal):
                        calificacion = float(calificacion)
                    elif isinstance(calificacion, str):
                        try:
                            calificacion = float(calificacion)
                        except:
                            calificacion = 0
                    
                    if calificacion > 4.0:
                        pk = limpiador.get('PK', '')
                        empleado_id = pk.replace('LIMPIADOR#', '') if pk.startswith('LIMPIADOR#') else pk
                        
                        limpiador_info = {
                            'PK': pk,
                            'idEmpleado': empleado_id,
                            'nombre': limpiador.get('nombre', ''),
                            'calificacionPromedio': calificacion,
                            'zonaAsignada': limpiador.get('zonaAsignada', ''),
                            'especialidades': limpiador.get('especialidades', []),
                            'asignacionesTotales': limpiador.get('asignacionesTotales', 0),
                            'estadoActual': limpiador.get('estadoActual', '')
                        }
                        resultados['personal_calificado'].append(limpiador_info)
                except:
                    continue
        except:
            resultados['personal_calificado'] = []
        
        
        try:
            habitaciones_response = table_habitacion.scan()
            habitaciones_items = convertir_para_json(habitaciones_response.get('Items', []))
            
            for habitacion in habitaciones_items:
                try:
                    tipo_habitacion = habitacion.get('tipoHabitacion', '').upper()
                    if tipo_habitacion not in ['SUITE', 'PRESIDENCIAL']:
                        continue
                    
                    estado = habitacion.get('estadoActual', '').upper()
                    if estado not in ['DISPONIBLE', 'MANTENIMIENTO']:
                        continue
                    
                    pk = habitacion.get('PK', '')
                    numero_habitacion = habitacion.get('numeroHabitacion', '')
                    if not numero_habitacion and pk.startswith('HABITACION#'):
                        numero_habitacion = pk.replace('HABITACION#', '')
                    
                    habitacion_info = {
                        'PK': pk,
                        'numeroHabitacion': numero_habitacion,
                        'tipoHabitacion': tipo_habitacion,
                        'piso': habitacion.get('piso', ''),
                        'estadoActual': estado,
                        'ultimaLimpieza': habitacion.get('ultimaLimpieza', ''),
                        'comodidades': habitacion.get('comodidades', []),
                        'zona': habitacion.get('zona', '')
                    }
                    resultados['habitaciones_lujo'].append(habitacion_info)
                except:
                    continue
        except:
            resultados['habitaciones_lujo'] = []
        
        
        try:
            total_reservas_vip = len(resultados['reservas_vip'])
            total_personal = len(resultados['personal_calificado'])
            
            monto_total_vip = 0
            for reserva in resultados['reservas_vip']:
                monto = reserva.get('montoTotal', 0)
                if isinstance(monto, (int, float, Decimal)):
                    if isinstance(monto, Decimal):
                        monto = float(monto)
                    monto_total_vip += monto
            
            total_calificacion = 0
            for limpiador in resultados['personal_calificado']:
                calificacion = limpiador.get('calificacionPromedio', 0)
                if isinstance(calificacion, (int, float, Decimal)):
                    if isinstance(calificacion, Decimal):
                        calificacion = float(calificacion)
                    total_calificacion += calificacion
            
            promedio_calificacion = total_calificacion / total_personal if total_personal > 0 else 0
            
            total_duracion = 0
            for reserva in resultados['reservas_vip']:
                duracion = reserva.get('duracion_estadia', 0)
                if isinstance(duracion, (int, float)):
                    total_duracion += duracion
            
            promedio_duracion = total_duracion / total_reservas_vip if total_reservas_vip > 0 else 0
            
            resultados['estadisticas'] = {
                'total_reservas_vip': total_reservas_vip,
                'total_personal_calificado': total_personal,
                'total_habitaciones_lujo': len(resultados['habitaciones_lujo']),
                'monto_total_reservas_vip': round(monto_total_vip, 2),
                'promedio_calificacion_personal': round(promedio_calificacion, 1),
                'promedio_duracion_estadia': round(promedio_duracion, 1)
            }
        except:
            resultados['estadisticas'] = {
                'total_reservas_vip': 0,
                'total_personal_calificado': 0,
                'total_habitaciones_lujo': 0,
                'monto_total_reservas_vip': 0,
                'promedio_calificacion_personal': 0,
                'promedio_duracion_estadia': 0
            }
        
        
        resultados['resumen'] = {
            'titulo': 'Reporte Complejo del Sistema Hotelero',
            'descripcion': 'Analisis integrado de reservas VIP, personal calificado y habitaciones de lujo',
            'fecha_generacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'COMPLETADO'
        }
        
        resultados_serializables = convertir_para_json(resultados)
        return jsonify(resultados_serializables)
        
    except Exception as e:
        return jsonify({
            "error": "Error en reporte complejo",
            "detalles": str(e)
        }), 500
```
### Como ejecutar
En primer lugar debes ejecutar el archivo CRUD.py el cual te generara un link para visitar la pagina web
### En caso de Error 
si por alguna casualidad tienes algun error por lo unico que puede ser es por el nombre de tus tablas 
