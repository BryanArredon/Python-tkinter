from pymongo import MongoClient as MC 

client = MC("mongodb://localhost:27017/")

db=client["BD_Escuela1"]

coleccion = db["Materia"]

#Insertar un documento 
coleccion.insert_one({"cveMat":"6000","nomMat":"IOT"})
print("Materia Insertada")
print("Lista de Materias")

#Consultar documentos
for doc in col	eccion.find():
    print(doc)
