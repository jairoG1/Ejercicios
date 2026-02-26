###### Jairo Guardado Aragón
## Práctica 3. Selección para la Gran Alianza
### Mapa de Especialidades Ninja
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea6.1.png)
### Metodo del Codo
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea6.png)

### Codigo
```python
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

df = pd.read_csv(r'C:\Users\jguardadoa01\Desktop\Justo\Segundo Trimestre\Ejercicio6\aptitudes_ninja.csv')
df = df.drop_duplicates().dropna()

X = df[['fuerza_fisica', 'control_chakra']]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

inercias = []
for k in range(1, 11):
    kmeans_codo = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans_codo.fit(X_scaled)
    inercias.append(kmeans_codo.inertia_)
plt.figure(figsize=(6, 4))
plt.plot(range(1, 11), inercias, marker='o', color='orange')
plt.title('Metodo del Codo')
plt.show() 


# se entrena con K=4 
k_elegido = 4
kmeans = KMeans(n_clusters=k_elegido, random_state=42, n_init=10)
df['clan_comportamiento'] = kmeans.fit_predict(X_scaled)

centroides = kmeans.cluster_centers_

plt.figure(figsize=(8, 6))
plt.scatter(X_scaled[:, 0], X_scaled[:, 1], c=df['clan_comportamiento'], cmap='viridis', alpha=0.6)
plt.scatter(centroides[:, 0], centroides[:, 1], c='red', marker='X', s=200, label='Centroides')
plt.title('Mapa de Especialidades Ninja')
plt.xlabel('Fuerza Fiisica')
plt.ylabel('Control de Chakra')
plt.legend()
plt.show() 

print("Análisis de Unidades Especializadas:")
print(df.groupby('clan_comportamiento')[['fuerza_fisica', 'control_chakra']].mean())
```
#### Conclusiones: Una breve explicación de por qué elegiste ese valor de K y qué representa cada grupo descubierto.
 he elegido la K=4 por que al representarlo lo probe de primeras con 3 de valor  y representaba 4 grupos entonces entendi que lo mejor para tener de valor de K seria tener 4.
 



