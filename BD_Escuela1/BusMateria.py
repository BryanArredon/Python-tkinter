from pymongo import MongoClient as MC 

client = MC("mongodb://localhost:27017/")

db=client["BD_Escuela1"]

Materias = db["Materia"]

for materia in Materias.find({"cveMat":"6000"}):
    print(materia)

print("=====Buscar Materia=====")
cveMat = input("Introduce la clave de la materia : ")
for materia in Materias.find({"cveMat": cveMat}):
    print(materia)
