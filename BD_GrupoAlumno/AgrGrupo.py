from pymongo import MongoClient as MC 

client = MC("mongodb://localhost:27017/")

db=client["BD_GrupoAlumno"]

coleccion = db["Grupo"]

coleccion.insert_one({"_id": "GSI0533", "cveGru": "GSI0533", "nomGru": "Grupo de Sistemas"})
print("Grupo Se guardó correctamente")
print("Lista de Grupos")

for doc in coleccion.find():
    print(doc)