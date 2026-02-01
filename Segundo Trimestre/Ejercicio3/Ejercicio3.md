###### Jairo Guardado Aragón
## Práctica 3: Extracción de datos en CoinMarketCap

### Objetivo
#### Debes desarrollar un script en Python que realice las siguientes tareas:

* Extracción masiva: Obtener los datos de las 500 primeras criptomonedas (esto implicará navegar por varias páginas de resultados).
* Campos obligatorios: Por cada moneda, debes extraer:
Nombre del activo.
Símbolo (ej. BTC, ETH).
Precio actual.
Market Cap (Capitalización de mercado).
Volumen de las últimas 24 horas.
* Almacenamiento: Guardar los resultados en un archivo cripto_data.csv utilizando la librería pandas.

#### Paso a Paso
#### 1. La estructura de la tabla
```python
filas = soup.select('table.cmc-table tbody tr')
celdas = fila.find_all('td')
```
#### 2. Identificación por selectores CSS
```python
ranking = celdas[1].text.strip()
nombre = celdas[2].find('p', class_='coin-item-name').text.strip()
simbolo = celdas[2].find('p', class_='coin-item-symbol').text.strip()
```
#### 3. Gestión de la paginación
```python
for pagina in range(1, 35):
    url = f"{base_url}?page={pagina}"

    time.sleep(2)
```
#### 4. Cabeceras de navegación (User-Agent)
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

response = requests.get(url, headers=headers, timeout=15)
```
#### 5. Limpieza de datos
```python
precio_raw = celdas[3].text
precio_limpio = precio_raw.replace('$', '').replace(',', '').strip()
precio_final = float(precio_limpio)
```
## Codigo completo
```python
import requests
from bs4 import BeautifulSoup
import time
import csv

# El User-Agent es para que la web se piense que somos un navegador y no nos eche
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

base_url = "https://coinmarketcap.com/"
datos_totales = []

print("Iniciando la extracción de datos...")

# Recorremos las páginas (pongo hasta 35 para asegurar que llegamos a las 500 monedas)
for pagina in range(1, 35):
    url = f"{base_url}?page={pagina}"
    print(f"Leyendo página {pagina}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Buscamos la tabla y luego todas las filas (tr)
            filas = soup.select('table.cmc-table tbody tr')

            for fila in filas:
                try:
                    # Sacamos todas las celdas de la fila
                    celdas = fila.find_all('td')
                    if len(celdas) > 3:
                        ranking = celdas[1].text.strip()
                        nombre = celdas[2].find('p', class_='coin-item-name').text.strip()
                        simbolo = celdas[2].find('p', class_='coin-item-symbol').text.strip()
                        # Limpiamos el precio: quitamos el $ y las comas para poder pasarlo a número
                        precio_raw = celdas[3].text
                        precio_limpio = precio_raw.replace('$', '').replace(',', '').strip()
                        precio_final = float(precio_limpio)
                        
                        datos_totales.append({
                            'Ranking': ranking,
                            'Nombre': nombre,
                            'Símbolo': simbolo,
                            'Precio (USD)': precio_final
                        })
                except (AttributeError, ValueError, IndexError):
                    continue
        else:
            print(f"Error al acceder a la página {pagina}: Código {response.status_code}")
            
    except Exception as e:
        print(f"Error de conexión: {e}")
        break
# Esperamos 2 segundos entre páginas para que no nos baneen la IP
    time.sleep(2)

nombre_archivo = "top_500moneditas.csv"
# Si hemos conseguido datos, pues lo guardamos en un CSV
if datos_totales:
    columnas = ['Ranking', 'Nombre', 'Símbolo', 'Precio (USD)']
    
    try:
        with open(nombre_archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columnas)
            writer.writeheader()
            # Guardamos solo los primeros 500 aunque hayamos bajado más
            writer.writerows(datos_totales[:500])
            
        print(f"\nÉxito: Se ha generado el archivo '{nombre_archivo}' con {len(datos_totales[:500])} registros.")
    except IOError as e:
        print(f"Error al escribir el archivo CSV: {e}")
else:
    print("No se extrajeron datos. Revisa la conexión o los selectores HTML.")
```