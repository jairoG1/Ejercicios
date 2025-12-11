import boto3
from boto3.dynamodb.conditions import Attr, Key
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import uuid
from decimal import Decimal
import json
from datetime import datetime, timedelta
import traceback

app = Flask(__name__)
CORS(app)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) if obj % 1 != 0 else int(obj)
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', 'ignore')
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super(DecimalEncoder, self).default(obj)

app.json_encoder = DecimalEncoder

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Tablas
table_reservas = dynamodb.Table('Reservas')
table_clientes = dynamodb.Table('Clientes')
table_habitacion = dynamodb.Table('Habitaciones')
table_limpiadores = dynamodb.Table('PersonalLimpieza')
table_asignacion = dynamodb.Table('Asignaciones')
table_limpieza = dynamodb.Table('AgendaLimpieza')

# Mapeo de tablas ESPECÍFICO PARA AGENDA
TABLES = {
    'reservas': {
        'table': table_reservas,
        'pk_name': 'PK',
        'sk_name': 'SK',
        'pk_prefix': 'RESERVA#',
        'sk_default': 'METADATOS',
        'id_field': 'idReserva'
    },
    'clientes': {
        'table': table_clientes,
        'pk_name': 'PK',
        'sk_name': 'SK',
        'pk_prefix': 'CLIENTE#',
        'sk_default': 'PERFIL',
        'id_field': None
    },
    'limpiadores': {
        'table': table_limpiadores,
        'pk_name': 'PK',
        'sk_name': 'SK',
        'pk_prefix': 'LIMPIADOR#',
        'sk_default': 'PERFIL',
        'id_field': None
    },
    'habitaciones': {
        'table': table_habitacion,
        'pk_name': 'PK',
        'sk_name': 'SK',
        'pk_prefix': 'HABITACION#',
        'sk_default': 'CONFIGURACION',
        'id_field': 'numeroHabitacion'
    },
    'asignaciones': {
        'table': table_asignacion,
        'pk_name': 'PK',
        'sk_name': 'SK',
        'pk_prefix': 'ASIGNACION#',
        'sk_default': None,
        'id_field': 'SK'
    },
    'agenda': {
        'table': table_limpieza,
        'pk_name': 'PK',
        'sk_name': 'SK',
        'pk_prefix': 'AGENDA#',
        'sk_default': None,
        'id_field': 'PK'  # Para agenda usamos PK como ID
    }
}

def convertir_para_json(data):
    """Convertir datos de DynamoDB a tipos serializables JSON - CORREGIDO"""
    if isinstance(data, list):
        return [convertir_para_json(item) for item in data]
    elif isinstance(data, dict):
        result = {}
        for key, value in data.items():
            try:
                result[key] = convertir_para_json(value)
            except:
                result[key] = str(value)  # Convertir a string si hay error
        return result
    elif isinstance(data, Decimal):
        try:
            return float(data) if data % 1 != 0 else int(data)
        except:
            return str(data)
    elif isinstance(data, set):
        return list(data)
    elif isinstance(data, bytes):
        try:
            return data.decode('utf-8', 'ignore')
        except:
            return str(data)
    else:
        return data

def construir_claves_agenda(id_input=None, data=None):
    """Construir PK y SK específicamente para Agenda - SIMPLIFICADO"""
    if data:
        # Para crear/actualizar con datos completos
        if 'PK' in data and 'SK' in data:
            return data['PK'], data['SK']
        elif 'fecha' in data and 'zona' in data and 'franjaHoraria' in data:
            fecha = str(data['fecha']).strip()
            zona = str(data['zona']).strip()
            hora = str(data['franjaHoraria']).split('-')[0].strip()
            return f"AGENDA#{fecha}", f"ZONA#{zona}#{hora}"
        elif 'fecha' in data:
            return f"AGENDA#{data['fecha']}", "ZONA#NORTE#08:00"
    
    # Para búsqueda/eliminación
    if id_input:
        if id_input.startswith('AGENDA#'):
            # Si viene PK completa
            if '#' in id_input and 'ZONA#' in id_input:
                # Formato completo: AGENDA#fecha#ZONA#zona#hora
                parts = id_input.split('#')
                if len(parts) >= 5:
                    pk = '#'.join(parts[:2])  # AGENDA#fecha
                    sk = '#'.join(parts[2:])  # ZONA#zona#hora
                    return pk, sk
                else:
                    return id_input, "ZONA#NORTE#08:00"
            else:
                return id_input, "ZONA#NORTE#08:00"
        else:
            # Si solo viene fecha
            return f"AGENDA#{id_input}", "ZONA#NORTE#08:00"
    
    # Por defecto
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    return f"AGENDA#{fecha_hoy}", "ZONA#NORTE#08:00"

