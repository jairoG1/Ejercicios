###### Jairo Guardado Aragón
## Práctica 1. El Rastro de la Grieta
## Bloque A: Limpieza

### Eliminación de Clones: Elimina registros idénticos que ensucian la base de datos.
```python
df = df.drop_duplicates()
```
### Estandarización de Aldeas: Normaliza los nombres de las aldeas (ej: “konoha ” -> “Konoha”).
```python
    df["aldea"] = df["aldea"].str.lower().str.strip()
```
### Identidad en la Niebla: Asigna nombres genéricos a los ninjas anónimos de Kiri.
```python
    df.loc[(df['nin_id'].isnull()) & (df['aldea'] == 'kiri'), 'nin_id'] = 'Ninja de la Niebla Anonimo'
```
### Despertar de la Fecha: Asegura que la columna de tiempo sea un objeto datetime.
```python
    df['ts'] = pd.to_datetime(df['ts'])
```
### Control de Chakra: Limpia valores de chakra que sean físicamente imposibles.
```python
    df = df[(df['chakra'] > 0) & (df['chakra'] <= 100000)]
```
### Formato ANBU: Renombra las columnas para que el informe sea profesional.
```python
  df = df.rename(columns={
        'id_reg': 'ID', 
        'ts': 'Fecha', 
        'nin_id': 'Ninja', 
        'status': 'Estado', 
        'desc': 'Descripcion'
    })
```
## Bloque B: Búsqueda

### Palabras Clave: Detecta amenazas filtrando palabras prohibidas en las descripciones.
```python
patron = 'espía|sospechoso|enemigo'
    sospechosos = df[df['Descripcion'].str.contains(patron, case=False, na=False)]
```
### El Infiltrado de la Lluvia: Localiza ninjas de rango alto de Amegakure.
```python
    ameelites = df[(df['aldea'] == 'amegakure') & (df['chakra'] > 5000) & (df['rango'] != 'D')]
```
### Vigilancia Nocturna: Identifica quién se mueve en las sombras de la madrugada.
```python
    madrugada = df[(df['Fecha'].dt.hour >= 23) | (df['Fecha'].dt.hour < 5)]
```
### La Elite de las Aldeas: Muestra a los guerreros más poderosos de cada nación.
```python
    topchakra = df.sort_values('chakra', ascending=False).groupby('aldea').head(5)
```
### Rastreo de Extranjeros: Filtra a los ninjas que no pertenecen a la Gran Alianza.
```python
alianza = ['konoha', 'suna', 'kumo']
    fueraalianza = df[~df['aldea'].isin(alianza)]
```
### Mapa de Fallos: Localiza qué regiones tienen más misiones fallidas.
```python
    fallosporaldea = df[df['Estado'] == 'Fallo'].groupby('aldea').size()
```

## Preguntas de reflexión

### ¿Cuántos registros duplicados has encontrado y qué impacto tendrían en un análisis de Big Data si no se eliminaran?
Los duplicados generan falsos positivos. En Big Data, esto infla las estadísticas y distorsiona la realidad, provocando que se tomen decisiones basadas en datos inexistentes o exagerados

### ¿Por qué es crítico convertir la columna de fecha a datetime antes de realizar búsquedas por franja horaria?    
Es vital porque el formato original es simple texto. Al convertirlo a datetime, el sistema "entiende" el tiempo, permitiendo extraer horas, días o meses para filtrar misiones nocturnas con un solo comando.
### ¿Cómo has manejado los niveles de chakra > 100,000? ¿Crees que son errores de sensor o posibles técnicas prohibidas?
Se han eliminado por ser datos atípicos. Aunque podrían ser técnicas prohibidas, lo más lógico en análisis de datos es tratarlos como errores de lectura del sensor, ya que distorsionan el promedio de un ninja normal.


### Conclusión: Breve opinión sobre cómo Pandas facilita el trabajo de un analista ANBU frente a una búsqueda manual en un pergamino de 1.500 líneas.
Pandas transforma horas de revisión manual en un pergamino en segundos de ejecución. Mientras que un humano puede obviar un detalle por fatiga, el código garantiza precisión total y permite al analista ANBU detectar amenazas al instante.