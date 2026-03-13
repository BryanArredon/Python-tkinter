import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from pymongo import MongoClient as MC
from pydantic import BaseModel, field_validator, ValidationError
import csv
import json
import xml.etree.ElementTree as ET
import os


# ---------- CONEXION MONGO ----------

client = MC("mongodb://localhost:27017/")
db = client["BD_GrupoAlumno"]
coleccion = db["Alumno"]


# ---------- MODELO ----------

class AlumnoModelo(BaseModel):

    cveAlu:int
    nomAlu:str
    edaAlu:int
    cveGru:str

    @field_validator('nomAlu','cveGru')
    @classmethod
    def validar_vacio(cls,v):
        if not str(v).strip():
            raise ValueError("Campo requerido")
        return v

    @field_validator('edaAlu')
    @classmethod
    def validar_edad(cls,v):
        if v <= 0:
            raise ValueError("Edad inválida")
        return v


# ---------- FUNCIONES ----------

def limpiar_campos():

    input_cveAlu.config(state="normal")

    input_cveAlu.delete(0,tk.END)
    input_nomAlu.delete(0,tk.END)
    input_edaAlu.delete(0,tk.END)
    input_cveGru.delete(0,tk.END)

    btn_Guardar.config(state="normal")
    btn_Actualizar.config(state="disabled")


def cargar_datos():

    for item in tabla.get_children():
        tabla.delete(item)

    registros = coleccion.find()

    for r in registros:

        tabla.insert(
            "",
            tk.END,
            values=(r["cveAlu"],r["nomAlu"],r["edaAlu"],r["cveGru"])
        )


# ---------- GUARDAR ----------

