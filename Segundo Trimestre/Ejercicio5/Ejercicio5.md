###### Jairo Guardado Aragón
## Práctica 2. El Rostro del Traidor (Detección de Anomalías)
### El Ojo de la Verdad (Describe) Carga el CSV misiones_limpias.csv. Usa .describe() para obtener el perfil de un ninja promedio.
#### ¿Cuál es la media de chakra?
        ID            Nivel_Chakra        Misiones_Falladas
mean    500.500000    108.932353           0.936000
#### ¿Cuál es la desviación estándar?
        ID            Nivel_Chakra         Misiones_Falladas
std     288.819436    251.736859           0.982277
#### ¿Ves algún valor máximo sospechoso?
Si, si la media es 108.932353 el maximo es sospechosos ya que es 8000.000000 en el Nivel_chakra
### Caza Mayor (Ampliación) El Capitán Yamato sospecha que no es solo un infiltrado.
#### ¿Hay algún “Super Ninja” que sea fuerte (Z-Score entre 2 y 3) pero no llegue a ser un traidor (Z-Score > 3)? Identifícalos.
no ahi
### Interrogatorio Final Una vez aislados los IDs de los sospechosos, muestra todos sus datos.~
#### ¿Coincide el infiltrado de chakra alto con el de la aldea desconocida?
si
 ID        Aldea   Rango  Nivel_Chakra  Misiones_Falladas  Z_Score_Chakra   
 699     Desconocida  Chunin       8000.0       0           31.346493
## Preguntas de reflexión

### ¿Por qué un outlier puede ser un error del sensor y no necesariamente un ataque? Pon un ejemplo que hayas encontrado en el dataset.   
Por que un dato que sobresalga de lo normal nos puede pergudicar a la hora de calcular la media o la desviacion 

### Si eliminas los outliers, ¿cómo cambia la media del dataset? ¿Sube o baja?
Bajara, ya que tenemos valoremos muy altos como 8000 que es muy alto en comparacion con la media de 100


### ¿Sería justo castigar a los “Super Ninjas” (Z-Score > 2 pero < 3) solo por ser fuertes? Justifica tu respuesta estadística.
yo creo que no seria justo , ya que veo una distribucion normal entr 2 y 3 pero no imposible ya que el infiltrado