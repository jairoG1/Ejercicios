###### Jairo Guardado Aragón
## Práctica 5: Operaciones CRUD en DynamoDB
## Parte 1: Diseño y Creación de la Tabla
##### Basándote en el patrón de acceso principal (histórico por sensor), decide cuáles serán tu Partition Key y tu Sort Key.
```bash
aws dynamodb create-table \
    --table-name SensoresEcoCity \
    --attribute-definitions \
        AttributeName=sensor_id,AttributeType=S \
        AttributeName=Timestamp,AttributeType=S \
    --key-schema \
        AttributeName=sensor_id,KeyType=HASH \
        AttributeName=Timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST
```

### Resultado Consola
```bash
    "TableDescription": {
        "AttributeDefinitions": [
            {
                "AttributeName": "Timestamp",
                "AttributeType": "S"
            },
            {
                "AttributeName": "sensor_id",
                "AttributeType": "S"
            }
        ],
        "TableName": "SensoresEcoCity",
        "KeySchema": [
            {
                "AttributeName": "sensor_id",
                "KeyType": "HASH"
:
```
![Foto4](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea5.1.png)

## 2. Ingesta de Datos (Create)
##### Los sensores empiezan a enviar datos.
###### Sensor 1
```bash
aws dynamodb put-item \
    --table-name SensoresEcoCity \
    --item '{
        "sensor_id": {"S": "SENSOR-ZONA-Norte-01"},
        "Timestamp": {"S": "2024-11-20T10:00:00Z"},
        "Tipo_de_Medición": {"S": "CO2, Ruido, Temperatura"},
        "Valor": {"N": "30"},
        "Estado": {"S": "OK, Alerta, Mantenimiento"}
      }'
```
###### Sensor 2
```bash
aws dynamodb put-item \
    --table-name SensoresEcoCity \
    --item '{
        "sensor_id": {"S": "SENSOR-ZONA-Norte-02"},
        "Timestamp": {"S": "2022-10-20T10:00:00Z"},
        "Tipo_de_Medición": {"S": "CO2"},
        "Valor": {"N": "42"},
        "Estado": {"S": "OK, Alerta, Mantenimiento"}
      }'
```
###### Sensor 3
```bash
aws dynamodb put-item \
    --table-name SensoresEcoCity \
    --item '{
        "sensor_id": {"S": "SENSOR-ZONA-Norte-02"},
        "Timestamp": {"S": "2021-09-20T10:00:00Z"},
        "Tipo_de_Medición": {"S": "Temperatura"},
        "Valor": {"N": "14"},
        "Estado": {"S": "Falso, Alerta, Mantenimiento"}
      }'
```
###### Sensor 4
```bash
aws dynamodb put-item \
    --table-name SensoresEcoCity \
    --item '{
        "sensor_id": {"S": "SENSOR-ZONA-Norte-04"},
        "Timestamp": {"S": "2002-01-20T10:00:00Z"},
        "Tipo_de_Medición": {"S": " Ruido"},
        "Valor": {"N": "25"},
        "Estado": {"S": "OK, Alerta, Mantenimiento"}
      }'
```
###### Sensor 5
```bash
aws dynamodb put-item \
    --table-name SensoresEcoCity \
    --item '{
        "sensor_id": {"S": "SENSOR-ZONA-Norte-04"},
        "Timestamp": {"S": "2042-02-20T10:00:00Z"},
        "Tipo_de_Medición": {"S": "CO2, Ruido"},
        "Valor": {"N": "11"},
        "Estado": {"S": "Falso, Alerta, Mantenimiento"}
      }'
```

### Resultado Consola


![Foto4](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea5.3.png)

## 3. Consulta de Datos (Read - Query)
##### Los analistas quieren ver la evolución de la temperatura del sensor SENSOR-ZONA-Norte-01.
```bash
aws dynamodb query \
    --table-name SensoresEcoCity \
    --key-condition-expression "sensor_id = :cid" \
    --expression-attribute-values '{ ":cid": {"S": "SENSOR-ZONA-Norte-01"} }'
```

### Resultado Consola
```bash
{
    "Items": [
        {
            "Estado": {
                "S": "OK, Alerta, Mantenimiento"
            },
            "Tipo_de_Medición": {
                "S": "CO2, Ruido, Temperatura"
            },
            "sensor_id": {
                "S": "SENSOR-ZONA-Norte-01"
            },
            "Valor": {
                "N": "30"
            },
            "Timestamp": {
                "S": "2024-11-20T10:00:00Z"
```
![Foto4](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea5.2.png)


## 4. Actualización de Datos (Update)
##### Un técnico ha revisado un sensor que daba lecturas erróneas y lo ha recalibrado. Debemos marcar esa lectura antigua como “Mantenimiento”.
```bash
aws dynamodb update-item \
    --table-name SensoresEcoCity \
    --key '{
        "sensor_id": {"S": "SENSOR-ZONA-Norte-01"},
        "Timestamp": {"S": "2024-11-20T10:00:00Z"}
    }' \
    --update-expression "SET Estado = :c, Nota = :val" \
    --expression-attribute-values '{
        ":c": {"S": "Mantenimiento"},
        ":val": {"S": "Recalibrado por técnico"}
    }' \
    --return-values UPDATED_NEW
```
### Resultado Consola
```bash
    "Attributes": {
        "Estado": {
            "S": "Mantenimiento"
        },
        "Nota": {
            "S": "Recalibrado por técnico"
        }
    }
}
```
![Foto4](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea5.4.png)

## 5. Eliminación de Datos (Delete)
##### Una lectura fue generada por un sensor defectuoso antes de ser activado oficialmente.


```bash
aws dynamodb delete-item \
    --table-name SensoresEcoCity \
    --key '{
        "sensor_id": {"S": "SENSOR-ZONA-Norte-02"},
        "Timestamp": {"S": "2022-10-20T10:00:00Z"}
    }' 
```
### Resultado Consola

![Foto4](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea5.5.png)

## 6. Reto Avanzado: Alertas Globales (Opcional)
##### Pregunta: Con tu diseño actual (clave partición = ID Sensor), ¿puedes hacer esto eficientemente con un Query? ¿Por qué?
>No,ya que la query es solo eficas si añades  tambien la ordenacion en la propia query
### Propuesta
>La propuesta sería crear un GSI para poder consultar los sensores de manera global según lo nos interesen,La clave de partición del GSI podría ser el tipo de medicion y la clave de ordenación del GSI sería el timestamp.
```bash
aws dynamodb update-table \
    --table-name SensoresEcoCity \
    --attribute-definitions AttributeName=tipoMedicion,AttributeType=S AttributeName=Tipo_de_Medición,AttributeType=S \
    --global-secondary-index-updates '[{
        "Create": {
            "IndexName": "AlertasGlobalesIndex",
            "KeySchema": [
                {"AttributeName":"tipoMedicion","KeyType":"HASH"},
                {"AttributeName":"Tipo_de_Medición","KeyType":"RANGE"}
            ],
            "Projection": {"ProjectionType":"ALL"}
        }
    }]'
```
## Conclusión:
###### Una breve reflexión sobre la idoneidad de DynamoDB para datos de IoT (Internet of Things).
>DynamoDB va bien para IoT porque aguanta muchos datos y funciona rápido. Es bueno para guardar lecturas de sensores en tiempo real, pero no sirve tanto para hacer consultas muy complicadas. Con un buen creador de  diseño de tablas.













