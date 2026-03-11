from pymongo import MongoClient as MC 

client = MC("mongodb://localhost:27017/")

db=client["BD_GrupoAlumno"]

Materias = db["Alumno"]

cveAlu = input("Escribe la clave del alumno: ")
resultado = list(Materias.find({"cveAlu":cveAlu}))

if(len(resultado)==0):
    print("El Alumno no Existe")
else: 
    for alumno in resultado:
        print(alumno)