from pymongo import MongoClient as MC

client = MC("mongodb://localhost:27017/")
db=client["BD_GrupoAlumno"]
Grupo = db["Grupo"]

cveGru = input("Escribe la clave del grupo: ")
resultado = list(Grupo.find({"cveGru":cveGru})) 

if(len(resultado)==0):
    print("El Grupo no Existe")
else: 
    for grupo in resultado:
        print(grupo)