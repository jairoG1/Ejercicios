import requests 
import time
import pandas as pd

url_inicial = "https://pokeapi.co/api/v2/pokemon?limit=100" 
todos_los_pokemon_resumen = []


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


# Si quieres limitar cambia usted el numero
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

# pasamos a  a DataFrame 
df = pd.DataFrame(datos_finales)
df['height_m'] = df['height'] / 10
df['weight_kg'] = df['weight'] / 10
df['bmi'] = df['weight_kg'] / (df['height_m'] ** 2)
df['bmi'] = df['bmi'].round(2)

# Guardar en CSV
df.to_csv("pokemon2.csv", index=False)
# guardar a json
df.to_json("pokemon3.json", orient='records',indent=2)

print(df.head()) 
