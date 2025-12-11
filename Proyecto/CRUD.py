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
    """Generar reporte complejo con datos de múltiples tablas"""
    try:
        # Obtener parámetros opcionales
        fecha_inicio = request.args.get('fecha_inicio', default=None)
        fecha_fin = request.args.get('fecha_fin', default=None)
        tipo_reporte = request.args.get('tipo', default='general')
        zona = request.args.get('zona', default=None)
        
        # Fechas por defecto (últimos 7 días)
        if not fecha_inicio:
            fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not fecha_fin:
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
        
        print(f"Generando reporte: tipo={tipo_reporte}, fecha_inicio={fecha_inicio}, fecha_fin={fecha_fin}")
        
        # Dependiendo del tipo de reporte, generar diferentes estructuras
        if tipo_reporte == 'limpieza':
            return reporte_limpieza(fecha_inicio, fecha_fin, zona)
        elif tipo_reporte == 'reservas':
            return reporte_reservas(fecha_inicio, fecha_fin)
        elif tipo_reporte == 'personal':
            return reporte_personal(fecha_inicio, fecha_fin)
        else:
            # Reporte general
            return reporte_general(fecha_inicio, fecha_fin)
    
    except Exception as e:
        print(f"Error generando reporte complejo: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Error al generar reporte: {str(e)}"}), 500

