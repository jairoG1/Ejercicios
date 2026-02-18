import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv(r'C:\Users\Jairo\Desktop\Ejercicio5\misiones_limpias.csv')
print(df.describe())

# Jutsu de Visualización (Boxplot)
plt.figure(figsize=(8, 6))
sns.boxplot(y=df["Nivel_Chakra"], color='orange')
plt.title('Torneo de Puntería: Nivel de Chakra (cm)')
plt.show()

# La Regla de los 3 Sigmas (Z-Score)
df['Z_Score_Chakra'] = (df['Nivel_Chakra'] - df['Nivel_Chakra'].mean()) / df['Nivel_Chakra'].std()
traidores = df[(df['Z_Score_Chakra'] > 3) | (df['Z_Score_Chakra'] < -3)]
print(traidores)

superningas = df[(df['Z_Score_Chakra'] >= 2) & (df['Z_Score_Chakra'] <= 3)]
print(superningas)
# Caza Mayor (Ampliación)
condicnegativa = df['Nivel_Chakra'] < 0
condicifesconocida = df['Aldea'] == 'Desconocida'
ea = df[condicnegativa | condicifesconocida]

print(ea)