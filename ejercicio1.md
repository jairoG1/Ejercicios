###### Jairo Guardado Aragón
# Ejercicios 
## Ejercicio 1

```json
{categoria:"Portátiles",marca:"TecnoÁgora Devices","especificaciones.ram":{$gt:8}}
```

## Ejercicio 2
```json
{tags:"oferta"}
```
## Ejercicio 3
```json
db["Producto"].updateOne({nombre:"Portátil Pro-Book X1"},{$inc:{stock:10}})
```
## Ejercicio 4

```json
db["Producto"].updateOne({ nombre: "Portátil Pro-Book X1" },{
$push: {reviews: {usuario: "Jairo",puntuacion: 2,comentario: "Excelente rendimiento, muy rápido."}}})
```
## Ejercicio 3
```json
db.productos.aggregate([{
    $unwind: "$reviews"
  },{
    $group: {
      _id: "$_id",
      nombre: { $first: "$nombre" },
      puntuacionMedia: { $avg: "$reviews.puntuacion" }
    }},{
    $sort: { puntuacionMedia: -1 }}])
```
# Ejercicios Opcionales
## Ejercicio 1
```json
{stock :{$lt:5}}
```
## Ejercicio 2
```json
db["Producto"].find({},{nombre: 1, precio: 1, _id: 0})
```
## Ejercicio 3
```json
db["Producto"].deleteOne({_id: "SKU-001"})
```
