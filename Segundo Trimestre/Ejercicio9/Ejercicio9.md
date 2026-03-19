###### Jairo Guardado Aragón
# Ejercicios Neo4j
## Tarea Consultas
#### select * from "misiones" limit 10
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea4.1.5.png)
#### CREATE TABLE misiones_okWITH (format = 'PARQUET',external_location = 's3://anbu-data-lake-guardado-misiones/gold/') ASSELECTid_reg,CAST(ts AS timestamp) AS ts,nin_idaldea TRY_CAST(chakra AS double) AS chakra,CAST(rango AS varchar(1)) AS rango,status, "desc" AS descripcion FROM misiones;
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea4.1.6.png)
#### SELECT *FROM "misiones_ok"limit 10;
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea4.1.7.png)
### Consultas:

#### 1. Número de misiones realizadas por cada ninja
```sql
SELECT nin_id, COUNT(*) AS total_misiones FROM misiones_ok GROUP BY nin_id;
```
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea4.1.8.png)

#### 2. Misiones completadas con éxito
```sql
SELECT * FROM misiones_ok WHERE status = 'Éxito';
```
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea4.1.9.png)

#### 3. Chakra medio usado por cada ninja
```sql
SELECT nin_id, AVG(chakra) AS chakra_medio FROM misiones_ok GROUP BY nin_id;
```
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea4.1.10.png)

#### 4. Número de misiones por aldea
```sql
SELECT aldea, COUNT(*) AS misiones_por_aldea FROM misiones_ok GROUP BY aldea;
```
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea4.1.11.png)

#### 5. Misiones de rango alto (A o S)
```sql
SELECT *FROM misiones_ok WHERE rango IN ('A', 'S');
```
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea4.1.12.png)

#### 6. Realiza un GROUP BY para encontrar qué aldea ha realizado más actividades sospechosas en el último mes
```sql
SELECT 
    aldea, 
    COUNT(*) AS total_sospechosas
FROM misiones_ok
WHERE status = 'Sospechoso' 
  AND ts >= TIMESTAMP '2025-02-01 00:00:00' 
GROUP BY aldea
ORDER BY total_sospechosas DESC
LIMIT 1;
```
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea4.1.14.png)