def reporte_general(fecha_inicio, fecha_fin):
    """Reporte general con estadísticas de todas las áreas"""
    try:
        # Obtener datos de reservas en el rango de fechas
        reservas = obtener_reservas_por_fecha(fecha_inicio, fecha_fin)
        
        # Obtener datos de limpieza
        agendas = obtener_agendas_por_fecha(fecha_inicio, fecha_fin)
        
        # Obtener datos de personal
        limpiadores = obtener_limpiadores_activos()
        
        # Obtener datos de habitaciones
        habitaciones = obtener_habitaciones()
        
        # Calcular estadísticas
        estadisticas = {
            'reservas': {
                'total': len(reservas),
                'confirmadas': len([r for r in reservas if r.get('estado') == 'CONFIRMADA']),
                'pendientes': len([r for r in reservas if r.get('estado') == 'PENDIENTE']),
                'canceladas': len([r for r in reservas if r.get('estado') == 'CANCELADA']),
                'ingresos_estimados': sum(float(r.get('precioTotal', 0)) for r in reservas)
            },
            'limpieza': {
                'tareas_totales': len(agendas),
                'tareas_completadas': len([a for a in agendas if a.get('estado') == 'COMPLETADO']),
                'tareas_pendientes': len([a for a in agendas if a.get('estado') == 'PENDIENTE']),
                'tareas_en_progreso': len([a for a in agendas if a.get('estado') == 'EN_PROGRESO']),
                'progreso_promedio': calcular_promedio([a.get('progreso', 0) for a in agendas])
            },
            'personal': {
                'total_limpiadores': len(limpiadores),
                'limpiadores_activos': len([l for l in limpiadores if l.get('estado') == 'ACTIVO']),
                'limpiadores_inactivos': len([l for l in limpiadores if l.get('estado') == 'INACTIVO']),
                'horas_totales_trabajadas': calcular_horas_trabajadas(agendas, limpiadores)
            },
            'habitaciones': {
                'total': len(habitaciones),
                'disponibles': len([h for h in habitaciones if h.get('estado') == 'DISPONIBLE']),
                'ocupadas': len([h for h in habitaciones if h.get('estado') == 'OCUPADA']),
                'en_limpieza': len([h for h in habitaciones if h.get('estado') == 'EN_LIMPIEZA']),
                'mantenimiento': len([h for h in habitaciones if h.get('estado') == 'MANTENIMIENTO'])
            },
            'fechas': {
                'inicio': fecha_inicio,
                'fin': fecha_fin,
                'generado': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        # Datos detallados para gráficos
        detalle_diario = obtener_detalle_diario(fecha_inicio, fecha_fin)
        
        return jsonify({
            'estadisticas': estadisticas,
            'detalle_diario': detalle_diario,
            'resumen': generar_resumen_textual(estadisticas)
        })
    
    except Exception as e:
        print(f"Error en reporte general: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Error generando reporte general: {str(e)}"}), 500

def reporte_limpieza(fecha_inicio, fecha_fin, zona=None):
    """Reporte específico de limpieza"""
    try:
        # Obtener agendas por fecha y zona
        agendas = obtener_agendas_por_fecha(fecha_inicio, fecha_fin, zona)
        
        # Agrupar por zona y franja horaria
        agrupado_por_zona = {}
        for agenda in agendas:
            zona_agenda = agenda.get('zona', 'SIN_ZONA')
            if zona_agenda not in agrupado_por_zona:
                agrupado_por_zona[zona_agenda] = {
                    'total_tareas': 0,
                    'completadas': 0,
                    'pendientes': 0,
                    'en_progreso': 0,
                    'habitaciones_total': 0,
                    'habitaciones_completadas': 0,
                    'limpiadores_asignados': set(),
                    'franjas_horarias': {}
                }
            
            stats = agrupado_por_zona[zona_agenda]
            stats['total_tareas'] += 1
            
            estado = agenda.get('estado', 'PENDIENTE')
            if estado == 'COMPLETADO':
                stats['completadas'] += 1
            elif estado == 'EN_PROGRESO':
                stats['en_progreso'] += 1
            else:
                stats['pendientes'] += 1
            
            # Habitaciones
            habitaciones_asignadas = agenda.get('habitationsAsignadas', [])
            if isinstance(habitaciones_asignadas, set):
                habitaciones_asignadas = list(habitaciones_asignadas)
            
            stats['habitaciones_total'] += len(habitaciones_asignadas)
            
            # Limpiadores
            limpiadores = agenda.get('limpiadoresAsignados', [])
            if isinstance(limpiadores, set):
                limpiadores = list(limpiadores)
            
            stats['limpiadores_asignados'].update(limpiadores)
            
            # Franja horaria
            franja = agenda.get('franjaHoraria', 'SIN_FRANJA')
            if franja not in stats['franjas_horarias']:
                stats['franjas_horarias'][franja] = 0
            stats['franjas_horarias'][franja] += 1
        
        # Convertir sets a listas para JSON
        for zona_stats in agrupado_por_zona.values():
            zona_stats['limpiadores_asignados'] = list(zona_stats['limpiadores_asignados'])
        
        # Calcular eficiencia
        eficiencia_por_zona = {}
        for zona, stats in agrupado_por_zona.items():
            if stats['habitaciones_total'] > 0:
                eficiencia = (stats['habitaciones_completadas'] / stats['habitaciones_total']) * 100
            else:
                eficiencia = 0
            
            eficiencia_por_zona[zona] = {
                'eficiencia': round(eficiencia, 2),
                'tareas_por_limpiador': stats['total_tareas'] / max(len(stats['limpiadores_asignados']), 1),
                'habitaciones_por_hora': calcular_habitaciones_por_hora(zona, agendas)
            }
        
        return jsonify({
            'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
            'zona_filtrada': zona,
            'resumen_por_zona': agrupado_por_zona,
            'eficiencia': eficiencia_por_zona,
            'total_general': {
                'tareas': sum(s['total_tareas'] for s in agrupado_por_zona.values()),
                'completadas': sum(s['completadas'] for s in agrupado_por_zona.values()),
                'pendientes': sum(s['pendientes'] for s in agrupado_por_zona.values()),
                'habitaciones': sum(s['habitaciones_total'] for s in agrupado_por_zona.values())
            },
            'recomendaciones': generar_recomendaciones_limpieza(agrupado_por_zona)
        })
    
    except Exception as e:
        print(f"Error en reporte limpieza: {str(e)}")
        return jsonify({"error": f"Error generando reporte limpieza: {str(e)}"}), 500

def reporte_reservas(fecha_inicio, fecha_fin):
    """Reporte específico de reservas"""
    try:
        reservas = obtener_reservas_por_fecha(fecha_inicio, fecha_fin)
        
        # Agrupar por estado y tipo
        agrupado_por_estado = {}
        agrupado_por_tipo_habitacion = {}
        ingresos_por_dia = {}
        
        for reserva in reservas:
            estado = reserva.get('estado', 'SIN_ESTADO')
            tipo_habitacion = reserva.get('tipoHabitacion', 'SIN_TIPO')
            fecha = reserva.get('fechaInicio', 'SIN_FECHA')
            precio = float(reserva.get('precioTotal', 0))
            
            # Por estado
            if estado not in agrupado_por_estado:
                agrupado_por_estado[estado] = {'cantidad': 0, 'ingresos': 0}
            agrupado_por_estado[estado]['cantidad'] += 1
            agrupado_por_estado[estado]['ingresos'] += precio
            
            # Por tipo de habitación
            if tipo_habitacion not in agrupado_por_tipo_habitacion:
                agrupado_por_tipo_habitacion[tipo_habitacion] = {'cantidad': 0, 'ingresos': 0}
            agrupado_por_tipo_habitacion[tipo_habitacion]['cantidad'] += 1
            agrupado_por_tipo_habitacion[tipo_habitacion]['ingresos'] += precio
            
            # Ingresos por día
            if fecha not in ingresos_por_dia:
                ingresos_por_dia[fecha] = 0
            ingresos_por_dia[fecha] += precio
        
        # Calcular ocupación
        habitaciones_totales = len(obtener_habitaciones())
        dias_periodo = (datetime.strptime(fecha_fin, '%Y-%m-%d') - datetime.strptime(fecha_inicio, '%Y-%m-%d')).days + 1
        capacidad_total = habitaciones_totales * dias_periodo
        noches_reservadas = sum(len(r.get('noches', [])) for r in reservas)
        
        ocupacion = (noches_reservadas / capacidad_total * 100) if capacidad_total > 0 else 0
        
        return jsonify({
            'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
            'resumen': {
                'total_reservas': len(reservas),
                'ingresos_totales': sum(float(r.get('precioTotal', 0)) for r in reservas),
                'ocupacion_promedio': round(ocupacion, 2),
                'duracion_promedio': calcular_duracion_promedio(reservas),
                'tasa_cancelacion': calcular_tasa_cancelacion(reservas)
            },
            'por_estado': agrupado_por_estado,
            'por_tipo_habitacion': agrupado_por_tipo_habitacion,
            'ingresos_diarios': ingresos_por_dia,
            'tendencias': analizar_tendencias_reservas(reservas)
        })
    
    except Exception as e:
        print(f"Error en reporte reservas: {str(e)}")
        return jsonify({"error": f"Error generando reporte reservas: {str(e)}"}), 500

def reporte_personal(fecha_inicio, fecha_fin):
    """Reporte específico de personal"""
    try:
        limpiadores = obtener_limpiadores_activos()
        agendas = obtener_agendas_por_fecha(fecha_inicio, fecha_fin)
        
        desempeno_limpiadores = []
        
        for limpiador in limpiadores:
            id_limpiador = limpiador.get('idEmpleado')
            
            # Filtrar agendas asignadas a este limpiador
            agendas_limpiador = []
            for agenda in agendas:
                limpiadores_asignados = agenda.get('limpiadoresAsignados', [])
                if isinstance(limpiadores_asignados, set):
                    limpiadores_asignados = list(limpiadores_asignados)
                
                if id_limpiador in limpiadores_asignados:
                    agendas_limpiador.append(agenda)
            
            # Calcular métricas
            tareas_completadas = len([a for a in agendas_limpiador if a.get('estado') == 'COMPLETADO'])
            tareas_asignadas = len(agendas_limpiador)
            
            habitaciones_completadas = sum(len(a.get('habitationsAsignadas', [])) 
                                         for a in agendas_limpiador if a.get('estado') == 'COMPLETADO')
            
            eficiencia = (tareas_completadas / tareas_asignadas * 100) if tareas_asignadas > 0 else 0
            
            desempeno_limpiadores.append({
                'id': id_limpiador,
                'nombre': limpiador.get('nombre', 'Sin nombre'),
                'estado': limpiador.get('estado', 'INACTIVO'),
                'tareas_asignadas': tareas_asignadas,
                'tareas_completadas': tareas_completadas,
                'habitaciones_completadas': habitaciones_completadas,
                'eficiencia': round(eficiencia, 2),
                'horas_trabajadas': calcular_horas_trabajadas_limpiador(id_limpiador, agendas)
            })
        
        # Ordenar por eficiencia
        desempeno_limpiadores.sort(key=lambda x: x['eficiencia'], reverse=True)
        
        return jsonify({
            'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
            'total_personal': len(limpiadores),
            'activos': len([l for l in limpiadores if l.get('estado') == 'ACTIVO']),
            'inactivos': len([l for l in limpiadores if l.get('estado') == 'INACTIVO']),
            'desempeno_individual': desempeno_limpiadores,
            'promedios': {
                'eficiencia_promedio': calcular_promedio([d['eficiencia'] for d in desempeno_limpiadores]),
                'tareas_promedio': calcular_promedio([d['tareas_asignadas'] for d in desempeno_limpiadores]),
                'horas_promedio': calcular_promedio([d.get('horas_trabajadas', 0) for d in desempeno_limpiadores])
            },
            'recomendaciones_personal': generar_recomendaciones_personal(desempeno_limpiadores)
        })
    
    except Exception as e:
        print(f"Error en reporte personal: {str(e)}")
        return jsonify({"error": f"Error generando reporte personal: {str(e)}"}), 500

# ========== FUNCIONES AUXILIARES ==========

# ========== FUNCIONES AUXILIARES CORREGIDAS ==========

def obtener_reservas_por_fecha(fecha_inicio, fecha_fin):
    """Obtener reservas en un rango de fechas - CORREGIDO"""
    try:
        # NOTA: En DynamoDB necesitamos un diseño específico para queries por fecha
        # Asumiendo que las reservas tienen PK con formato: RESERVA#fecha#idReserva
        
        print(f"Buscando reservas entre {fecha_inicio} y {fecha_fin}")
        
        # Escanear todas las reservas con prefijo común
        response = table_reservas.scan(
            FilterExpression=Attr('PK').begins_with('RESERVA#')
        )
        reservas = response.get('Items', [])
        
        reservas_filtradas = []
        for reserva in reservas:
            # Extraer fecha de la PK
            pk = reserva.get('PK', '')
            if pk.startswith('RESERVA#'):
                # Formato: RESERVA#2024-01-15#R12345
                parts = pk.split('#')
                if len(parts) >= 2:
                    fecha_reserva = parts[1]  # La fecha está después del primer #
                    
                    # También intentar obtener fecha del campo fechaInicio
                    if 'fechaInicio' in reserva:
                        fecha_reserva = reserva['fechaInicio']
                    
                    # Verificar si está en el rango
                    try:
                        if fecha_inicio <= fecha_reserva <= fecha_fin:
                            reservas_filtradas.append(convertir_para_json(reserva))
                    except:
                        # Si hay error en la comparación, omitir
                        pass
        
        print(f"Encontradas {len(reservas_filtradas)} reservas en el rango")
        return reservas_filtradas
    except Exception as e:
        print(f"Error obteniendo reservas: {str(e)}")
        traceback.print_exc()
        return []

def obtener_agendas_por_fecha(fecha_inicio, fecha_fin, zona=None):
    """Obtener agendas en un rango de fechas - CORREGIDO"""
    try:
        print(f"Buscando agendas entre {fecha_inicio} y {fecha_fin}")
        
        # Usar query en lugar de scan para mejor rendimiento
        # Asumiendo que las agendas tienen PK: AGENDA#fecha
        
        agendas_filtradas = []
        
        # Convertir fechas a datetime para iterar
        inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        current_dt = inicio_dt
        while current_dt <= fin_dt:
            fecha_str = current_dt.strftime('%Y-%m-%d')
            pk = f"AGENDA#{fecha_str}"
            
            # Query por PK específica
            try:
                response = table_limpieza.query(
                    KeyConditionExpression=Key('PK').eq(pk)
                )
                items = response.get('Items', [])
                
                for item in items:
                    agenda_json = convertir_para_json(item)
                    
                    # Filtrar por zona si se especifica
                    if zona:
                        if agenda_json.get('zona') == zona:
                            agendas_filtradas.append(agenda_json)
                    else:
                        agendas_filtradas.append(agenda_json)
                
            except Exception as query_error:
                print(f"Error querying agenda para fecha {fecha_str}: {query_error}")
            
            current_dt += timedelta(days=1)
        
        print(f"Encontradas {len(agendas_filtradas)} agendas en el rango")
        return agendas_filtradas
        
    except Exception as e:
        print(f"Error obteniendo agendas: {str(e)}")
        traceback.print_exc()
        return []

def obtener_limpiadores_activos():
    """Obtener todos los limpiadores - CORREGIDO"""
    try:
        response = table_limpiadores.scan(
            FilterExpression=Attr('PK').begins_with('LIMPIADOR#')
        )
        limpiadores = response.get('Items', [])
        print(f"Encontrados {len(limpiadores)} limpiadores")
        return [convertir_para_json(l) for l in limpiadores]
    except Exception as e:
        print(f"Error obteniendo limpiadores: {str(e)}")
        traceback.print_exc()
        return []

def obtener_habitaciones():
    """Obtener todas las habitaciones - CORREGIDO"""
    try:
        response = table_habitacion.scan(
            FilterExpression=Attr('PK').begins_with('HABITACION#')
        )
        habitaciones = response.get('Items', [])
        print(f"Encontradas {len(habitaciones)} habitaciones")
        return [convertir_para_json(h) for h in habitaciones]
    except Exception as e:
        print(f"Error obteniendo habitaciones: {str(e)}")
        traceback.print_exc()
        return []

def extract_fecha_from_pk(pk):
    """Extraer fecha de una PK de agenda - MEJORADA"""
    if pk.startswith('AGENDA#'):
        parts = pk.split('#')
        if len(parts) > 1:
            fecha = parts[1]
            # Validar formato de fecha
            try:
                datetime.strptime(fecha, '%Y-%m-%d')
                return fecha
            except ValueError:
                # Intentar otros formatos
                for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%Y/%m/%d']:
                    try:
                        datetime.strptime(fecha, fmt)
                        return fecha
                    except:
                        continue
    return None

# ========== CORRECCIONES EN LAS FUNCIONES DE REPORTE ==========

def reporte_limpieza(fecha_inicio, fecha_fin, zona=None):
    """Reporte específico de limpieza - CORREGIDO"""
    try:
        # Obtener agendas por fecha y zona
        agendas = obtener_agendas_por_fecha(fecha_inicio, fecha_fin, zona)
        
        print(f"Agendas obtenidas para reporte: {len(agendas)}")
        
        if len(agendas) == 0:
            return jsonify({
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'zona_filtrada': zona,
                'mensaje': 'No se encontraron datos de limpieza en el período especificado',
                'resumen_por_zona': {},
                'total_general': {
                    'tareas': 0,
                    'completadas': 0,
                    'pendientes': 0,
                    'habitaciones': 0
                }
            })
        
        # Agrupar por zona y franja horaria
        agrupado_por_zona = {}
        for agenda in agendas:
            zona_agenda = agenda.get('zona', 'SIN_ZONA')
            if zona_agenda not in agrupado_por_zona:
                agrupado_por_zona[zona_agenda] = {
                    'total_tareas': 0,
                    'completadas': 0,
                    'pendientes': 0,
                    'en_progreso': 0,
                    'habitaciones_total': 0,
                    'habitaciones_completadas': 0,
                    'limpiadores_asignados': set(),
                    'franjas_horarias': {}
                }
            
            stats = agrupado_por_zona[zona_agenda]
            stats['total_tareas'] += 1
            
            estado = agenda.get('estado', 'PENDIENTE')
            if estado == 'COMPLETADO':
                stats['completadas'] += 1
                # Si está completado, contar habitaciones como completadas
                habitaciones_asignadas = agenda.get('habitationsAsignadas', [])
                if isinstance(habitaciones_asignadas, set):
                    habitaciones_asignadas = list(habitaciones_asignadas)
                stats['habitaciones_completadas'] += len(habitaciones_asignadas)
            elif estado == 'EN_PROGRESO':
                stats['en_progreso'] += 1
            else:
                stats['pendientes'] += 1
            
            # Habitaciones
            habitaciones_asignadas = agenda.get('habitationsAsignadas', [])
            if isinstance(habitaciones_asignadas, set):
                habitaciones_asignadas = list(habitaciones_asignadas)
            elif not isinstance(habitaciones_asignadas, list):
                habitaciones_asignadas = []
            
            stats['habitaciones_total'] += len(habitaciones_asignadas)
            
            # Limpiadores
            limpiadores = agenda.get('limpiadoresAsignados', [])
            if isinstance(limpiadores, set):
                limpiadores = list(limpiadores)
            elif not isinstance(limpiadores, list):
                limpiadores = []
            
            stats['limpiadores_asignados'].update(limpiadores)
            
            # Franja horaria
            franja = agenda.get('franjaHoraria', 'SIN_FRANJA')
            if franja not in stats['franjas_horarias']:
                stats['franjas_horarias'][franja] = 0
            stats['franjas_horarias'][franja] += 1
        
        # Convertir sets a listas para JSON
        for zona_stats in agrupado_por_zona.values():
            zona_stats['limpiadores_asignados'] = list(zona_stats['limpiadores_asignados'])
        
        # Calcular eficiencia
        eficiencia_por_zona = {}
        for zona, stats in agrupado_por_zona.items():
            if stats['habitaciones_total'] > 0:
                eficiencia = (stats['habitaciones_completadas'] / stats['habitaciones_total']) * 100
            else:
                eficiencia = 0
            
            eficiencia_por_zona[zona] = {
                'eficiencia': round(eficiencia, 2),
                'tareas_por_limpiador': round(stats['total_tareas'] / max(len(stats['limpiadores_asignados']), 1), 2),
                'habitaciones_por_hora': calcular_habitaciones_por_hora(zona, agendas)
            }
        
        return jsonify({
            'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
            'zona_filtrada': zona,
            'resumen_por_zona': agrupado_por_zona,
            'eficiencia': eficiencia_por_zona,
            'total_general': {
                'tareas': sum(s['total_tareas'] for s in agrupado_por_zona.values()),
                'completadas': sum(s['completadas'] for s in agrupado_por_zona.values()),
                'pendientes': sum(s['pendientes'] for s in agrupado_por_zona.values()),
                'habitaciones': sum(s['habitaciones_total'] for s in agrupado_por_zona.values())
            },
            'recomendaciones': generar_recomendaciones_limpieza(agrupado_por_zona)
        })
    
    except Exception as e:
        print(f"Error en reporte limpieza: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Error generando reporte limpieza: {str(e)}"}), 500

