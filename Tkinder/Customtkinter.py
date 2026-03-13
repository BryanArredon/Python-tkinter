import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from pymongo import MongoClient as MC
from pydantic import BaseModel, field_validator, ValidationError
import csv
import json
import xml.etree.ElementTree as ET
import os


# --- Configuración Mongo ---
try:
    client = MC("mongodb://localhost:27017/")
    db = client["BD_GrupoAlumno"]
    coleccion = db["Grupo"]
except Exception as e:
    print(f"Error: {e}")


# --- Modelo ---
class GrupoModelo(BaseModel):

    cveGru: str
    nomGru: str

    @field_validator('cveGru','nomGru')
    @classmethod
    def validar_vacio(cls,v):

        if not v.strip():
            raise ValueError("Campo requerido")

        return v.strip()

    @field_validator('nomGru')
    @classmethod
    def validar_nombre(cls,v):

        if not v.replace(" ","").isalnum():
            raise ValueError("Nombre alfanumérico")

        return v


# --- CRUD ---

def limpiar_campos():

    input_Grupo.config(state='normal')
    input_Grupo.delete(0,tk.END)
    input_NomGru.delete(0,tk.END)

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
            values=(r.get("cveGru",""),r.get("nomGru",""))
        )


def guardar_datos():

    try:

        if coleccion.find_one({"cveGru":input_Grupo.get()}):
            messagebox.showwarning("Advertencia","La clave ya existe")
            return

        datos = GrupoModelo(
            cveGru=input_Grupo.get(),
            nomGru=input_NomGru.get()
        )

        coleccion.insert_one(datos.model_dump())

        messagebox.showinfo("Éxito","Grupo guardado")

        limpiar_campos()
        cargar_datos()

    except ValidationError as e:

        errores = "\n".join(
            [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
        )

        messagebox.showerror("Validación",errores)


def seleccionar_registro(event):

    seleccion = tabla.focus()

    if seleccion:

        valores = tabla.item(seleccion,"values")

        limpiar_campos()

        input_Grupo.insert(0,valores[0])
        input_Grupo.config(state="disabled")

        input_NomGru.insert(0,valores[1])

        btn_Guardar.config(state="disabled")
        btn_Actualizar.config(state="normal")


def actualizar_datos():

    seleccion = tabla.focus()

    if not seleccion:
        messagebox.showwarning("Advertencia","Seleccione un registro")
        return

    cve = input_Grupo.get()
    nuevo = input_NomGru.get()

    datos = GrupoModelo(cveGru=cve,nomGru=nuevo)

    coleccion.update_one(
        {"cveGru":cve},
        {"$set":{"nomGru":datos.nomGru}}
    )

    messagebox.showinfo("Éxito","Grupo actualizado")

    limpiar_campos()
    cargar_datos()


def eliminar_datos():

    seleccion = tabla.focus()

    if not seleccion:
        messagebox.showwarning("Advertencia","Seleccione un registro")
        return

    valores = tabla.item(seleccion,"values")

    coleccion.delete_one({"cveGru":valores[0]})

    cargar_datos()

    messagebox.showinfo("Éxito","Grupo eliminado")


# --- BUSCAR ---

def buscar_grupo():

    clave = input_Grupo.get().strip()

    if not clave:
        messagebox.showwarning("Advertencia","Ingrese la clave")
        return

    limpiar_campos()

    resultado = coleccion.find_one({"cveGru":clave})

    if resultado:

        input_Grupo.insert(0,resultado["cveGru"])
        input_Grupo.config(state="disabled")

        input_NomGru.insert(0,resultado["nomGru"])

        btn_Guardar.config(state="disabled")
        btn_Actualizar.config(state="normal")

    else:
        messagebox.showwarning("Aviso","Grupo no encontrado")


# --- EXPORTAR ---

def exportar_csv():

    archivo = filedialog.asksaveasfilename(defaultextension=".csv")

    if not archivo:
        return

    datos = coleccion.find()

    with open(archivo,"w",newline="") as f:

        writer = csv.writer(f)

        writer.writerow(["cveGru","nomGru"])

        for d in datos:
            writer.writerow([d.get("cveGru"),d.get("nomGru")])

    messagebox.showinfo("Éxito","Exportado a CSV")


def exportar_json():

    archivo = filedialog.asksaveasfilename(defaultextension=".json")

    if not archivo:
        return

    datos = list(coleccion.find({},{"_id":0}))

    with open(archivo,"w") as f:
        json.dump(datos,f,indent=4)

    messagebox.showinfo("Éxito","Exportado a JSON")


def exportar_xml():

    archivo = filedialog.asksaveasfilename(defaultextension=".xml")

    if not archivo:
        return

    root = ET.Element("Grupos")

    datos = coleccion.find()

    for d in datos:

        grupo = ET.SubElement(root,"Grupo")

        ET.SubElement(grupo,"cveGru").text = d.get("cveGru","")
        ET.SubElement(grupo,"nomGru").text = d.get("nomGru","")

    tree = ET.ElementTree(root)
    tree.write(archivo)

    messagebox.showinfo("Éxito","Exportado a XML")


# --- IMPORTAR ---

def importar_csv():

    archivo = filedialog.askopenfilename(filetypes=[("CSV","*.csv")])

    if not archivo:
        return

    with open(archivo) as f:

        reader = csv.DictReader(f)

        for row in reader:
            coleccion.insert_one(row)

    cargar_datos()

    messagebox.showinfo("Éxito","CSV importado")


def importar_json():

    archivo = filedialog.askopenfilename(filetypes=[("JSON","*.json")])

    if not archivo:
        return

    with open(archivo) as f:

        datos = json.load(f)

        for d in datos:
            coleccion.insert_one(d)

    cargar_datos()

    messagebox.showinfo("Éxito","JSON importado")


def importar_xml():

    archivo = filedialog.askopenfilename(filetypes=[("XML","*.xml")])

    if not archivo:
        return

    tree = ET.parse(archivo)

    root = tree.getroot()

    for grupo in root.findall("Grupo"):

        coleccion.insert_one({
            "cveGru":grupo.find("cveGru").text,
            "nomGru":grupo.find("nomGru").text
        })

    cargar_datos()

    messagebox.showinfo("Éxito","XML importado")


# --- BACKUP ---

def ejecutar_backup():

    carpeta = filedialog.askdirectory()

    if not carpeta:
        return

    datos = list(coleccion.find({},{"_id":0}))

    ruta = os.path.join(carpeta,"backup_grupos.json")

    with open(ruta,"w") as f:
        json.dump(datos,f,indent=4)

    messagebox.showinfo("Backup","Backup creado correctamente")


def restaurar_backup():

    archivo = filedialog.askopenfilename(filetypes=[("JSON","*.json")])

    if not archivo:
        return

    with open(archivo) as f:
        datos = json.load(f)

    coleccion.delete_many({})

    for d in datos:
        coleccion.insert_one(d)

    cargar_datos()

    messagebox.showinfo("Restaurar","Backup restaurado correctamente")


def eliminar_todos():

    if messagebox.askyesno("Confirmar","¿Eliminar TODOS los grupos?"):

        coleccion.delete_many({})

        cargar_datos()

        messagebox.showinfo("Éxito","Todos los grupos eliminados")


# --- INTERFAZ ---

ventana = tk.Tk()
ventana.title("Sistema de Administración de Grupos")
ventana.geometry("750x650")
ventana.configure(bg="#f0f2f5")


titulo = tk.Label(
    ventana,
    text="Administración de Grupos",
    font=("Segoe UI",18,"bold"),
    bg="#f0f2f5"
)

titulo.pack(pady=10)


# --- FORMULARIO ---

frame_form = tk.LabelFrame(
    ventana,
    text="Datos del Grupo",
    bg="white",
    padx=20,
    pady=15
)

frame_form.pack(pady=10,fill="x",padx=20)

tk.Label(frame_form,text="Clave:",bg="white").grid(row=0,column=0,padx=10,pady=5)

input_Grupo = tk.Entry(frame_form,width=30)
input_Grupo.grid(row=0,column=1,padx=10,pady=5)

tk.Label(frame_form,text="Nombre:",bg="white").grid(row=1,column=0,padx=10,pady=5)

input_NomGru = tk.Entry(frame_form,width=30)
input_NomGru.grid(row=1,column=1,padx=10,pady=5)


# --- OPERACIONES ---

frame_botones = tk.LabelFrame(
    ventana,
    text="Operaciones",
    bg="white",
    padx=10,
    pady=10
)

frame_botones.pack(pady=10,fill="x",padx=20)


# CRUD

btn_Guardar = tk.Button(frame_botones,text="Guardar",width=12,bg="#4CAF50",fg="white",command=guardar_datos)
btn_Guardar.grid(row=0,column=0,padx=5,pady=5)

btn_Actualizar = tk.Button(frame_botones,text="Modificar",width=12,bg="#2196F3",fg="white",command=actualizar_datos,state="disabled")
btn_Actualizar.grid(row=0,column=1,padx=5,pady=5)

btn_Eliminar = tk.Button(frame_botones,text="Eliminar",width=12,bg="#f44336",fg="white",command=eliminar_datos)
btn_Eliminar.grid(row=0,column=2,padx=5,pady=5)

btn_Buscar = tk.Button(frame_botones,text="Buscar",width=12,bg="#9C27B0",fg="white",command=buscar_grupo)
btn_Buscar.grid(row=0,column=3,padx=5,pady=5)

btn_Limpiar = tk.Button(frame_botones,text="Limpiar",width=12,bg="#607D8B",fg="white",command=limpiar_campos)
btn_Limpiar.grid(row=0,column=4,padx=5,pady=5)


# Exportar

tk.Label(frame_botones,text="Exportar:",bg="white").grid(row=1,column=0,pady=5)

tk.Button(frame_botones,text="CSV",width=12,command=exportar_csv).grid(row=1,column=1,padx=5)
tk.Button(frame_botones,text="JSON",width=12,command=exportar_json).grid(row=1,column=2,padx=5)
tk.Button(frame_botones,text="XML",width=12,command=exportar_xml).grid(row=1,column=3,padx=5)


# Importar

tk.Label(frame_botones,text="Importar:",bg="white").grid(row=2,column=0,pady=5)

tk.Button(frame_botones,text="CSV",width=12,command=importar_csv).grid(row=2,column=1,padx=5)
tk.Button(frame_botones,text="JSON",width=12,command=importar_json).grid(row=2,column=2,padx=5)
tk.Button(frame_botones,text="XML",width=12,command=importar_xml).grid(row=2,column=3,padx=5)


# Backup

tk.Button(frame_botones,text="Crear Backup",width=15,command=ejecutar_backup).grid(row=3,column=1,pady=5)

tk.Button(frame_botones,text="Restaurar Backup",width=15,command=restaurar_backup).grid(row=3,column=2,pady=5)


# Eliminar todos

tk.Button(
    frame_botones,
    text="Eliminar TODOS los grupos",
    bg="#b71c1c",
    fg="white",
    width=25,
    command=eliminar_todos
).grid(row=4,column=1,columnspan=2,pady=10)


# --- TABLA ---

frame_tabla = tk.Frame(ventana,bg="#f0f2f5")
frame_tabla.pack(fill=tk.BOTH,expand=True,padx=20,pady=10)

tabla = ttk.Treeview(frame_tabla,columns=("cveGru","nomGru"),show="headings")

tabla.heading("cveGru",text="Clave del Grupo")
tabla.heading("nomGru",text="Nombre del Grupo")

tabla.column("cveGru",width=150,anchor="center")
tabla.column("nomGru",width=300,anchor="center")

tabla.pack(fill=tk.BOTH,expand=True)

tabla.bind("<<TreeviewSelect>>",seleccionar_registro)

cargar_datos()

ventana.mainloop()