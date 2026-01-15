import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
#Convertimos la fecha de ayer y hoy
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
    

#Cargamos el dataset
df = pd.read_csv("ventas.csv")
df.info()
filasiniciales= len(df)
#Vemos cuantos duplicados ahi
df.duplicated().sum()

#Eliminamos los duplicados
filaseliminadas=df.drop_duplicates()

#comprobamos que se han borrado
df.duplicated().sum()

#Eliminamos los espacios en blanco 
df = df.apply(lambda col: col.str.rstrip() if col.dtype == "object" else col)

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

#Convertir fechas en formato ISO
df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce', dayfirst=True)

# Aplicar la función a la columna
df['fecha'] = df['fecha'].apply(convertir_fecha_relativa)

#Pasar a json
df.to_json("ventas_limpias_Jairo.json", orient="records", force_ascii=False, indent=4)

#para ver los registros perdidos
df_limpio = df.drop_duplicates(subset="id", keep="first")
df_limpio = df.groupby("id").agg({
    "producto": "first",
    "precio": "median",  
    "cantidad": "sum"
}).reset_index()
registros_iniciales = len(df)
registros_finales = len(df_limpio)
perdidos = registros_iniciales - registros_finales

print("Iniciando limpieza de [Jairo Guardado]")
print("Total de filas iniciales.",{filasiniciales})
print("Total de filas eliminadas por duplicidad.",len(filaseliminadas))
print("Valor de la mediana utilizada para los precios.",{media})
print("Número total de registros con “cantidades negativas” descartados.",{negativos})
print(f"Registros perdidos: {perdidos}")