def construir_claves(tabla, id_input=None, data=None):
    """Construir PK y SK según el tipo de tabla"""
    if tabla == 'agenda':
        return construir_claves_agenda(id_input, data)
    
    table_info = TABLES[tabla]
    pk_prefix = table_info['pk_prefix']
    sk_default = table_info['sk_default']
    
    if tabla == 'reservas':
        if data and 'fechaInicio' in data and 'idReserva' in data:
            return f"{pk_prefix}{data['fechaInicio']}#{data['idReserva']}", 'METADATOS'
        elif id_input and id_input.startswith('RESERVA#'):
            return id_input, 'METADATOS'
        elif id_input:
            return f"{pk_prefix}2025-01-01#{id_input}", 'METADATOS'
    
    elif tabla == 'clientes':
        if data and 'idCliente' in data:
            cliente_id = data['idCliente']
            if not cliente_id.startswith('CLIENTE#'):
                cliente_id = f"{pk_prefix}{cliente_id}"
            return cliente_id, 'PERFIL'
        elif id_input:
            if id_input.startswith('CLIENTE#'):
                return id_input, 'PERFIL'
            else:
                return f"{pk_prefix}{id_input}", 'PERFIL'
    
    elif tabla == 'limpiadores':
        if data and 'idEmpleado' in data:
            limpiador_id = data['idEmpleado']
            if not limpiador_id.startswith('LIMPIADOR#'):
                limpiador_id = f"{pk_prefix}{limpiador_id}"
            return limpiador_id, 'PERFIL'
        elif id_input:
            if id_input.startswith('LIMPIADOR#'):
                return id_input, 'PERFIL'
            else:
                return f"{pk_prefix}{id_input}", 'PERFIL'
    
    elif tabla == 'habitaciones':
        if data and 'numeroHabitacion' in data:
            return f"{pk_prefix}{data['numeroHabitacion']}", 'CONFIGURACION'
        elif id_input:
            if id_input.startswith('HABITACION#'):
                return id_input, 'CONFIGURACION'
            else:
                return f"{pk_prefix}{id_input}", 'CONFIGURACION'
    
    elif tabla == 'asignaciones':
        if data and 'fecha' in data and 'idLimpiador' in data and 'idReserva' in data:
            fecha = str(data['fecha']).split(' ')[0]
            return f"{pk_prefix}{fecha}", f"LIMPIADOR#{data['idLimpiador']}#{data['idReserva']}"
        elif id_input:
            if '#' in id_input:
                parts = id_input.split('#', 1)
                if len(parts) == 2:
                    return f"{pk_prefix}{parts[0]}", parts[1]
    
    # Por defecto
    default_id = id_input if id_input else str(uuid.uuid4())[:8]
    return f"{pk_prefix}{default_id}", sk_default

def buscar_agenda_por_id(id_input):
    """Buscar agenda específica - CORREGIDO"""
    try:
        # Primero intentar construir claves
        pk, sk = construir_claves_agenda(id_input)
        
        if pk:
            # Intentar get_item con PK y SK
            key = {'PK': pk}
            if sk:
                key['SK'] = sk
            
            print(f"Buscando agenda con key: {key}")
            response = table_limpieza.get_item(Key=key)
            
            if 'Item' in response:
                item = response['Item']
                print(f"Encontrado por get_item: {item}")
                return convertir_para_json(item)
            
            # Si no encontró, buscar todos con ese PK
            print(f"Buscando por PK: {pk}")
            response = table_limpieza.query(
                KeyConditionExpression=Key('PK').eq(pk)
            )
            items = response.get('Items', [])
            
            if len(items) > 0:
                print(f"Encontrados {len(items)} items con PK {pk}")
                # Devolver el primero
                return convertir_para_json(items[0])
        
        # Último intento: scan por cualquier campo que contenga el ID
        print(f"Último intento: scan para {id_input}")
        response = table_limpieza.scan(
            FilterExpression=Attr('PK').contains(id_input)
        )
        items = response.get('Items', [])
        
        if len(items) > 0:
            print(f"Encontrados {len(items)} items por scan")
            return convertir_para_json(items[0])
        
        print(f"No se encontró agenda con ID: {id_input}")
        return None
        
    except Exception as e:
        print(f"Error en buscar_agenda_por_id: {str(e)}")
        traceback.print_exc()
        return None

