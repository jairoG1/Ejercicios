###### Jairo Guardado Aragón
# Ejercicios Neo4j
## Ejercicio 1: Diseño del Modelo de Datos de la Red Social
#### Usuarios:
```json
CREATE (:User {username: 'JairoG', name: 'Jairo',registration_date:'17/2/2003'})
```
```json
CREATE (:User {username: 'AnaM', name: 'Ana', registration_date: '25/11/2021'})
```
```json
CREATE (:User {username: 'LuisP', name: 'Luis', registration_date: '03/08/2018'})
```
```json
CREATE (:User {username: 'ElaraV', name: 'Elara', registration_date: '25/8/2021'})
```
#### Post:
```json
CREATE (:Post {content: 'Hola', timestamp: '30/11/2017'})
```
```json
CREATE (:Post {content: '¡Nuevo artículo en el blog!', timestamp: '15/05/2024'})
```
```json
CREATE (:Post {content: 'Echando un café en la oficina', timestamp: '01/01/2020'})
```
```json
CREATE (:Post {content: 'Adios', timestamp: '23/10/2025'})
```
### Relaciones:

#### Follows:
```json
CREATE (:User {username: 'JairoG', name: 'Jairo',registration_date:'17/2/2003'})-[:FOLLOWS]->(:User {username: 'ElaraV', name: 'Elara', registration_date: '25/8/2021'})
```
```json
CREATE (:User {username: 'JairoG', name: 'Jairo',registration_date:'17/2/2003'})-[:FOLLOWS]->(:User {username: 'LuisP', name: 'Luis', registration_date: '03/08/2018'})
```
```json
CREATE (:User {username: 'ElaraV', name: 'Elara', registration_date: '25/8/2021'})-[:FOLLOWS]->(:User {username: 'AnaM', name: 'Ana', registration_date: '25/11/2021'})
```
#### Posted:
```json
CREATE (:User {username: 'JairoG', name: 'Jairo',registration_date:'17/2/2003'})-[:POSTED]->(:Post {content: 'Adios', timestamp: '23/10/2025'})
```
```json
CREATE (:User {username: 'JairoG', name: 'Jairo',registration_date:'17/2/2003'})-[:POSTED]->(:Post {content: '¡Nuevo artículo en el blog!', timestamp: '15/05/2024'})
```
```json
CREATE (:User {username: 'AnaM', name: 'Ana', registration_date: '25/11/2021'})-[:POSTED]->(:Post {content: 'Adios', timestamp: '23/10/2025'})
```
#### Likes:
```json
CREATE (:User {username: 'JairoG', name: 'Jairo',registration_date:'17/2/2003'})-[:LIKES]->(:Post {content: 'Adios', timestamp: '23/10/2025'})
```
```json
CREATE (:User {username: 'AnaM', name: 'Ana', registration_date: '25/11/2021'})-[:LIKES]->(:Post {content: 'Adios', timestamp: '23/10/2025'})
```
```json
CREATE (:User {username: 'JairoG', name: 'Jairo',registration_date:'17/2/2003'})-[:LIKES]->(:Post {content: 'Echando un café en la oficina', timestamp: '01/01/2020'})
```

## Ejercicio 3: Encontrar Amigos y Seguidores
### 3.1 Encontrar todos los usuarios que un usuario específico sigue: 
```json
MATCH (a:User{username:'JairoG'})-[:FOLLOWS]->(p:User)
RETURN p.username
```
## 3.2 Encontrar todos los usuarios que siguen a un usuario específico: 
```json
MATCH (a:User)-[:FOLLOWS]->(p:User{username:'AnaM'})
RETURN a.username
```
## Ejercicio 4: Analizando Posts e Interacciones

### 4.1 Encontrar todos los posts de un usuario específico:
```json 
MATCH (a:User{username:'JairoG'})-[:POSTED]->(p:Post)
RETURN p.content
```
### 4.2 Encontrar los posts que un usuario ha dado “Like”: 
```json 
MATCH (a:User{username:'JairoG'})-[:LIKES]->(p:Post)
RETURN p.content
```


## Ejercicio 5: Explorando el Grafo Visualmente

### Arrastra nodos para reorganizar el grafo.
![Foto1](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea2.png)


### Haz doble clic en un nodo para expandir sus relaciones.
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea2.1.png)

### Usa el panel de estilos para cambiar colores y tamaños de nodos/relaciones.
![Foto3](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea2.2.png)