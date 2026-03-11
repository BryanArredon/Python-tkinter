from pymongo import MongoClient as MC

client = MC("mongodb://localhost:27017/")
db = client["BD_GrupoAlumno"]

# colecciones
Grupo = db["Grupo"]
Alumno = db["Alumno"]


def mostrar_todos():
    print("Lista de Grupos")
    for g in Grupo.find():
        print(g)

    print("\n Lista de Alumnos")
    for a in Alumno.find():
        print(a)


if __name__ == "__main__":
    mostrar_todos()
