import pandas as pd

# 1. Carga del pergamino secreto
df = pd.read_csv(r'C:\Users\jguardadoa01\Desktop\Justo\Segundo Trimestre\Ejercicio4\registros_misiones.csv')
# --- SECCIÓN 1: LIMPIEZA DE DATOS ---

def limpiar_registro(df):
    # Reto 1: Elimina filas duplicadas
    df = df.drop_duplicates()
    
    # Reto 2: Estandariza la columna 'aldea'
    df["aldea"] = df["aldea"].str.lower().str.strip()
    
    # Reto 3: Relleno de ninjas anónimos de Kiri
    df.loc[(df['nin_id'].isnull()) & (df['aldea'] == 'kiri'), 'nin_id'] = 'Ninja de la Niebla Anonimo'
    
    # Reto 4: Convierte 'ts' a datetime
    df['ts'] = pd.to_datetime(df['ts'])
    
    # Reto 5: Filtra o corrige niveles de chakra imposibles (<= 0 o > 100.000)
    df = df[(df['chakra'] > 0) & (df['chakra'] <= 100000)]
    
    # Reto 6: Renombra las columnas (Corregido 'columns')
    df = df.rename(columns={
        'id_reg': 'ID', 
        'ts': 'Fecha', 
        'nin_id': 'Ninja', 
        'status': 'Estado', 
        'desc': 'Descripcion'
    })
    
    return df

# --- SECCIÓN 2: BÚSQUEDA Y CONSULTAS ---

def realizar_consultas(df):
    # Reto 7
    patron = 'espía|sospechoso|enemigo'
    sospechosos = df[df['Descripcion'].str.contains(patron, case=False, na=False)]
    print("Sospechosos:", len(sospechosos))

    # Reto 8
    ameelites = df[(df['aldea'] == 'amegakure') & (df['chakra'] > 5000) & (df['rango'] != 'D')]
    print("Elites_Amegakure:", len(ameelites))
    
    # Reto 9
    madrugada = df[(df['Fecha'].dt.hour >= 23) | (df['Fecha'].dt.hour < 5)]
    print("Accesos_Madrugada:", len(madrugada))
    
    # Reto 10
    topchakra = df.sort_values('chakra', ascending=False).groupby('aldea').head(5)
    print("Top_Chakra_Aldeas:\n", topchakra[['Ninja', 'aldea', 'chakra']])
    
    # Reto 11
    alianza = ['konoha', 'suna', 'kumo']
    fueraalianza = df[~df['aldea'].isin(alianza)]
    print("Fuera_Alianza:", len(fueraalianza))
    
    # Reto 12
    fallosporaldea = df[df['Estado'] == 'Fallo'].groupby('aldea').size()
    print("Fallos_Aldeas:\n", fallosporaldea)
    pass 
df_limpio = limpiar_registro(df)
realizar_consultas(df_limpio)
# Guardado final
df_limpio.to_csv('misiones_limpias_[Jairo].csv', index=False)