def guardar_datos():

    try:

        datos = AlumnoModelo(
            cveAlu=int(input_cveAlu.get()),
            nomAlu=input_nomAlu.get(),
            edaAlu=int(input_edaAlu.get()),
            cveGru=input_cveGru.get()
        )

        if coleccion.find_one({"cveAlu":datos.cveAlu}):
            messagebox.showwarning("Advertencia","La clave ya existe")
            return

        coleccion.insert_one(datos.model_dump())

        messagebox.showinfo("Éxito","Alumno guardado")

        limpiar_campos()
        cargar_datos()

    except ValidationError as e:

        errores = "\n".join(
            [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
        )

        messagebox.showerror("Validación",errores)


# ---------- SELECCIONAR ----------

def seleccionar_registro(event):

    seleccion = tabla.focus()

    if seleccion:

        valores = tabla.item(seleccion,"values")

        limpiar_campos()

        input_cveAlu.insert(0,valores[0])
        input_cveAlu.config(state="disabled")

        input_nomAlu.insert(0,valores[1])
        input_edaAlu.insert(0,valores[2])
        input_cveGru.insert(0,valores[3])

        btn_Guardar.config(state="disabled")
        btn_Actualizar.config(state="normal")


# ---------- ACTUALIZAR ----------

def actualizar_datos():

    try:

        datos = AlumnoModelo(
            cveAlu=int(input_cveAlu.get()),
            nomAlu=input_nomAlu.get(),
            edaAlu=int(input_edaAlu.get()),
            cveGru=input_cveGru.get()
        )

        coleccion.update_one(
            {"cveAlu":datos.cveAlu},
            {"$set":{
                "nomAlu":datos.nomAlu,
                "edaAlu":datos.edaAlu,
                "cveGru":datos.cveGru
            }}
        )

        messagebox.showinfo("Éxito","Alumno actualizado")

        limpiar_campos()
        cargar_datos()

    except:
        messagebox.showerror("Error","Datos inválidos")


# ---------- ELIMINAR ----------

def eliminar_datos():

    seleccion = tabla.focus()

    if not seleccion:
        messagebox.showwarning("Advertencia","Seleccione un registro")
        return

    valores = tabla.item(seleccion,"values")

    coleccion.delete_one({"cveAlu":int(valores[0])})

    cargar_datos()

    messagebox.showinfo("Éxito","Alumno eliminado")


# ---------- BUSCAR ----------

def buscar_alumno():

    try:

        clave = int(input_cveAlu.get())

        resultado = coleccion.find_one({"cveAlu":clave})

        if resultado:

            limpiar_campos()

            input_cveAlu.insert(0,resultado["cveAlu"])
            input_cveAlu.config(state="disabled")

            input_nomAlu.insert(0,resultado["nomAlu"])
            input_edaAlu.insert(0,resultado["edaAlu"])
            input_cveGru.insert(0,resultado["cveGru"])

            btn_Guardar.config(state="disabled")
            btn_Actualizar.config(state="normal")

        else:
            messagebox.showwarning("Aviso","Alumno no encontrado")

    except:
        messagebox.showerror("Error","Clave inválida")


# ---------- EXPORTAR ----------

def exportar_json():

    archivo = filedialog.asksaveasfilename(defaultextension=".json")
    if not archivo: return

    datos = list(coleccion.find({},{"_id":0}))

    with open(archivo,"w",encoding="utf-8") as f:
        json.dump(datos,f,indent=4)

    messagebox.showinfo("Éxito","Exportado a JSON")


def exportar_csv():

    archivo = filedialog.asksaveasfilename(defaultextension=".csv")
    if not archivo: return

    datos = list(coleccion.find({},{"_id":0}))

    with open(archivo,"w",newline="",encoding="utf-8") as f:

        writer = csv.DictWriter(f,fieldnames=["cveAlu","nomAlu","edaAlu","cveGru"])
        writer.writeheader()
        writer.writerows(datos)

    messagebox.showinfo("Éxito","Exportado a CSV")


def exportar_xml():

    archivo = filedialog.asksaveasfilename(defaultextension=".xml")
    if not archivo: return

    datos = list(coleccion.find({},{"_id":0}))

    root = ET.Element("alumnos")

    for d in datos:

        alumno = ET.SubElement(root,"alumno")

        for k,v in d.items():

            campo = ET.SubElement(alumno,k)
            campo.text = str(v)

    tree = ET.ElementTree(root)
    tree.write(archivo,encoding="utf-8",xml_declaration=True)

    messagebox.showinfo("Éxito","Exportado a XML")


# ---------- IMPORTAR ----------

def importar_json():

    archivo = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
    if not archivo: return

    with open(archivo,"r",encoding="utf-8") as f:
        datos = json.load(f)

    coleccion.insert_many(datos)

    cargar_datos()

    messagebox.showinfo("Éxito","Importado JSON")


def importar_csv():

    archivo = filedialog.askopenfilename(filetypes=[("CSV","*.csv")])
    if not archivo: return

    datos = []

    with open(archivo,"r",encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:

            datos.append({
                "cveAlu": int(row["cveAlu"]),
                "nomAlu": row["nomAlu"],
                "edaAlu": int(row["edaAlu"]),
                "cveGru": row["cveGru"]
            })

    coleccion.insert_many(datos)

    cargar_datos()

    messagebox.showinfo("Éxito","Importado CSV")


def importar_xml():

    archivo = filedialog.askopenfilename(filetypes=[("XML","*.xml")])
    if not archivo: return

    tree = ET.parse(archivo)
    root = tree.getroot()

    datos = []

    for alumno in root.findall("alumno"):

        datos.append({
            "cveAlu": int(alumno.find("cveAlu").text),
            "nomAlu": alumno.find("nomAlu").text,
            "edaAlu": int(alumno.find("edaAlu").text),
            "cveGru": alumno.find("cveGru").text
        })

    coleccion.insert_many(datos)

    cargar_datos()

    messagebox.showinfo("Éxito","Importado XML")


# ---------- BACKUP ----------

def crear_backup():

    if not os.path.exists("backups"):
        os.makedirs("backups")

    archivo = "backups/backup_alumnos.json"

    datos = list(coleccion.find({},{"_id":0}))

    with open(archivo,"w",encoding="utf-8") as f:
        json.dump(datos,f,indent=4)

    messagebox.showinfo("Backup","Backup creado")


def ejecutar_backup():

    archivo = "backups/backup_alumnos.json"

    if not os.path.exists(archivo):
        messagebox.showwarning("Error","No existe backup")
        return

    with open(archivo,"r",encoding="utf-8") as f:
        datos = json.load(f)

    coleccion.delete_many({})
    coleccion.insert_many(datos)

    cargar_datos()

    messagebox.showinfo("Backup","Backup restaurado")


def eliminar_todos():

    confirmacion = messagebox.askyesno(
        "Confirmar",
        "¿Seguro que quieres eliminar TODOS los alumnos?"
    )

    if confirmacion:

        coleccion.delete_many({})

        cargar_datos()

        messagebox.showinfo("Éxito","Todos los alumnos fueron eliminados")


# ---------- INTERFAZ ----------

ventana = tk.Tk()
ventana.title("Sistema de Administración de Alumnos")
ventana.geometry("800x700")


titulo = tk.Label(
    ventana,
    text="Administración de Alumnos",
    font=("Arial",18,"bold")
)

titulo.pack(pady=10)


frame_form = tk.LabelFrame(ventana,text="Datos del Alumno",padx=20,pady=20)
frame_form.pack(pady=10,fill="x",padx=20)


tk.Label(frame_form,text="Clave Alumno").grid(row=0,column=0,padx=10,pady=5)
input_cveAlu = tk.Entry(frame_form,width=30)
input_cveAlu.grid(row=0,column=1,padx=10,pady=5)


tk.Label(frame_form,text="Nombre").grid(row=1,column=0,padx=10,pady=5)
input_nomAlu = tk.Entry(frame_form,width=30)
input_nomAlu.grid(row=1,column=1,padx=10,pady=5)


tk.Label(frame_form,text="Edad").grid(row=2,column=0,padx=10,pady=5)
input_edaAlu = tk.Entry(frame_form,width=30)
input_edaAlu.grid(row=2,column=1,padx=10,pady=5)


tk.Label(frame_form,text="Clave Grupo").grid(row=3,column=0,padx=10,pady=5)
input_cveGru = tk.Entry(frame_form,width=30)
input_cveGru.grid(row=3,column=1,padx=10,pady=5)


frame_botones = tk.LabelFrame(ventana,text="Operaciones")
frame_botones.pack(pady=10,fill="x",padx=20)


btn_Guardar = tk.Button(frame_botones,text="Guardar",width=12,command=guardar_datos)
btn_Guardar.grid(row=0,column=0,padx=5,pady=5)

btn_Actualizar = tk.Button(frame_botones,text="Modificar",width=12,command=actualizar_datos,state="disabled")
btn_Actualizar.grid(row=0,column=1,padx=5,pady=5)

btn_Eliminar = tk.Button(frame_botones,text="Eliminar",width=12,command=eliminar_datos)
btn_Eliminar.grid(row=0,column=2,padx=5,pady=5)

btn_Buscar = tk.Button(frame_botones,text="Buscar",width=12,command=buscar_alumno)
btn_Buscar.grid(row=0,column=3,padx=5,pady=5)

btn_Limpiar = tk.Button(frame_botones,text="Limpiar",width=12,command=limpiar_campos)
btn_Limpiar.grid(row=0,column=4,padx=5,pady=5)

btn_EliminarTodos = tk.Button(frame_botones,text="Eliminar TODOS",command=eliminar_todos,bg="#B71C1C",fg="white")
btn_EliminarTodos.grid(row=0,column=5,padx=5,pady=5)


btn_ExportarJSON = tk.Button(frame_botones,text="Exportar JSON",command=exportar_json)
btn_ExportarJSON.grid(row=1,column=0,padx=5,pady=5)

btn_ExportarCSV = tk.Button(frame_botones,text="Exportar CSV",command=exportar_csv)
btn_ExportarCSV.grid(row=1,column=1,padx=5,pady=5)

btn_ExportarXML = tk.Button(frame_botones,text="Exportar XML",command=exportar_xml)
btn_ExportarXML.grid(row=1,column=2,padx=5,pady=5)


btn_ImportarJSON = tk.Button(frame_botones,text="Importar JSON",command=importar_json)
btn_ImportarJSON.grid(row=2,column=0,padx=5,pady=5)

btn_ImportarCSV = tk.Button(frame_botones,text="Importar CSV",command=importar_csv)
btn_ImportarCSV.grid(row=2,column=1,padx=5,pady=5)

btn_ImportarXML = tk.Button(frame_botones,text="Importar XML",command=importar_xml)
btn_ImportarXML.grid(row=2,column=2,padx=5,pady=5)


btn_Backup = tk.Button(frame_botones,text="Crear Backup",command=crear_backup)
btn_Backup.grid(row=1,column=3,padx=5,pady=5)

btn_Restore = tk.Button(frame_botones,text="Restaurar Backup",command=ejecutar_backup)
btn_Restore.grid(row=1,column=4,padx=5,pady=5)


tabla = ttk.Treeview(
    ventana,
    columns=("cve","nom","eda","gru"),
    show="headings"
)

tabla.heading("cve",text="Clave")
tabla.heading("nom",text="Nombre")
tabla.heading("eda",text="Edad")
tabla.heading("gru",text="Grupo")

tabla.pack(fill="both",expand=True,padx=20,pady=10)

tabla.bind("<<TreeviewSelect>>",seleccionar_registro)

cargar_datos()

ventana.mainloop()