def reporte_reservas(fecha_inicio, fecha_fin):
    """Reporte específico de reservas"""
    try:
        reservas = obtener_reservas_por_fecha(fecha_inicio, fecha_fin)
        
        print(f"Reservas obtenidas para reporte: {len(reservas)}")
        
        if len(reservas) == 0:
            return jsonify({
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'mensaje': 'No se encontraron reservas en el período especificado',
                'resumen': {
                    'total_reservas': 0,
                    'ingresos_totales': 0,
                    'ocupacion_promedio': 0,
                    'duracion_promedio': 0,
                    'tasa_cancelacion': 0
                }
            })
        
        # Agrupar por estado y tipo
        agrupado_por_estado = {}
        agrupado_por_tipo_habitacion = {}
        ingresos_por_dia = {}
        noches_totales = 0
        
        for reserva in reservas:
            estado = reserva.get('estado', 'SIN_ESTADO')
            tipo_habitacion = reserva.get('tipoHabitacion', 'SIN_TIPO')
            fecha = reserva.get('fechaInicio', 'SIN_FECHA')
            
            # Convertir precio a float de forma segura
            precio = 0
            try:
                precio_str = str(reserva.get('precioTotal', 0))
                precio = float(precio_str.replace(',', '.')) if precio_str else 0
            except:
                precio = 0
            
            # Calcular noches
            try:
                fecha_inicio_res = reserva.get('fechaInicio', fecha_inicio)
                fecha_fin_res = reserva.get('fechaFin', fecha_inicio)
                
                if fecha_inicio_res and fecha_fin_res:
                    inicio = datetime.strptime(fecha_inicio_res, '%Y-%m-%d')
                    fin = datetime.strptime(fecha_fin_res, '%Y-%m-%d')
                    noches = (fin - inicio).days
                    if noches <= 0:
                        noches = 1
                    noches_totales += noches
            except:
                noches_totales += 1
            
            # Por estado
            if estado not in agrupado_por_estado:
                agrupado_por_estado[estado] = {'cantidad': 0, 'ingresos': 0}
            agrupado_por_estado[estado]['cantidad'] += 1
            agrupado_por_estado[estado]['ingresos'] += precio
            
            # Por tipo de habitación
            if tipo_habitacion not in agrupado_por_tipo_habitacion:
                agrupado_por_tipo_habitacion[tipo_habitacion] = {'cantidad': 0, 'ingresos': 0}
            agrupado_por_tipo_habitacion[tipo_habitacion]['cantidad'] += 1
            agrupado_por_tipo_habitacion[tipo_habitacion]['ingresos'] += precio
            
            # Ingresos por día
            if fecha not in ingresos_por_dia:
                ingresos_por_dia[fecha] = 0
            ingresos_por_dia[fecha] += precio
        
        # Calcular ocupación
        habitaciones_totales = len(obtener_habitaciones())
        dias_periodo = (datetime.strptime(fecha_fin, '%Y-%m-%d') - datetime.strptime(fecha_inicio, '%Y-%m-%d')).days + 1
        capacidad_total = habitaciones_totales * dias_periodo
        
        ocupacion = (noches_totales / capacidad_total * 100) if capacidad_total > 0 else 0
        
        ingresos_totales = sum(float(r.get('precioTotal', 0)) for r in reservas)
        
        return jsonify({
            'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
            'resumen': {
                'total_reservas': len(reservas),
                'ingresos_totales': round(ingresos_totales, 2),
                'ocupacion_promedio': round(ocupacion, 2),
                'duracion_promedio': round(calcular_duracion_promedio(reservas), 2),
                'tasa_cancelacion': round(calcular_tasa_cancelacion(reservas), 2)
            },
            'por_estado': agrupado_por_estado,
            'por_tipo_habitacion': agrupado_por_tipo_habitacion,
            'ingresos_diarios': ingresos_por_dia,
            'tendencias': analizar_tendencias_reservas(reservas)
        })
    
    except Exception as e:
        print(f"Error en reporte reservas: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Error generando reporte reservas: {str(e)}"}), 500

