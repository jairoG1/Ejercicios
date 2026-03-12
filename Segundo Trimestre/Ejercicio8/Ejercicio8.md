###### Jairo Guardado Aragón
# Ejercicios Neo4j
## Práctica 2. El Índice de las Sombras (NoSQL)
#### Creación de la Tabla Principal.
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea9.1.png)
#### Ingesta de Dados Críticos:
##### Codigo creacion ninjas
```python
{
  "ID_Ninja": { "S": "N001" },
  "Fecha_Registro": { "N": "20260312" },
  "Nombre": { "S": "Naruto Uzumaki" },
  "Clan": { "S": "Uzumaki" },
  "Rango": { "S": "Hokage" }
}
```
```python
{
  "ID_Ninja": { "S": "N002" },
  "Fecha_Registro": { "N": "20260312" },
  "Nombre": { "S": "Sasuke Uchiha" },
  "Habilidades_Especiales": { "L": [ { "S": "Sharingan" }, { "S": "Rinnegan" } ] },
  "Herramientas": { "M": { "Espada": { "S": "Kusanagi" }, "Sellos": { "N": "15" } } }
}
```
```python
{
  "ID_Ninja": { "S": "N003" },
  "Fecha_Registro": { "N": "20260312" },
  "Nombre": { "S": "Sakura Haruno" },
  "Estado_Ultima_Mision": { "S": "Completada" },
  "Especialidad": { "S": "Medicina Ninja" }
}
```
```python
{
  "ID_Ninja": { "S": "N004" },
  "Fecha_Registro": { "N": "20260312" },
  "Nombre": { "S": "Shikamaru Nara" },
  "IQ": { "N": "200" },
  "Activo": { "BOOL": true }
}
```
```python
{
  "ID_Ninja": { "S": "N005" },
  "Fecha_Registro": { "N": "20260312" },
  "Nombre": { "S": "Kakashi Hatake" },
  "Misiones_S": { "N": "42" },
  "Alias": { "S": "Ninja que copia" }
}
```
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea9.2.png)
#### Simulación de Búsqueda ANBU:
##### Una Query buscando por un ID_Ninja específico (mira la velocidad).
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea9.3.png)
##### Un Scan buscando a todos los ninjas de un “Clan” específico. Reflexiona: ¿Por qué el Scan es mucho más lento y costoso que la Query?
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea9.4.png)
### ¿Actualización Dinámica: 
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea9.5.png)

