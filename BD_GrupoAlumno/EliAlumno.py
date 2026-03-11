from pymongo import MongoClient as MC

#Configuracion de la conexion a la base de datos

client = MC("mongodb://localhost:27017/")
db = client["BD_GrupoAlumno"]
Alumno = db["Alumno"] 


cveAlu = input("Escribe la clave del alumno a eliminar: ")
resultado = list(Alumno.find({"cveAlu": cveAlu}))
if len(resultado) == 0:
    print("El Alumno no Existe")
else:
    # Mostrar el alumno encontrado
    print("Alumno encontrado:")
    for alumno in resultado:
        print(alumno)

    eliminado = Alumno.delete_one({"cveAlu": cveAlu})
    print(f"Se eliminó el alumno (eliminados: {eliminado.deleted_count})")