def reporte_personal(fecha_inicio, fecha_fin):
    """Reporte específico de personal - CORREGIDO"""
    try:
        limpiadores = obtener_limpiadores_activos()
        agendas = obtener_agendas_por_fecha(fecha_inicio, fecha_fin)
        
        print(f"Limpiadores: {len(limpiadores)}, Agendas: {len(agendas)}")
        
        if len(limpiadores) == 0:
            return jsonify({
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'mensaje': 'No se encontraron datos de personal',
                'desempeno_individual': []
            })
        
        desempeno_limpiadores = []
        
        for limpiador in limpiadores:
            id_limpiador = limpiador.get('idEmpleado', limpiador.get('id', ''))
            
            # Filtrar agendas asignadas a este limpiador
            agendas_limpiador = []
            for agenda in agendas:
                limpiadores_asignados = agenda.get('limpiadoresAsignados', [])
                if isinstance(limpiadores_asignados, set):
                    limpiadores_asignados = list(limpiadores_asignados)
                elif not isinstance(limpiadores_asignados, list):
                    limpiadores_asignados = []
                
                # Verificar si el ID del limpiador está en la lista
                if id_limpiador in limpiadores_asignados:
                    agendas_limpiador.append(agenda)
            
            # Calcular métricas
            tareas_completadas = len([a for a in agendas_limpiador if a.get('estado') == 'COMPLETADO'])
            tareas_asignadas = len(agendas_limpiador)
            
            # Calcular habitaciones completadas
            habitaciones_completadas = 0
            for agenda in agendas_limpiador:
                if agenda.get('estado') == 'COMPLETADO':
                    habitaciones = agenda.get('habitationsAsignadas', [])
                    if isinstance(habitaciones, set):
                        habitaciones = list(habitaciones)
                    elif not isinstance(habitaciones, list):
                        habitaciones = []
                    habitaciones_completadas += len(habitaciones)
            
            eficiencia = (tareas_completadas / tareas_asignadas * 100) if tareas_asignadas > 0 else 0
            
            desempeno_limpiadores.append({
                'id': id_limpiador,
                'nombre': limpiador.get('nombre', 'Sin nombre'),
                'estado': limpiador.get('estado', 'INACTIVO'),
                'tareas_asignadas': tareas_asignadas,
                'tareas_completadas': tareas_completadas,
                'habitaciones_completadas': habitaciones_completadas,
                'eficiencia': round(eficiencia, 2),
                'horas_trabajadas': calcular_horas_trabajadas_limpiador(id_limpiador, agendas)
            })
        
        # Ordenar por eficiencia
        desempeno_limpiadores.sort(key=lambda x: x['eficiencia'], reverse=True)
        
        return jsonify({
            'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
            'total_personal': len(limpiadores),
            'activos': len([l for l in limpiadores if l.get('estado') == 'ACTIVO']),
            'inactivos': len([l for l in limpiadores if l.get('estado') == 'INACTIVO']),
            'desempeno_individual': desempeno_limpiadores,
            'promedios': {
                'eficiencia_promedio': round(calcular_promedio([d['eficiencia'] for d in desempeno_limpiadores]), 2),
                'tareas_promedio': round(calcular_promedio([d['tareas_asignadas'] for d in desempeno_limpiadores]), 2),
                'horas_promedio': round(calcular_promedio([d.get('horas_trabajadas', 0) for d in desempeno_limpiadores]), 2)
            },
            'recomendaciones_personal': generar_recomendaciones_personal(desempeno_limpiadores)
        })
    
    except Exception as e:
        print(f"Error en reporte personal: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Error generando reporte personal: {str(e)}"}), 500

