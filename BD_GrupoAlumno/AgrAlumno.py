from pymongo import MongoClient as MC 

client = MC("mongodb://localhost:27017/")

db=client["BD_GrupoAlumno"]

coleccion = db["Alumno"]

coleccion.insert_one({"_id": "8000", "cveAlu": "8000", 
                      "nomAlu": "Juan Perez", "edad": 20, "grupo": "GSI0533"})
print("Alumno Se guardó correctamente")
print("Lista de Alumnos")

for doc in coleccion.find():
    print(doc)