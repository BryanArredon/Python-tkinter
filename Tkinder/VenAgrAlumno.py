import tkinter as tk
from tkinter import messagebox, ttk
from pymongo import MongoClient as MC
from pydantic import BaseModel, Field, field_validator, ValidationError

# --- Configuración Mongo ---
try: 
    client = MC("mongodb://localhost:27017/")
    db = client["BD_GrupoAlumno"]
    coleccion = db["Alumno"]
    coleccion_grupo = db["Grupo"] # Para validar si existe el grupo
except Exception as e:
    print(f"Error de conexión: {e}")

# --- Modelo de Datos ---
class AlumnoModelo(BaseModel):
    cveAlu: str
    nomAlu: str
    edaAlu: int # Mejor validarlo como entero
    cveGru: str

    @field_validator('cveAlu', 'nomAlu', 'cveGru')
    @classmethod
    def validar_vacio(cls, v):
        if not v.strip(): raise ValueError("Campo requerido")
        return v.strip()
    
    @field_validator('edaAlu')
    @classmethod
    def validar_edad(cls, v):
        if v <= 0: raise ValueError("La edad debe ser mayor a 0")
        return v

# --- Funciones CRUD ---
def limpiar_campos():
    input_Alumno.config(state='normal')
    input_Alumno.delete(0, tk.END)
    input_NomAlu.delete(0, tk.END)
    input_Edad.delete(0, tk.END)
    input_Grupo.delete(0, tk.END)
    btn_guardar.config(state='normal')
    btn_Actualizar.config(state='disabled')

def cargar_datos():
    # Limpiar tabla
    for item in tabla.get_children():
        tabla.delete(item)
    
    # Obtener datos de MongoDB
    try:
        registros = coleccion.find()
        for registro in registros:
            tabla.insert("", tk.END, text=registro["_id"], values=(
                registro.get("cveAlu", ""), 
                registro.get("nomAlu", ""), 
                registro.get("edaAlu", ""), 
                registro.get("cveGru", "")
            ))
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar datos: {e}")

def guardar_datos():
    try:
        # Validación: cveAlu ya existe?
        if coleccion.find_one({"cveAlu": input_Alumno.get()}):
            messagebox.showwarning("Advertencia", "La clave del Alumno ya existe")
            return
            
        # Validación: existe el cveGru en la colección Grupo? (Integridad referencial)
        if not coleccion_grupo.find_one({"cveGru": input_Grupo.get()}):
            messagebox.showwarning("Advertencia", "La clave de Grupo ingresada NO existe en los registros de Grupos")
            return

        # Validación con Pydantic
        datos = AlumnoModelo(
            cveAlu = input_Alumno.get(), 
            nomAlu = input_NomAlu.get(),
            edaAlu = int(input_Edad.get()), # Convertir a entero
            cveGru = input_Grupo.get()
        )

        coleccion.insert_one(datos.model_dump(by_alias=True))

        messagebox.showinfo("Éxito", f"El Alumno se guardó correctamente: {datos.nomAlu}")
        limpiar_campos()
        cargar_datos()

    except ValueError:
        messagebox.showerror("Validación", "La edad debe ser un número válido")
    except ValidationError as e:
        errores = "\n".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
        messagebox.showerror("Validación", errores)
    except Exception as e:      
        messagebox.showerror("Error", f"Error inesperado: {e}")

def seleccionar_registro(event):
    seleccion = tabla.focus()
    if seleccion:
        valores = tabla.item(seleccion, "values")
        if valores:
            limpiar_campos()
            input_Alumno.insert(0, valores[0])
            input_Alumno.config(state='disabled') # Bloquear clave de alumno
            input_NomAlu.insert(0, valores[1])
            input_Edad.insert(0, valores[2])
            input_Grupo.insert(0, valores[3])
            
            btn_guardar.config(state='disabled')
            btn_Actualizar.config(state='normal')