# ========== ENDPOINT DE DEBUG PARA REPORTES ==========

@app.route('/debug/reporte', methods=['GET'])
def debug_reporte():
    """Endpoint para debug de reportes"""
    try:
        # Mostrar información de cada tabla
        info_tablas = {}
        
        for tabla_nombre, tabla_info in TABLES.items():
            table = tabla_info['table']
            try:
                response = table.scan(Limit=5)
                items = response.get('Items', [])
                info_tablas[tabla_nombre] = {
                    'count': len(items),
                    'sample_pks': [item.get('PK', 'Sin PK')[:50] for item in items[:3]],
                    'sample_sks': [item.get('SK', 'Sin SK')[:50] for item in items[:3]]
                }
            except Exception as e:
                info_tablas[tabla_nombre] = {'error': str(e)}
        
        # Probar funciones individuales
        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        fecha_ayer = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        reservas = obtener_reservas_por_fecha(fecha_ayer, fecha_hoy)
        agendas = obtener_agendas_por_fecha(fecha_ayer, fecha_hoy)
        limpiadores = obtener_limpiadores_activos()
        habitaciones = obtener_habitaciones()
        
        return jsonify({
            'tablas_info': info_tablas,
            'funciones_prueba': {
                'reservas_count': len(reservas),
                'agendas_count': len(agendas),
                'limpiadores_count': len(limpiadores),
                'habitaciones_count': len(habitaciones)
            },
            'formato_pk_agenda': 'AGENDA#YYYY-MM-DD',
            'formato_pk_reserva': 'RESERVA#YYYY-MM-DD#IDRESERVA',
            'nota': 'Las fechas deben coincidir exactamente con el formato en PK'
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def obtener_agendas_por_fecha(fecha_inicio, fecha_fin, zona=None):
    """Obtener agendas en un rango de fechas"""
    try:
        response = table_limpieza.scan()
        agendas = response.get('Items', [])
        
        agendas_filtradas = []
        for agenda in agendas:
            fecha_agenda = extract_fecha_from_pk(agenda.get('PK', ''))
            if fecha_agenda and fecha_inicio <= fecha_agenda <= fecha_fin:
                agenda_json = convertir_para_json(agenda)
                if zona:
                    if agenda_json.get('zona') == zona:
                        agendas_filtradas.append(agenda_json)
                else:
                    agendas_filtradas.append(agenda_json)
        
        return agendas_filtradas
    except Exception as e:
        print(f"Error obteniendo agendas: {str(e)}")
        return []

def obtener_limpiadores_activos():
    """Obtener todos los limpiadores"""
    try:
        response = table_limpiadores.scan()
        limpiadores = response.get('Items', [])
        return [convertir_para_json(l) for l in limpiadores]
    except Exception as e:
        print(f"Error obteniendo limpiadores: {str(e)}")
        return []

def obtener_habitaciones():
    """Obtener todas las habitaciones"""
    try:
        response = table_habitacion.scan()
        habitaciones = response.get('Items', [])
        return [convertir_para_json(h) for h in habitaciones]
    except Exception as e:
        print(f"Error obteniendo habitaciones: {str(e)}")
        return []

def extract_fecha_from_pk(pk):
    """Extraer fecha de una PK de agenda"""
    if pk.startswith('AGENDA#'):
        parts = pk.split('#')
        if len(parts) > 1:
            return parts[1]
    return None

def calcular_promedio(valores):
    """Calcular promedio de una lista de valores"""
    if not valores:
        return 0
    return sum(valores) / len(valores)

def calcular_horas_trabajadas(agendas, limpiadores):
    """Calcular horas totales trabajadas"""
    # Simplificado: 1 hora por agenda
    return len(agendas)

def calcular_habitaciones_por_hora(zona, agendas):
    """Calcular habitaciones por hora para una zona"""
    agendas_zona = [a for a in agendas if a.get('zona') == zona]
    if not agendas_zona:
        return 0
    
    total_habitaciones = sum(len(a.get('habitationsAsignadas', [])) for a in agendas_zona)
    return total_habitaciones / len(agendas_zona)

def calcular_horas_trabajadas_limpiador(id_limpiador, agendas):
    """Calcular horas trabajadas por un limpiador"""
    agendas_limpiador = [a for a in agendas if id_limpiador in a.get('limpiadoresAsignados', [])]
    # Suponer 1 hora por agenda
    return len(agendas_limpiador)

def calcular_duracion_promedio(reservas):
    """Calcular duración promedio de reservas"""
    if not reservas:
        return 0
    
    total_noches = 0
    for reserva in reservas:
        fecha_inicio = reserva.get('fechaInicio', '')
        fecha_fin = reserva.get('fechaFin', '')
        if fecha_inicio and fecha_fin:
            try:
                inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
                duracion = (fin - inicio).days
                total_noches += max(duracion, 1)
            except:
                total_noches += 1
    
    return total_noches / len(reservas)

def calcular_tasa_cancelacion(reservas):
    """Calcular tasa de cancelación"""
    if not reservas:
        return 0
    
    canceladas = len([r for r in reservas if r.get('estado') == 'CANCELADA'])
    return (canceladas / len(reservas)) * 100

def obtener_detalle_diario(fecha_inicio, fecha_fin):
    """Obtener detalle diario de actividades"""
    try:
        # Crear un diccionario con todas las fechas del período
        inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        detalle = {}
        current_date = inicio
        while current_date <= fin:
            fecha_str = current_date.strftime('%Y-%m-%d')
            detalle[fecha_str] = {
                'reservas': 0,
                'checkins': 0,
                'checkouts': 0,
                'tareas_limpieza': 0,
                'tareas_completadas': 0,
                'ingresos': 0
            }
            current_date += timedelta(days=1)
        
        # Aquí podrías llenar los datos reales consultando las tablas
        # Por ahora devolvemos la estructura vacía
        
        return detalle
    except Exception as e:
        print(f"Error obteniendo detalle diario: {str(e)}")
        return {}

def generar_resumen_textual(estadisticas):
    """Generar un resumen textual del reporte"""
    res = estadisticas['reservas']
    limp = estadisticas['limpieza']
    pers = estadisticas['personal']
    hab = estadisticas['habitaciones']
    
    resumen = f"""
    REPORTE GENERAL - {estadisticas['fechas']['generado']}
    
    RESERVAS:
    • Total: {res['total']} reservas
    • Confirmadas: {res['confirmadas']}
    • Pendientes: {res['pendientes']}
    • Canceladas: {res['canceladas']}
    • Ingresos estimados: ${res['ingresos_estimados']:,.2f}
    
    LIMPIEZA:
    • Tareas programadas: {limp['tareas_totales']}
    • Completadas: {limp['tareas_completadas']}
    • En progreso: {limp['tareas_en_progreso']}
    • Pendientes: {limp['tareas_pendientes']}
    • Progreso promedio: {limp['progreso_promedio']}%
    
    PERSONAL:
    • Total limpiadores: {pers['total_limpiadores']}
    • Activos: {pers['limpiadores_activos']}
    • Inactivos: {pers['limpiadores_inactivos']}
    • Horas trabajadas: {pers['horas_totales_trabajadas']}h
    
    HABITACIONES:
    • Total: {hab['total']}
    • Disponibles: {hab['disponibles']}
    • Ocupadas: {hab['ocupadas']}
    • En limpieza: {hab['en_limpieza']}
    • En mantenimiento: {hab['mantenimiento']}
    """
    
    return resumen

def generar_recomendaciones_limpieza(agrupado_por_zona):
    """Generar recomendaciones basadas en datos de limpieza"""
    recomendaciones = []
    
    for zona, stats in agrupado_por_zona.items():
        if stats['pendientes'] > stats['completadas']:
            recomendaciones.append(f"Zona {zona}: Alta carga pendiente. Considerar asignar más personal.")
        
        if len(stats['limpiadores_asignados']) == 0 and stats['total_tareas'] > 0:
            recomendaciones.append(f"Zona {zona}: Tareas sin limpiadores asignados. Revisar asignaciones.")
    
    if not recomendaciones:
        recomendaciones.append("El rendimiento de limpieza es adecuado. Mantener distribución actual.")
    
    return recomendaciones

def generar_recomendaciones_personal(desempeno):
    """Generar recomendaciones para el personal"""
    recomendaciones = []
    
    if desempeno:
        mejor_limpiador = max(desempeno, key=lambda x: x['eficiencia'])
        peor_limpiador = min(desempeno, key=lambda x: x['eficiencia'])
        
        if mejor_limpiador['eficiencia'] > 90:
            recomendaciones.append(f"Reconocer el buen desempeño de {mejor_limpiador['nombre']} (eficiencia: {mejor_limpiador['eficiencia']}%)")
        
        if peor_limpiador['eficiencia'] < 50:
            recomendaciones.append(f"Ofrecer capacitación adicional a {peor_limpiador['nombre']} (eficiencia: {peor_limpiador['eficiencia']}%)")
    
    return recomendaciones

def analizar_tendencias_reservas(reservas):
    """Analizar tendencias en las reservas"""
    tendencias = {
        'dias_populares': {},
        'tipo_popular': '',
        'cliente_frecuente': ''
    }
    
    if reservas:
        # Contar reservas por día de la semana
        for reserva in reservas:
            fecha = reserva.get('fechaInicio', '')
            if fecha:
                try:
                    dia_semana = datetime.strptime(fecha, '%Y-%m-%d').strftime('%A')
                    tendencias['dias_populares'][dia_semana] = tendencias['dias_populares'].get(dia_semana, 0) + 1
                except:
                    pass
        
        # Tipo de habitación más popular
        tipos = {}
        for reserva in reservas:
            tipo = reserva.get('tipoHabitacion', '')
            if tipo:
                tipos[tipo] = tipos.get(tipo, 0) + 1
        
        if tipos:
            tendencias['tipo_popular'] = max(tipos.items(), key=lambda x: x[1])[0]
    
    return tendencias

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')