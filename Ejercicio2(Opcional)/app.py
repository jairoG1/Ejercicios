from flask import Flask, jsonify, request, send_from_directory
from neo4j import GraphDatabase
import os

app = Flask(__name__)


uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "Jairo2003"))




@app.route("/users", methods=["GET"])
def get_users():
    with driver.session() as session:
        result = session.run("MATCH (u:User) RETURN u.username AS username, u.name AS name")
        users = [record.data() for record in result]
    return jsonify(users)


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



@app.route("/follow", methods=["POST"])
def follow_user():
    data = request.get_json()
    with driver.session() as session:
        session.run("""
            MATCH (a:User {username: $1}), (b:User {username: $2})
            MERGE (a)-[:FOLLOWS]->(b)
        """, data["from"],data["to"])
    return jsonify({"status": "ok", "message": f"{data['from']} ahora sigue a {data['to']}."})




@app.route("/posts", methods=["POST"])
def create_post():
    data = request.get_json()
    with driver.session() as session:
        session.run("""
            MATCH (u:User {username: $username})
            CREATE (u)-[:POSTED]->(:Post {id: randomUUID(), content: $content})
        """, username=data["username"], content=data["content"])
    return jsonify({"status": "ok", "message": f"Post creado por {data['username']}."})


@app.route("/posts/<username>", methods=["GET"])
def get_user_posts(username):
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {username: $username})-[:POSTED]->(p:Post)
            RETURN p.content AS content, p.id AS id
        """, username=username)
        posts = [record.data() for record in result]
    return jsonify(posts)




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




@app.route("/")
def serve_frontend():
    return send_from_directory(os.getcwd(), "index.html")


if __name__ == "__main__":
    app.run(debug=True)
