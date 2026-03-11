from pymongo import MongoClient as MC

client = MC("mongodb://localhost:27017/")
db = client["BD_GrupoAlumno"]
Grupo = db["Grupo"]
Alumno = db["Alumno"]

cveGru = input("Escribe la clave del grupo a eliminar: ")
resultado = list(Grupo.find({"cveGru": cveGru}))
if len(resultado) == 0:
    print("El Grupo no Existe")
else:
    # Mostrar el grupo encontrado
    print("Grupo encontrado:")
    for grupo in resultado:
        print(grupo)

    borrados_alumnos = Alumno.delete_many({"grupo": cveGru})
    eliminado = Grupo.delete_one({"cveGru": cveGru})

    print(f"Se eliminó el grupo (eliminados: {eliminado.deleted_count})")
    print(f"Alumnos eliminados en cascada: {borrados_alumnos.deleted_count}")