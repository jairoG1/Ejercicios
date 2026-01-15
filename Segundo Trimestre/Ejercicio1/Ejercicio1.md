###### Jairo Guardado Aragón
## Práctica 1: Hijo de la Forja (Limpieza de Datos Masivos)

### 1. Carga del dataset:
#### Utilizar read_csv y analizar la estructura inicial con info().
```python
df = pd.read_csv("ventas.csv")
df.info()
```
#### Fase de Limpieza Estructural:
#### Aplicar drop_duplicates y realizar el filtrado de cantidades.
```python
#Vemos cuantos duplicados ahi
df.duplicated().sum()

#Eliminamos los duplicados
filaseliminadas=df.drop_duplicates()

#comprobamos que se han borrado
df.duplicated().sum()
```
### Fase de Transformación:
#### Asegurar tipos de datos y manejar errores de conversión con errors='coerce'.
```python
#Convertir a Camelcase o capitalizado
df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

#Tratamiento de precios:
df["precio"] = pd.to_numeric(df["precio"], errors="coerce")
media=df["precio"].median()
df["precio"].fillna(df["precio"].median(), inplace=True)

#Validación de cantidades
negativos=(df["cantidad"] < 0).sum()
print("Registros descartados por cantidades negativas:", negativos)
df["cantidad"].fillna(df["cantidad"].median(), inplace=True)
```
### Procesamiento de Fechas:
#### Desarrollar una función que use datetime para transformar “Hace X dias” en fechas reales.
```python
def convertir_fecha_relativa(valor):
    hoy = datetime.now().date()
    
    if pd.isna(valor):
        return pd.NaT
    
    valor = str(valor).strip().lower()
    if valor == "hoy":
        return hoy
    elif valor == "ayer":
        return hoy - timedelta(days=1)
    match = re.match(r"hace (\d+) días?", valor)
    if match:
        dias = int(match.group(1))
        return hoy - timedelta(days=dias)
    
    try:
        return pd.to_datetime(valor, dayfirst=True).date()
    except:
        return pd.NaT  
```
#### Exportación y Reporte:
#### Guardar en JSON e imprimir la bitácora final.
```python
df.to_json("ventas_limpias_Jairo.json", orient="records", force_ascii=False, indent=4)
```

### La Bitácora de Limpieza 
#### Al final de la ejecución, el programa debe imprimir un resumen con:
* Total de filas iniciales.
* Total de filas eliminadas por duplicidad.
* Valor de la mediana utilizada para los precios.
* Número total de registros con “cantidades negativas” descartados.

```python
filasiniciales= len(df)
filaseliminadas=df.drop_duplicates()
media=df["precio"].median()
negativos=(df["cantidad"] < 0).sum()


print("Iniciando limpieza de [Jairo Guardado]")
print("Total de filas iniciales.",{filasiniciales})
print("Total de filas eliminadas por duplicidad.",len(filaseliminadas))
print("Valor de la mediana utilizada para los precios.",{media})
print("Número total de registros con “cantidades negativas” descartados.",{negativos})

```
![Foto4](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea1.2.1.png)
## Preguntas de reflexión

### ¿Cuántos registros se perdieron en total tras todo el proceso de limpieza?.
```python
df_limpio = df.drop_duplicates(subset="id", keep="first")
df_limpio = df.groupby("id").agg({
    "producto": "first",
    "precio": "median",  
    "cantidad": "sum"
}).reset_index()
registros_iniciales = len(df)
registros_finales = len(df_limpio)
perdidos = registros_iniciales - registros_finales
print(f"Registros perdidos: {perdidos}")
```
Un total de 451 registros perdidos



### ¿Hubo algún caso de id repetido con datos distintos? ¿Cómo decidiste manejarlo para no perder información?
-No hubo ids repetidos con datos distintos 
-De esta manejamos el no perder esa informacion
```python
df_limpio = df.drop_duplicates(subset="id", keep="first")
```


### ¿Por qué crees que es más seguro usar la mediana que la media para imputar precios en este dataset con errores manualles?

Es más seguro usar la mediana porque es menos sensible a valores extremos o errores de registro. En un dataset con errores manuales, como precios muy altos o muy bajos por equivocación, la media se ve afectada y puede dar un valor distorsionado. En cambio, la mediana representa el valor central real de los datos, proporcionando una estimación más confiable y robusta para imputar precios.