def actualizar_datos():
    seleccion = tabla.focus()
    if not seleccion:
        messagebox.showwarning("Advertencia", "Seleccione un registro para actualizar")
        return

    try:
        cve_actual = input_Alumno.get()
        nuevo_nom = input_NomAlu.get()
        nueva_edad = int(input_Edad.get())
        nuevo_grupo = input_Grupo.get()
        
        # Validación: existe el cveGru en la colección Grupo?
        if not coleccion_grupo.find_one({"cveGru": nuevo_grupo}):
            messagebox.showwarning("Advertencia", "La clave de Grupo ingresada NO existe en los registros de Grupos")
            return

        # Validación con Pydantic
        datos = AlumnoModelo(
            cveAlu = cve_actual, 
            nomAlu = nuevo_nom,
            edaAlu = nueva_edad,
            cveGru = nuevo_grupo
        )
        
        resultado = coleccion.update_one(
            {"cveAlu": cve_actual},
            {"$set": {
                "nomAlu": datos.nomAlu,
                "edaAlu": datos.edaAlu,
                "cveGru": datos.cveGru
            }}
        )

        if resultado.modified_count > 0:
            messagebox.showinfo("Éxito", "El Alumno se actualizó correctamente")
            limpiar_campos()
            cargar_datos()
        else:
            messagebox.showinfo("Info", "No se realizaron cambios")

    except ValueError:
        messagebox.showerror("Validación", "La edad debe ser un número válido")
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

    respuesta = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar al alumno con clave {cve_eliminar}?")
    if respuesta:
        try:
            coleccion.delete_one({"cveAlu": cve_eliminar})
            messagebox.showinfo("Éxito", "Alumno eliminado correctamente")
            limpiar_campos()
            cargar_datos()
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar: {e}")

# --- Interfaz Gráfica ---
Ventana = tk.Tk()
Ventana.title("CRUD de Alumnos")
Ventana.geometry("650x600")
Ventana.config(cursor="hand2")

# Marco superior para formulario
frame_form = tk.Frame(Ventana)
frame_form.pack(pady=20)

titulo = tk.Label(frame_form, text="Gestión de Alumnos", font=("Arial", 14, "bold"))
titulo.grid(row=0, column=0, columnspan=2, pady=10)

label_Alumno = tk.Label(frame_form, text="Clave del Alumno (cveAlu):", font=("Arial", 10))
label_Alumno.grid(row=1, column=0, sticky="e", padx=10, pady=5)
input_Alumno = tk.Entry(frame_form)
input_Alumno.grid(row=1, column=1, pady=5) 

label_NomAlu = tk.Label(frame_form, text="Nombre (nomAlu):", font=("Arial", 10))
label_NomAlu.grid(row=2, column=0, sticky="e", padx=10, pady=5)
input_NomAlu = tk.Entry(frame_form)
input_NomAlu.grid(row=2, column=1, pady=5)

label_Edad = tk.Label(frame_form, text="Edad (edaAlu):", font=("Arial", 10))
label_Edad.grid(row=3, column=0, sticky="e", padx=10, pady=5)
input_Edad = tk.Entry(frame_form)
input_Edad.grid(row=3, column=1, pady=5)

label_Grupo = tk.Label(frame_form, text="Clave del Grupo (cveGru):", font=("Arial", 10))
label_Grupo.grid(row=4, column=0, sticky="e", padx=10, pady=5)
input_Grupo = tk.Entry(frame_form)
input_Grupo.grid(row=4, column=1, pady=5)

# Marco para botones
frame_botones = tk.Frame(Ventana)
frame_botones.pack(pady=10)

btn_guardar = tk.Button(frame_botones, text="Guardar", command=guardar_datos, bg="#4CAF50", fg="black", width=12)
btn_guardar.grid(row=0, column=0, padx=5)

btn_Actualizar = tk.Button(frame_botones, text="Actualizar", command=actualizar_datos, bg="#2196F3", fg="black", width=12, state='disabled')
btn_Actualizar.grid(row=0, column=1, padx=5)

btn_Eliminar = tk.Button(frame_botones, text="Eliminar", command=eliminar_datos, bg="#f44336", fg="black", width=12)
btn_Eliminar.grid(row=0, column=2, padx=5)

btn_Limpiar = tk.Button(frame_botones, text="Limpiar", command=limpiar_campos, bg="#9E9E9E", fg="black", width=12)
btn_Limpiar.grid(row=0, column=3, padx=5)

# Marco para la tabla
frame_tabla = tk.Frame(Ventana)
frame_tabla.pack(pady=10, fill=tk.BOTH, expand=True)

columnas = ("cveAlu", "nomAlu", "edaAlu", "cveGru")
tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")

tabla.heading("cveAlu", text="Cve. Alumno")
tabla.heading("nomAlu", text="Nombre")
tabla.heading("edaAlu", text="Edad")
tabla.heading("cveGru", text="Cve. Grupo")

# Tamaños de columnas
tabla.column("cveAlu", width=100)
tabla.column("nomAlu", width=200)
tabla.column("edaAlu", width=80)
tabla.column("cveGru", width=100)

tabla.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

# Un solo clic para seleccionar
tabla.bind("<<TreeviewSelect>>", seleccionar_registro)

# Cargar datos iniciales
cargar_datos()

Ventana.mainloop()