###### Jairo Guardado Aragón
# Ejercicios Neo4j
## Práctica 1. El Purificador de Pergaminos (ETL)
#### Configuración del Crawler: Crea un Crawler en AWS Glue que rastree la carpeta /raw. Ejecútalo para que cree la tabla inicial en el Data Catalog.
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea3.5.1.png)
#### Transformación: Añade un nodo de “Filter” o “Drop Fields” para eliminar columnas innecesarias o registros nulos.
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea6.1.1.png)
#### Target: Selecciona la carpeta /silver de tu bucket S3. Crucial: Cambia el formato de salida a Parquet.
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea7.1.1.png)
#### Ejecución y Monitoreo: Ejecuta el Job usando el LabRole. Observa en la pestaña “Runs” el tiempo de ejecución y los recursos consumidos (DPUs).
![Foto2](https://github.com/jairoG1/Ejercicios/blob/main/Fotos/Tarea8.1.1.png)

### ¿Qué ventajas crees que tiene este proceso “Serverless” frente a procesar el archivo con un script manual en tu PC?
La principal diferencia entre el procesamiento local y el modelo Serverless radica en la transición de una gestión basada en activos (tu hardware) a una gestión basada en eventos y resultados.

Escalabilidad Elástica: A diferencia de un PC, cuya capacidad de cómputo es finita y lineal, el modelo Serverless permite el procesamiento paralelo masivo. Si entran 500 archivos simultáneamente, la nube despliega 500 instancias de ejecución independientes, completando la tarea en una fracción del tiempo que requeriría un script manual.

Automatización Mediante Eventos: Se elimina la intervención humana. El proceso se activa automáticamente mediante "triggers" (disparadores), como la carga de un archivo a un repositorio en la nube, garantizando que el flujo de trabajo ocurra 24/7 sin depender de que un equipo local esté encendido o conectado.

Optimización de Recursos y Costos: Bajo el esquema de "pago por uso", solo se factura el tiempo exacto de ejecución (medido en milisegundos). Esto resulta mucho más eficiente que mantener infraestructura local o servidores encendidos en tiempos de inactividad.

Abstracción de la Infraestructura: El desarrollador se desentiende de la configuración del sistema operativo, las actualizaciones de seguridad o la gestión de dependencias. Esto permite que el enfoque técnico se centre exclusivamente en la lógica del código y no en el mantenimiento del entorno.