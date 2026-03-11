from pymongo import MongoClient as MC 

client = MC("mongodb://localhost:27017/")

db=client["BD_Escuela1"]

Materias = db["Materia"]

cveMat = input("Escribe la clave de la materia: ")
resultado = list(Materias.find({"cveMat":cveMat}))

if(len(resultado)==0):
    print("La Materia no Existe")
else: 
    for materia in resultado:
        print(materia)

