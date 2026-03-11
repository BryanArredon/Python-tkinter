from pymongo import MongoClient as MC

# Cadena de conexión local
client = MC("mongodb://localhost:27017/")

# Seleccionar la base de datos
db = client["BD_Escuela1"]

# Seleccionar la colección
coleccion = db["Materia"]

# Consultar documentos
for doc in coleccion.find():
    print(doc)
