###### Jairo Guardado Aragón
## Práctica 2: El Pergamino Infinito (Consumo de APIs)

### Requisitos
#### Librería requests y pandas instaladas (pip install requests pandas).
![Foto1](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea2.2.1.png)

#### Paso a Paso
#### Preparar el Bucle Ninja.
```python
import requests 
import time
import pandas as pd

url_inicial = "https://pokeapi.co/api/v2/pokemon?limit=100" 
todos_los_pokemon_resumen = []
```
#### Realizar la Invocación (Petición).
```python
url = url_inicial
while url:
    response = requests.get(url)
    data = response.json()
    todos_los_pokemon_resumen.extend(data['results'])
    #  ir actualizando las paginas
    url = data['next']
    
    print(f"cogidos {len(todos_los_pokemon_resumen)} Pokémon...", end="\r")
    time.sleep(0.2) #para no saturar

print(f"Total: {len(todos_los_pokemon_resumen)}")

datos_finales = []
```
#### Aplanado de Datos (Flattening - Rango Jōnin).
```python
for poke in todos_los_pokemon_resumen[:1350]: 
    res = requests.get(poke['url'])
    detalles = res.json()
    
    # Extraemos solo lo necesario
    datos_finales.append({
        "name": detalles['name'],
        "height": detalles['height'],
        "weight": detalles['weight'],
        "base_experience": detalles['base_experience']
    })
    time.sleep(0.1)
```
#### Cálculo de Campos Derivados (Ingeniería de Características).
```python
# pasamos a  a DataFrame
df = pd.DataFrame(datos_finales)
df['height_m'] = df['height'] / 10
df['weight_kg'] = df['weight'] / 10
df['bmi'] = df['weight_kg'] / (df['height_m'] ** 2)
df['bmi'] = df['bmi'].round(2)
```
#### Guardado del Pergamino
```python
# Guardar en CSV
df.to_csv("pokemon2.csv", index=False)
# guardar a json
df.to_json("pokemon3.json", orient='records',indent=2)
```
## Preguntas de reflexión

### ¿Por qué es importante actualizar la URL con el enlace next en lugar de simplemente incrementar un número de página manualmente?
tenemos varias razones 
    * Tenemos una finalizacion de datos clara
    * Tema de Compatibilidad con cursores
    * Evitamos errores de conteo

### ¿Qué ventaja tiene normalizar las unidades (como pasar de decímetros a metros) dentro del propio proceso ETL en lugar de hacerlo después en una hoja de cálculo?
tenemos 4 ventajas principalmente
    * Evitamos errores nuestro de los humanos
    * Ahorre de tiempo
    * Consistencia Total
    * Una Capacidad Masiva  

### Si la API tuviera un límite de 1000 registros por página, ¿cómo afectaría esto al rendimiento de tu script?

nos favorece bastante el echo  de limitar el registro a 1000 ya que tendremos mejor velocidad de ejecucion ,menor consumo de memoria y mayor velocidad de procesamiento de datos