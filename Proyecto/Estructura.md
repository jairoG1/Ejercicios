## Estructura de Tablas DynamoDB

---

### **1. TABLA PRINCIPAL: Reservas**
**Claves:**  
- **PK:** `RESERVA#FECHA#ID`  
- **SK:** `METADATOS`

**Campos principales:**
- idReserva  
- idCliente  
- nombreCliente  
- tipoServicio (HOTEL / LIMPIEZA)  
- numeroHabitacion  
- piso  
- fechaInicio  
- fechaFin  
- horaCheckIn  
- horaCheckOut  
- estado (PENDIENTE / CONFIRMADA / COMPLETADA / CANCELADA)  
- estadoPago  
- montoTotal  
- limpiadoresAsignados  
- peticionesEspeciales  
- prioridad  

---

### **2. TABLA: Clientes**
**Claves:**  
- **PK:** `CLIENTE#ID`  
- **SK:** `PERFIL`

**Campos principales:**
- nombre  
- email  
- telefono  
- idioma  
- productosLimpieza  
- tipoHabitacion  
- reservasTotales  
- gastoTotal  
- nivelFidelidad (BRONCE / PLATA / ORO / PLATINO)  
- metodosPago (encriptado)

---

### **3. TABLA: PersonalLimpieza**
**Claves:**  
- **PK:** `LIMPIADOR#ID`  
- **SK:** `PERFIL`

**Campos principales:**
- puesto  
- departamento  
- fechaContratacion  
- especialidades  
- horarioTrabajo  
- zonaAsignada  
- estadoActual (DISPONIBLE / ASIGNADO / FUERA_DE_SERVICIO)  
- asignacionesTotales  
- calificacionPromedio  

---

### **4. TABLA: Habitaciones**
**Claves:**  
- **PK:** `HABITACION#NUMERO`  
- **SK:** `CONFIGURACION`

**Campos principales:**
- numeroHabitacion  
- piso  
- edificio  
- zona  
- tipoHabitacion (INDIVIDUAL / DOBLE / SUITE)  
- estadoActual (DISPONIBLE / OCUPADA / LIMPIANDOSE)  
- ultimaLimpieza  
- proximaLimpiezaProgramada  
- duracionLimpieza  
- comodidades  
- insumosLimpiezaNecesarios  

---

### **5. TABLA: AsignacionesLimpieza**
**Claves:**  
- **PK:** `ASIGNACION#FECHA`  
- **SK:** `LIMPIADOR#RESERVA`

**Campos principales:**
- idLimpiador  
- idReserva  
- idHabitacion  
- tipoTarea (LIMPIEZA_CHECKOUT / ESTANCIA / LIMPIEZA_PROFUNDA)  
- inicioProgramado  
- finProgramado  
- inicioReal  
- finReal  
- estado (PROGRAMADA / EN_PROGRESO / COMPLETADA)  
- puntuacionCalidad  
- listaVerificacion  
- problemasDetectados  
- notas  

---

### **6. TABLA: AgendaLimpieza**
**Claves:**  
- **PK:** `AGENDA#FECHA`  
- **SK:** `ZONA#HORA`

**Campos principales:**
- fecha  
- zona  
- franjaHoraria  
- limpiadoresAsignados  
- habitacionesAsignadas  
- habitacionesEstimadasPorHora  
- habitacionesPrioritarias  
- estado  
- progreso  
- notas  

# Relaciones entre Tablas del Sistema de Reservas

A continuación se muestran las relaciones lógicas entre las tablas del sistema, adaptadas al modelo DynamoDB.

---

## 1. Reservas ↔ Clientes
**Tipo de relación:** Muchos a uno (N:1)

- Un cliente puede tener muchas reservas.  
- Una reserva pertenece a un solo cliente.

**Campos relacionados:**
- `Reservas.idCliente`
- `Clientes.PK = CLIENTE#ID`

---

## 2. Reservas ↔ Habitaciones
**Tipo de relación:** Muchos a uno (N:1)

- Una reserva corresponde a una habitación.  
- Una habitación puede tener muchas reservas en el tiempo.

**Campos relacionados:**
- `Reservas.numeroHabitacion`
- `Habitaciones.PK = HABITACION#NUMERO`

---

## 3. Reservas ↔ Personal de Limpieza (Asignaciones)
**Tipo de relación:** Muchos a muchos (N:M)

- Una reserva puede tener varios limpiadores asignados.  
- Un limpiador puede trabajar en varias reservas.

**Tabla intermediaria:** `AsignacionesLimpieza`

**Campos relacionados:**
- `Reservas.idReserva`
- `PersonalLimpieza.idLimpiador`
- `AsignacionesLimpieza.idReserva`
- `AsignacionesLimpieza.idLimpiador`

---

## 4. Personal de Limpieza ↔ Agenda de Limpieza
**Tipo de relación:** Muchos a muchos (N:M)

- Una franja de agenda puede incluir varios limpiadores.  
- Un limpiador puede estar asignado a múltiples franjas de limpieza.

**Campos relacionados:**
- `AgendaLimpieza.limpiadoresAsignados[]`
- `PersonalLimpieza.PK = LIMPIADOR#ID`

---

## 5. Habitaciones ↔ Agenda de Limpieza
**Tipo de relación:** Muchos a muchos (N:M)

- Una franja de limpieza puede incluir varias habitaciones.  
- Una habitación puede estar programada para diferentes días y franjas.

**Campos relacionados:**
- `AgendaLimpieza.habitacionesAsignadas[]`
- `Habitaciones.PK = HABITACION#NUMERO`

---

## 6. Habitaciones ↔ Asignaciones de Limpieza
**Tipo de relación:** Uno a muchos (1:N)

- Una habitación puede tener múltiples registros de asignaciones de limpieza.  
- Cada asignación corresponde a una habitación específica.

**Campos relacionados:**
- `AsignacionesLimpieza.idHabitacion`
- `Habitaciones.PK = HABITACION#NUMERO`

---

## 7. Clientes ↔ Asignaciones de Limpieza (relación indirecta)
**Tipo de relación:** Indirecta a través de Reservas

- Un cliente → muchas reservas → muchas asignaciones de limpieza.

**Ruta:**
`Clientes → Reservas → AsignacionesLimpieza`


## Resumen Visual de Relaciones

- **Clientes** (1) — (N) **Reservas**  
- **Habitaciones** (1) — (N) **Reservas**  
- **Reservas** (N) — (M) **PersonalLimpieza** *(vía AsignacionesLimpieza)*  
- **PersonalLimpieza** (N) — (M) **AgendaLimpieza**  
- **Habitaciones** (N) — (M) **AgendaLimpieza**  
- **Habitaciones** (1) — (N) **AsignacionesLimpieza**

---