def buscar_por_id_directo(tabla, id_input):
    """Buscar un registro por ID"""
    if tabla == 'agenda':
        return buscar_agenda_por_id(id_input)
    
    table_info = TABLES[tabla]
    table = table_info['table']
    
    try:
        pk, sk = construir_claves(tabla, id_input)
        
        if pk:
            key = {table_info['pk_name']: pk}
            if sk and table_info['sk_name']:
                key[table_info['sk_name']] = sk
            
            response = table.get_item(Key=key)
            if 'Item' in response:
                return convertir_para_json(response['Item'])
        
        # Buscar por scan como fallback
        response = table.scan(
            FilterExpression=Attr(table_info['pk_name']).contains(id_input)
        )
        items = response.get('Items', [])
        if len(items) > 0:
            return convertir_para_json(items[0])
        
        return None
        
    except Exception as e:
        print(f"Error en buscar_por_id_directo para {tabla}: {str(e)}")
        return None

# ========== ENDPOINTS ESPECÍFICOS PARA AGENDA ==========

@app.route('/datos/agenda', methods=['GET'])
def listar_agenda():
    """Listar agenda específico"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        last_key = request.args.get('last_key', default=None)
        
        scan_params = {'Limit': limit}
        
        if last_key:
            try:
                scan_params['ExclusiveStartKey'] = json.loads(last_key)
            except:
                pass
        
        response = table_limpieza.scan(**scan_params)
        items = response.get('Items', [])
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        # Convertir cuidadosamente cada item
        items_serializables = []
        for item in items:
            try:
                items_serializables.append(convertir_para_json(item))
            except Exception as e:
                print(f"Error convirtiendo item: {e}")
                # Crear una versión segura del item
                safe_item = {}
                for k, v in item.items():
                    try:
                        safe_item[k] = convertir_para_json(v)
                    except:
                        safe_item[k] = str(v)
                items_serializables.append(safe_item)
        
        result = {
            "items": items_serializables,
            "count": len(items),
            "has_more": last_evaluated_key is not None
        }
        
        if last_evaluated_key:
            try:
                last_key_serializable = convertir_para_json(last_evaluated_key)
                result["last_key"] = json.dumps(last_key_serializable, cls=DecimalEncoder)
            except:
                result["last_key"] = json.dumps(str(last_evaluated_key))
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error listando agenda: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Error al listar agenda: {str(e)}"}), 500

@app.route('/datos/agenda/<id>', methods=['GET'])
def obtener_agenda(id):
    """Obtener agenda específica"""
    try:
        print(f"Obteniendo agenda con ID: {id}")
        item = buscar_agenda_por_id(id)
        
        if item:
            print(f"Agenda encontrada: {item}")
            return jsonify(item)
        else:
            print(f"Agenda no encontrada para ID: {id}")
            return jsonify({"error": "Registro de agenda no encontrado"}), 404
    
    except Exception as e:
        print(f"Error obteniendo agenda: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Error al obtener agenda: {str(e)}"}), 500

@app.route('/datos/agenda', methods=['POST'])
def crear_agenda():
    """Crear nueva agenda - CORREGIDO"""
    data = request.get_json()
    print(f"Creando agenda con datos: {json.dumps(data, indent=2, default=str)}")
    
    try:
        # Asegurar campos requeridos
        if 'fecha' not in data or not data['fecha']:
            data['fecha'] = datetime.now().strftime('%Y-%m-%d')
        
        if 'zona' not in data or not data['zona']:
            data['zona'] = 'NORTE'
        
        if 'franjaHoraria' not in data or not data['franjaHoraria']:
            data['franjaHoraria'] = '08:00-09:00'
        
        # Construir claves
        fecha = str(data['fecha']).strip()
        zona = str(data['zona']).strip()
        hora = str(data['franjaHoraria']).split('-')[0].strip()
        
        pk = f"AGENDA#{fecha}"
        sk = f"ZONA#{zona}#{hora}"
        
        data['PK'] = pk
        data['SK'] = sk
        
        # Asegurar otros campos
        if 'estado' not in data:
            data['estado'] = 'PENDIENTE'
        
        if 'progreso' not in data:
            data['progreso'] = 0
        else:
            # Convertir progreso a entero
            try:
                data['progreso'] = int(data['progreso'])
            except:
                data['progreso'] = 0
        
        # Convertir números a int (no Decimal)
        for key in ['habitacionesEstimadasPorHora', 'progreso']:
            if key in data and isinstance(data[key], (int, float, Decimal, str)):
                try:
                    data[key] = int(float(data[key]))
                except:
                    data[key] = 0
        
        # Convertir listas a sets si es necesario
        list_fields = ['limpiadoresAsignados', 'habitacionesPrioritarias', 'habitationsAsignadas']
        for field in list_fields:
            if field in data and isinstance(data[field], list):
                data[field] = set(data[field])
        
        print(f"Datos preparados para DynamoDB: {data}")
        
        # Insertar en DynamoDB
        table_limpieza.put_item(Item=data)
        
        response_id = f"{pk}#{sk}"  # ID completo para referencia
        
        return jsonify({
            "message": "Agenda creada exitosamente",
            "id": response_id,
            "data": convertir_para_json(data)
        }), 201
    
    except Exception as e:
        print(f"Error creando agenda: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Error al crear agenda: {str(e)}"}), 500

@app.route('/datos/agenda/<id>', methods=['PUT'])
def actualizar_agenda(id):
    """Actualizar agenda existente - CORREGIDO"""
    data = request.get_json()
    print(f"Actualizando agenda ID: {id}")
    print(f"Datos recibidos: {json.dumps(data, indent=2, default=str)}")
    
    try:
        # Buscar agenda existente
        existing_item = buscar_agenda_por_id(id)
        
        if not existing_item:
            return jsonify({"error": "Registro de agenda no encontrado"}), 404
        
        print(f"Agenda existente encontrada: {existing_item}")
        
        # Preservar las claves originales (IMPORTANTE)
        pk = existing_item.get('PK')
        sk = existing_item.get('SK')
        
        if not pk or not sk:
            return jsonify({"error": "No se pudieron encontrar las claves de la agenda"}), 400
        
        # Actualizar solo los campos que vienen en data (excepto PK/SK)
        for key, value in data.items():
            if key not in ['PK', 'SK']:
                existing_item[key] = value
        
        # Asegurar que las claves se mantengan
        existing_item['PK'] = pk
        existing_item['SK'] = sk
        
        # Preparar datos para DynamoDB
        # Convertir números a int
        if 'progreso' in existing_item:
            try:
                existing_item['progreso'] = int(float(existing_item['progreso']))
            except:
                existing_item['progreso'] = 0
        
        if 'habitacionesEstimadasPorHora' in existing_item:
            try:
                existing_item['habitacionesEstimadasPorHora'] = int(float(existing_item['habitacionesEstimadasPorHora']))
            except:
                existing_item['habitacionesEstimadasPorHora'] = 1
        
        # Convertir listas a sets
        list_fields = ['limpiadoresAsignados', 'habitacionesPrioritarias', 'habitationsAsignadas']
        for field in list_fields:
            if field in existing_item and isinstance(existing_item[field], list):
                existing_item[field] = set(existing_item[field])
        
        print(f"Datos finales para actualizar: {existing_item}")
        
        # Actualizar en DynamoDB
        table_limpieza.put_item(Item=existing_item)
        
        return jsonify({
            "message": "Agenda actualizada exitosamente",
            "id": id
        })
    
    except Exception as e:
        print(f"Error actualizando agenda: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Error al actualizar agenda: {str(e)}"}), 500

@app.route('/datos/agenda/<id>', methods=['DELETE'])
def eliminar_agenda(id):
    """Eliminar agenda - CORREGIDO"""
    print(f"Eliminando agenda con ID: {id}")
    
    try:
        # Buscar agenda existente
        existing_item = buscar_agenda_por_id(id)
        
        if not existing_item:
            return jsonify({"error": "Registro de agenda no encontrado"}), 404
        
        print(f"Agenda encontrada para eliminar: {existing_item}")
        
        # Obtener claves
        pk = existing_item.get('PK')
        sk = existing_item.get('SK')
        
        if not pk or not sk:
            return jsonify({"error": "No se pudieron encontrar las claves de la agenda"}), 400
        
        print(f"Eliminando con PK: {pk}, SK: {sk}")
        
        # Eliminar de DynamoDB
        table_limpieza.delete_item(Key={'PK': pk, 'SK': sk})
        
        return jsonify({
            "message": "Agenda eliminada exitosamente",
            "id": id
        })
    
    except Exception as e:
        print(f"Error eliminando agenda: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Error al eliminar agenda: {str(e)}"}), 500

# ========== ENDPOINTS GENERALES (mantener para otras tablas) ==========

@app.route('/datos/<tabla>', methods=['GET'])
def listar_datos(tabla):
    """Listar datos de cualquier tabla excepto agenda"""
    if tabla == 'agenda':
        return listar_agenda()
    
    if tabla not in TABLES:
        return jsonify({"error": "Tabla no encontrada"}), 404
    
    table_info = TABLES[tabla]
    table = table_info['table']
    
    try:
        limit = request.args.get('limit', default=50, type=int)
        last_key = request.args.get('last_key', default=None)
        
        scan_params = {'Limit': limit}
        
        if last_key:
            try:
                scan_params['ExclusiveStartKey'] = json.loads(last_key)
            except:
                pass
        
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
        print(f"Error listando datos de {tabla}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/datos/<tabla>/<id>', methods=['GET'])
def obtener_dato(tabla, id):
    """Obtener dato de cualquier tabla"""
    if tabla == 'agenda':
        return obtener_agenda(id)
    
    if tabla not in TABLES:
        return jsonify({"error": "Tabla no encontrada"}), 404
    
    try:
        item = buscar_por_id_directo(tabla, id)
        
        if item:
            return jsonify(item)
        else:
            return jsonify({"error": "Registro no encontrado"}), 404
    
    except Exception as e:
        print(f"Error obteniendo dato de {tabla}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/datos/<tabla>', methods=['POST'])
def crear_dato(tabla):
    """Crear dato en cualquier tabla"""
    if tabla == 'agenda':
        return crear_agenda()
    
    if tabla not in TABLES:
        return jsonify({"error": "Tabla no encontrada"}), 404
    
    table_info = TABLES[tabla]
    table = table_info['table']
    data = request.get_json()
    
    try:
        # Lógica específica para cada tabla
        if tabla == 'reservas':
            if 'idReserva' not in data:
                data['idReserva'] = f"R{str(uuid.uuid4())[:8].upper()}"
            if 'fechaInicio' not in data:
                data['fechaInicio'] = '2025-01-01'
        
        elif tabla == 'clientes':
            if 'idCliente' not in data:
                data['idCliente'] = f"C{str(uuid.uuid4())[:8].upper()}"
        
        elif tabla == 'limpiadores':
            if 'idEmpleado' not in data:
                data['idEmpleado'] = f"L{str(uuid.uuid4())[:8].upper()}"
        
        # Construir claves
        pk, sk = construir_claves(tabla, None, data)
        data['PK'] = pk
        if sk:
            data['SK'] = sk
        
        # Convertir para DynamoDB
        for key, value in data.items():
            if isinstance(value, (int, float)):
                data[key] = Decimal(str(value))
            elif isinstance(value, list) and key not in ['PK', 'SK']:
                if all(isinstance(x, str) for x in value):
                    data[key] = set(value)
        
        # Insertar
        table.put_item(Item=data)
        
        # Obtener ID para respuesta
        response_id = None
        if tabla == 'reservas':
            response_id = data.get('idReserva')
        elif tabla == 'clientes':
            response_id = data.get('idCliente')
        elif tabla == 'limpiadores':
            response_id = data.get('idEmpleado')
        elif tabla == 'habitaciones':
            response_id = data.get('numeroHabitacion')
        
        return jsonify({
            "message": f"Registro creado en {tabla}",
            "id": response_id,
            "data": convertir_para_json(data)
        }), 201
    
    except Exception as e:
        print(f"Error creando en {tabla}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/datos/<tabla>/<id>', methods=['PUT'])
def actualizar_dato(tabla, id):
    """Actualizar dato en cualquier tabla"""
    if tabla == 'agenda':
        return actualizar_agenda(id)
    
    if tabla not in TABLES:
        return jsonify({"error": "Tabla no encontrada"}), 404
    
    table_info = TABLES[tabla]
    table = table_info['table']
    data = request.get_json()
    
    try:
        existing_item = buscar_por_id_directo(tabla, id)
        
        if not existing_item:
            return jsonify({"error": "Registro no encontrado"}), 404
        
        # Preservar claves
        pk = existing_item.get('PK')
        sk = existing_item.get('SK')
        
        for key, value in data.items():
            if key not in ['PK', 'SK']:
                existing_item[key] = value
        
        existing_item['PK'] = pk
        if sk:
            existing_item['SK'] = sk
        
        # Convertir para DynamoDB
        for key, value in existing_item.items():
            if isinstance(value, (int, float)):
                existing_item[key] = Decimal(str(value))
        
        table.put_item(Item=existing_item)
        
        return jsonify({
            "message": "Actualizado exitosamente",
            "id": id
        })
    
    except Exception as e:
        print(f"Error actualizando {tabla}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/datos/<tabla>/<id>', methods=['DELETE'])
def eliminar_dato(tabla, id):
    """Eliminar dato de cualquier tabla"""
    if tabla == 'agenda':
        return eliminar_agenda(id)
    
    if tabla not in TABLES:
        return jsonify({"error": "Tabla no encontrada"}), 404
    
    table_info = TABLES[tabla]
    table = table_info['table']
    
    try:
        existing_item = buscar_por_id_directo(tabla, id)
        
        if not existing_item:
            return jsonify({"error": "Registro no encontrado"}), 404
        
        pk = existing_item.get('PK')
        sk = existing_item.get('SK')
        
        key = {table_info['pk_name']: pk}
        if sk and table_info['sk_name']:
            key[table_info['sk_name']] = sk
        
        table.delete_item(Key=key)
        
        return jsonify({
            "message": "Eliminado exitosamente",
            "id": id
        })
    
    except Exception as e:
        print(f"Error eliminando de {tabla}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== ENDPOINTS PARA DEBUG ==========

@app.route('/debug/agenda', methods=['GET'])
def debug_agenda():
    """Debug específico para agenda"""
    try:
        response = table_limpieza.scan(Limit=5)
        items = response.get('Items', [])
        
        sample_data = []
        for item in items:
            safe_item = {}
            for k, v in item.items():
                try:
                    safe_item[k] = convertir_para_json(v)
                except:
                    safe_item[k] = str(v)
            sample_data.append(safe_item)
        
        return jsonify({
            "table_name": "AgendaLimpieza",
            "count": len(items),
            "sample_data": sample_data
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test/agenda/<accion>', methods=['GET'])
def test_agenda(accion):
    """Endpoint de prueba para agenda"""
    if accion == 'listar':
        return listar_agenda()
    elif accion == 'crear':
        test_data = {
            "fecha": "2025-01-25",
            "zona": "NORTE",
            "franjaHoraria": "14:00-15:00",
            "habitacionesEstimadasPorHora": 3,
            "habitacionesPrioritarias": ["101", "102"],
            "habitationsAsignadas": ["101", "102", "103"],
            "limpiadoresAsignados": ["L001", "L002"],
            "estado": "PENDIENTE",
            "progreso": 0,
            "notas": "Prueba creación agenda"
        }
        return crear_agenda(test_data)
    
    return jsonify({"error": "Acción no válida"}), 400

# Mantener los otros endpoints (buscar_reserva, reporte_complejo, etc.)

@app.route('/buscar_reserva', methods=['POST'])
def buscar_reserva():
    data = request.get_json()
    reserva_id = data.get("id")

    try:
        response = table_reservas.scan(
            FilterExpression=Attr("idReserva").eq(reserva_id)
        )

        items = response.get('Items', [])
        
        if len(items) > 0:
            return jsonify({
                "found": True, 
                "data": convertir_para_json(items[0])
            })
        else:
            return jsonify({"found": False})
    
    except Exception as e:
        print(f"Error buscando reserva: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/reporte_complejo', methods=['GET'])
def reporte_complejo():
    # Mantener la misma implementación anterior
    pass

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')