###### Jairo Guardado Aragón
## Ejercicio 4: Automatización de DynamoDB con Python y Boto3
## Parte 1: Preparando el Entorno de Programación
### 1.1. Instalación de Boto3
#### Instala Boto3:
![Foto3](![Foto1](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea4.1.png))
##### Aqui se muestra la instalacion de Boto3
-------------
![Foto3](![Foto1](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea4.2.png)
##### Despues introducimos las credenciales a traves del comando aws configure
### 1.2. Verificación de las Credenciales
![Foto3](![Foto1](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea4.3.png)
##### En esta parte comprobamos y verificamos el usuaria de AWS
## Parte 2: Automatizando Operaciones con Boto3
### 2.1. Conexión a DynamoDB
```python
import boto3

# 1. Crear un recurso de servicio de DynamoDB
# Reemplaza 'us-east-1' con la región que estés utilizando
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# 2. Seleccionar la tabla 'Orders'
table = dynamodb.Table('Orders')

# 3. Imprimir un mensaje de confirmación
print(f"Conectado a la tabla '{table.name}' en la región '{dynamodb.meta.client.meta.region_name}'.")
```
### Ejercicio 1: Crear un Nuevo Pedido
```python
def create_order(order_id, customer_name, product, quantity, status):
    '''Crea un nuevo ítem en la tabla Orders.'''
    try:
        response = table.put_item(
           Item={
                'order_id': order_id,
                'customer_name': customer_name,
                'product': product,
                'quantity': quantity,
                'status': status,
                'order_date': '2025-11-10' # Puedes usar una fecha actual
            }
        )
        print(f"Pedido {order_id} creado exitosamente.")
        return response
    except Exception as e:
        print(f"Error al crear el pedido: {e}")
```
### Ejercicio 2: Leer un Pedido
```python
def get_order(order_id):
    '''Obtiene un ítem de la tabla Orders por su ID.'''
    try:
        response = table.get_item(Key={'order_id': order_id})
        item = response.get('Item')
        if item:
            print(f"Datos del pedido {order_id}: {item}")
            return item
        else:
            print(f"No se encontró el pedido con ID {order_id}.")
            return None
    except Exception as e:
        print(f"Error al obtener el pedido: {e}")
```
### Ejercicio 3: Actualizar el Estado de un Pedido
```python
def update_order_status(order_id, new_status):
    '''Actualiza el atributo 'status' de un pedido.'''
    try:
        response = table.update_item(
            Key={'order_id': order_id},
            UpdateExpression="set #st = :s",
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues={':s': new_status},
            ReturnValues="UPDATED_NEW"
        )
        print(f"Estado del pedido {order_id} actualizado a '{new_status}'.")
        return response
    except Exception as e:
        print(f"Error al actualizar el pedido: {e}")
```
### Ejercicio 4: Eliminar un Pedido
```python
def delete_order(order_id):
    '''Elimina un item de la tabla Orders.'''
    try:
        response = table.delete_item(Key={'order_id': order_id})
        print(f"Pedido {order_id} eliminado exitosamente.")
        return response
    except Exception as e:
        print(f"Error al eliminar el pedido: {e}")
```
### Ejercicio 5: Buscar Pedidos por Cliente
```python
def get_orders_by_customer(customer_name):
    '''Elimina un item de la tabla Orders.'''
    try:
        response = table.delete_item(Key={'order_id': order_id})
        print(f"Pedido {order_id} eliminado exitosamente.")
        return response
    except Exception as e:
        print(f"Error al eliminar el pedido: {e}")
```
### Ejercicio 6: TU TAREA
```python
def get_orders_by_customer(customer_name):
    response = table.scan(FilterExpression=Attr('customer_name').eq(customer_name))
    items = response['Items']
    print(f"Pedidos encontrados para '{customer_name}':")
    for order in items:
        print(order)
    return items
```
>En esta función hemos utilizado el scan() y hacemos una busqueda por clientes para luego encontrar los pedidos que a realizado
### Parte 3: Demostración y Entrega
```python
if __name__ == "__main__":
    print("--- Demostración de operaciones con DynamoDB ---")

    # 1. Crear un nuevo pedido
    create_order("ORD-PY-1001", "Ana García", "Teclado Mecánico", 1, "Pending")

    # 2. Leer el pedido recién creado
    get_order("ORD-PY-1001")

    # 3. Actualizar su estado
    update_order_status("ORD-PY-1001", "Shipped")
    get_order("ORD-PY-1001") # Verificamos el cambio

    # 4. Buscar todos los pedidos de un cliente (usa un nombre que exista en tu tabla)
    get_orders_by_customer("Ana García")
    get_orders_by_customer("Carlos Soto") # Ejemplo con otro cliente

    # 5. Eliminar el pedido
    delete_order("ORD-PY-1001")
    get_order("ORD-PY-1001") # Verificamos que ya no existe

    print("\n--- Demostración finalizada ---")
```
##### Resultado del Script
![Foto3](![Foto1](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea4.7.png)

### Reflexión Final
 >Automatización vs. Consola: ¿Qué ventajas claras observas al usar un script de Python en lugar de la consola web de AWS para gestionar los datos? ¿Y qué desventajas?
 
Como ventajas veo la facilidad de manipular los datos a traves de un lenguaje que ya conoces , como desventaja veria la falta de claridad de ver tus objetos ya que mediante consola no puedes ver los datos de forma visual



 >SDK como Herramienta: ¿En qué otros escenarios (además de gestionar pedidos) podrías imaginar el uso de Boto3 para automatizar tareas en AWS?

- Subir/descargar archivos en S3 o hacer copias de seguridad.

- Iniciar, detener o hacer snapshots de instancias EC2.

- Gestionar bases de datos RDS y generar reportes.

- Configurar alarmas y extraer métricas con CloudWatch.

- Crear usuarios y roles en IAM automáticamente.

- Desplegar funciones Lambda y automatizar flujos entre servicios.

 >Dificultades y Aprendizajes: ¿Qué parte de la práctica te resultó más desafiante? ¿Cuál fue el concepto más interesante que aprendiste?

La parte mas desafiante fue de realizar la funcion de encontrar el cliente y luego mostrar los pedidos.Lo mas importante que e aprendido es la facilidad y como se puede consustar y manipular datos a traves de la consola y a traves del lenguaje python
