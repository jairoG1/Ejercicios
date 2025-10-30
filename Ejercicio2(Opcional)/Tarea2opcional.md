### a) Crear un usuario (`POST /users`)

**Descripción:** Permite registrar un nuevo usuario con `username` y `name`.

**Código:**

```python
@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    with driver.session() as session:
        session.run(
            "CREATE (u:User {username: $username, name: $name})",
            username=data["username"],
            name=data["name"]
        )
    return jsonify({"status": "ok", "message": f"Usuario {data['username']} creado."})
```
### b) Crear un post (POST /posts)

**Descripción:** Permite que un usuario publique un post, creando un nodo Post relacionado con el usuario.

**Código:**
```python
@app.route("/posts", methods=["POST"])
def create_post():
    data = request.get_json()
    with driver.session() as session:
        session.run("""
            MATCH (u:User {username: $username})
            CREATE (u)-[:POSTED]->(:Post {id: randomUUID(), content: $content})
        """, username=data["username"], content=data["content"])
    return jsonify({"status": "ok", "message": f"Post creado por {data['username']}."})
```
### d) Ver usuarios que se siguen mutuamente (GET /mutuals)

**Descripción:** Recupera los pares de usuarios que se siguen entre sí, mostrando relaciones mutuas (FOLLOWS) en ambas direcciones.

**Código:**
```python
@app.route("/mutuals", methods=["GET"])
def mutual_follows():
    with driver.session() as session:
        result = session.run("""
            MATCH (a:User)-[:FOLLOWS]->(b:User),
                  (b)-[:FOLLOWS]->(a)
            RETURN a.username AS user1, b.username AS user2
        """)
        mutuals = [record.data() for record in result]
    return jsonify(mutuals)
```
### e) Interfaz web simple (HTML + JS)

**Descripción:** Permite interactuar con la API desde el navegador, crear usuarios, posts, listar posts y ver relaciones mutuas de manera visual. Los resultados se muestran en un panel <pre>.

**Código (index.html):**
```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Red Social Neo4j</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; }
    input, textarea { margin: 5px 0; width: 200px; display: block; }
    button { margin-bottom: 10px; }
    pre { background: #f0f0f0; padding: 10px; max-height: 300px; overflow: auto; }
  </style>
</head>
<body>
  <h1>Demo Red Social</h1>

  <h2>Crear usuario</h2>
  <input id="username" placeholder="Usuario">
  <input id="name" placeholder="Nombre">
  <button onclick="createUser()">Crear</button>

  <h2>Crear post</h2>
  <input id="userPost" placeholder="Usuario">
  <textarea id="content" placeholder="Contenido"></textarea>
  <button onclick="createPost()">Publicar</button>

  <h2>Listar posts</h2>
  <input id="userPosts" placeholder="Usuario">
  <button onclick="getPosts()">Ver posts</button>

  <h2>Ver relaciones mutuas</h2>
  <button onclick="getMutuals()">Mutuos</button>

  <h2>Todos los usuarios</h2>
  <button onclick="getUsers()">Usuarios</button>

  <pre id="output"></pre>

  <script>
    const out = document.getElementById("output");

    async function createUser() {
      const res = await fetch("/users", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username: username.value, name: name.value})
      });
      out.textContent = await res.text();
    }

    async function createPost() {
      const res = await fetch("/posts", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username: userPost.value, content: content.value})
      });
      out.textContent = await res.text();
    }

    async function getPosts() {
      const res = await fetch("/posts/" + userPosts.value);
      out.textContent = await res.text();
    }

    async function getMutuals() {
      const res = await fetch("/mutuals");
      out.textContent = await res.text();
    }

    async function getUsers() {
      const res = await fetch("/users");
      out.textContent = await res.text();
    }
  </script>
</body>
</html>
```

### Mini Tutorial: Cómo ejecutar la API y la interfaz web

## Ejecuta:
```python
python app.py
```

## Flask iniciará un servidor local en http://127.0.0.1:5000.

## Verás mensajes como:

 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

## Abrir la interfaz web

## Coloca index.html en la misma carpeta que app.py.

## Abre index.html en tu navegador.

## Usa los formularios y botones para interactuar con la API

