import tkinter as tk
from tkinter import messagebox, ttk
from pymongo import MongoClient as MC
from pydantic import BaseModel, Field, field_validator, ValidationError

# --- Configuración Mongo ---
try:
    client = MC("mongodb://localhost:27017/")
    db = client["BD_GrupoAlumno"]
    coleccion = db["Grupo"]
except Exception as e:
    print(f"Error: {e}")

# --- Modelo de Datos ---
class GrupoModelo(BaseModel):
    cveGru: str
    nomGru: str

    @field_validator('cveGru', 'nomGru')
    @classmethod
    def validar_vacio(cls, v):
        if not v.strip(): raise ValueError("Campo requerido")
        return v.strip()

    @field_validator('nomGru')
    @classmethod
    def validar_nombre(cls, v):
        if not v.replace(" ", "").isalnum(): 
            raise ValueError("El nombre debe ser alfanumérico")
        return v

# --- Funciones CRUD ---
def limpiar_campos():
    input_Grupo.config(state='normal')
    input_Grupo.delete(0, tk.END)
    input_NomGru.delete(0, tk.END)
    btn_Guardar.config(state='normal')
    btn_Actualizar.config(state='disabled')

def cargar_datos():
    # Limpiar tabla
    for item in tabla.get_children():
        tabla.delete(item)
    
    # Obtener datos de MongoDB
    try:
        registros = coleccion.find()
        for registro in registros:
            tabla.insert("", tk.END, text=registro["_id"], values=(registro["cveGru"], registro["nomGru"]))
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar datos: {e}")

def guardar_datos():
    try:
        # Validación: cveGru ya existe?
        if coleccion.find_one({"cveGru": input_Grupo.get()}):
            messagebox.showwarning("Advertencia", "La clave del Grupo ya existe")
            return
            
        # Validación: nomGru ya existe?
        if coleccion.find_one({"nomGru": input_NomGru.get()}):
            messagebox.showwarning("Advertencia", "El nombre del Grupo ya existe")
            return

        # Validación con Pydantic
        datos = GrupoModelo(
            cveGru = input_Grupo.get(), 
            nomGru = input_NomGru.get()
        )
        
        coleccion.insert_one(datos.model_dump(by_alias=True))
        messagebox.showinfo("Éxito", f"El Grupo se guardó correctamente: {datos.nomGru}")
        limpiar_campos()
        cargar_datos()

    except ValidationError as e:
        errores = "\n".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
        messagebox.showerror("Validación", errores)
    except Exception as e:
        messagebox.showerror("Error", f"Error de red o base de datos: {e}")

def seleccionar_registro(event):
    seleccion = tabla.focus()
    if seleccion:
        valores = tabla.item(seleccion, "values")
        if valores:
            limpiar_campos()
            input_Grupo.insert(0, valores[0])
            input_Grupo.config(state='disabled') # No permitir cambiar la clave
            input_NomGru.insert(0, valores[1])
            
            btn_Guardar.config(state='disabled')
            btn_Actualizar.config(state='normal')

def actualizar_datos():
    seleccion = tabla.focus()
    if not seleccion:
        messagebox.showwarning("Advertencia", "Seleccione un registro para actualizar")
        return

    try:
        cve_actual = input_Grupo.get()
        nuevo_nom = input_NomGru.get()
        
        # Validación: nomGru ya existe para otro grupo?
        existe = coleccion.find_one({"nomGru": nuevo_nom, "cveGru": {"$ne": cve_actual}})
        if existe:
            messagebox.showwarning("Advertencia", "El nombre del Grupo ya existe en otro registro")
            return

        # Validación con Pydantic
        datos = GrupoModelo(
            cveGru = cve_actual, 
            nomGru = nuevo_nom
        )
        
        resultado = coleccion.update_one(
            {"cveGru": cve_actual},
            {"$set": {"nomGru": datos.nomGru}}
        )

        if resultado.modified_count > 0:
            messagebox.showinfo("Éxito", "El Grupo se actualizó correctamente")
            limpiar_campos()
            cargar_datos()
        else:
            messagebox.showinfo("Info", "No se realizaron cambios")

    except ValidationError as e:
        errores = "\n".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
        messagebox.showerror("Validación", errores)
    except Exception as e:
        messagebox.showerror("Error", f"Error al actualizar: {e}")

def eliminar_datos():
    seleccion = tabla.focus()
    if not seleccion:
        messagebox.showwarning("Advertencia", "Seleccione un registro para eliminar")
        return
    
    valores = tabla.item(seleccion, "values")
    cve_eliminar = valores[0]

    respuesta = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el grupo {cve_eliminar}?")
    if respuesta:
        try:
            coleccion.delete_one({"cveGru": cve_eliminar})
            messagebox.showinfo("Éxito", "Grupo eliminado correctamente")
            limpiar_campos()
            cargar_datos()
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar: {e}")

# --- Interfaz Gráfica ---
ventana = tk.Tk()
ventana.title("CRUD de Grupos")
ventana.geometry("600x500")
ventana.config(cursor="hand2")

# Marco para el formulario
frame_form = tk.Frame(ventana)
frame_form.pack(pady=20)

lbl_Bienvenido = tk.Label(frame_form, text="Gestión de Grupos", font=("Arial", 14, "bold"))
lbl_Bienvenido.grid(row=0, column=0, columnspan=2, pady=10)

lbl_cveGru = tk.Label(frame_form, text="Clave (cveGru):", font=("Arial", 10))
lbl_cveGru.grid(row=1, column=0, sticky="e", padx=10, pady=5)
input_Grupo = tk.Entry(frame_form)
input_Grupo.grid(row=1, column=1, pady=5)

lbl_nomGru = tk.Label(frame_form, text="Nombre (nomGru):", font=("Arial", 10))
lbl_nomGru.grid(row=2, column=0, sticky="e", padx=10, pady=5)
input_NomGru = tk.Entry(frame_form)
input_NomGru.grid(row=2, column=1, pady=5)

# Marco para botones
frame_botones = tk.Frame(ventana)
frame_botones.pack(pady=10)

btn_Guardar = tk.Button(frame_botones, text="Guardar", command=guardar_datos, bg="#4CAF50", fg="black", width=12)
btn_Guardar.grid(row=0, column=0, padx=5)

btn_Actualizar = tk.Button(frame_botones, text="Actualizar", command=actualizar_datos, bg="#2196F3", fg="black", width=12, state='disabled')
btn_Actualizar.grid(row=0, column=1, padx=5)

btn_Eliminar = tk.Button(frame_botones, text="Eliminar", command=eliminar_datos, bg="#f44336", fg="black", width=12)
btn_Eliminar.grid(row=0, column=2, padx=5)

btn_Limpiar = tk.Button(frame_botones, text="Limpiar", command=limpiar_campos, bg="#9E9E9E", fg="black", width=12)
btn_Limpiar.grid(row=0, column=3, padx=5)

# Marco para la tabla
frame_tabla = tk.Frame(ventana)
frame_tabla.pack(pady=10, fill=tk.BOTH, expand=True)

columnas = ("cveGru", "nomGru")
tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
tabla.heading("cveGru", text="Clave del Grupo")
tabla.heading("nomGru", text="Nombre del Grupo")
tabla.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

tabla.bind("<<TreeviewSelect>>", seleccionar_registro)

# Cargar datos iniciales
cargar_datos()

ventana.mainloop()