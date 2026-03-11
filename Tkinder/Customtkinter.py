import customtkinter as ctk
from tkinter import ttk, messagebox
from pymongo import MongoClient as MC
from pydantic import BaseModel, field_validator, ValidationError
from contextlib import suppress
from dataclasses import dataclass
from typing import Optional

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Paleta ────────────────────────────────────────────────────────────────────
BG     = "#080b10"
PANEL  = "#0d1117"
CARD   = "#111520"
CARD2  = "#0a0d14"
LINE   = "#1e2535"
NEON_G = "#00ff9d"
NEON_B = "#00c8ff"
NEON_Y = "#f5c400"
DANGER = "#ff3c5a"
WARN   = "#ff8c00"
TEXT   = "#cdd6f4"
MUTED  = "#4a5270"

F_HERO  = ("Consolas", 28, "bold")
F_MONO  = ("Consolas", 11, "bold")
F_SM    = ("Consolas",  9, "bold")
F_BODY  = ("Consolas", 10)
F_BTN   = ("Consolas", 10, "bold")
F_ENTRY = ("Consolas", 12)
F_NUM   = ("Consolas", 36, "bold")


# ── MongoDB ───────────────────────────────────────────────────────────────────
def _connect():
    client = MC("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    client.server_info()
    return client["BD_GrupoAlumno"]["Grupo"]

coleccion = None
with suppress(Exception):
    coleccion = _connect()


# ── Modelo ────────────────────────────────────────────────────────────────────
class GrupoModelo(BaseModel):
    cveGru: str
    nomGru: str

    @field_validator("cveGru", "nomGru")
    @classmethod
    def no_vacio(cls, v):
        if not v.strip():
            raise ValueError("Campo requerido")
        return v.strip()

    @field_validator("nomGru")
    @classmethod
    def solo_alfa(cls, v):
        if not v.replace(" ", "").isalpha():
            raise ValueError("Solo se permiten letras")
        return v


# ── Estado de validación ──────────────────────────────────────────────────────
@dataclass
class ValResult:
    ok: bool
    msg: str
    color: str
    border: str


def _validar_clave(val: str, edit_id=None) -> ValResult:
    checks = [
        (not val,          ValResult(False, "── awaiting input",           MUTED,  LINE)),
        (len(val) < 3,     ValResult(False, "✗  clave muy corta (min. 3)", DANGER, DANGER)),
    ]
    for condition, result in checks:
        if condition:
            return result

    dupe = coleccion is not None and coleccion.find_one({"cveGru": val})
    if dupe and str(dupe["_id"]) != str(edit_id):
        return ValResult(False, "⚠  clave duplicada en BD", WARN, WARN)

    return ValResult(True, "✔  clave disponible", NEON_G, NEON_G)


def _validar_nombre(val: str) -> ValResult:
    checks = [
        (not val,                             ValResult(True,  "",                         MUTED,  LINE)),
        (not val.replace(" ", "").isalpha(),  ValResult(False, "✗  solo letras en nombre", DANGER, DANGER)),
    ]
    for condition, result in checks:
        if condition:
            return result
    return ValResult(True, "", NEON_B, NEON_B)


# ── Helpers de DB ─────────────────────────────────────────────────────────────
def _require_db():
    if coleccion is None:
        raise RuntimeError("MongoDB no disponible en localhost:27017")


def _check_dupes(datos: GrupoModelo, exclude_id=None):
    fields = {
        "cveGru": f"La clave '{datos.cveGru}' ya existe.",
        "nomGru": f"El nombre '{datos.nomGru}' ya existe.",
    }
    for field, msg in fields.items():
        doc = coleccion.find_one({field: getattr(datos, field)})
        if doc and str(doc.get("_id")) != str(exclude_id):
            raise ValueError(msg)


# ═══════════════════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GRP//MGMT · Sistema de Grupos")
        self.geometry("1080x680")
        self.minsize(900, 580)
        self.configure(fg_color=BG)
        self._edit_id : Optional[object] = None
        self._editing : bool             = False
        self._draw_ui()
        self._load()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _draw_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_rail()
        self._build_workspace()

    # ── Rail izquierdo ────────────────────────────────────────────────────────
    def _build_rail(self):
        rail = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=PANEL)
        rail.grid(row=0, column=0, sticky="nsew")
        rail.grid_propagate(False)

        ctk.CTkFrame(rail, fg_color=NEON_G, corner_radius=0, height=2).pack(fill="x")

        head = ctk.CTkFrame(rail, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(24, 0))
        ctk.CTkLabel(head, text="GRP",    font=F_HERO, text_color=NEON_G).pack(anchor="w")
        ctk.CTkLabel(head, text="// MGMT", font=("Consolas", 13, "bold"), text_color=NEON_B).pack(anchor="w")
        ctk.CTkLabel(head, text="Sistema de Gestión", font=F_SM, text_color=MUTED).pack(anchor="w", pady=(4, 0))

        ctk.CTkFrame(rail, height=1, fg_color=LINE).pack(fill="x", padx=20, pady=18)

        stat = ctk.CTkFrame(rail, fg_color=CARD2, corner_radius=8, border_width=1, border_color=LINE)
        stat.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(stat, text="REGISTROS ACTIVOS", font=F_SM, text_color=MUTED).pack(anchor="w", padx=14, pady=(12, 0))
        self.lbl_count = ctk.CTkLabel(stat, text="000", font=F_NUM, text_color=NEON_G)
        self.lbl_count.pack(anchor="w", padx=14, pady=(0, 12))

        db_color = NEON_G if coleccion is not None else DANGER
        db_text  = "MONGODB  ●  ONLINE" if coleccion is not None else "MONGODB  ●  OFFLINE"
        conn = ctk.CTkFrame(rail, fg_color=CARD2, corner_radius=8, border_width=1, border_color=db_color)
        conn.pack(fill="x", padx=16, pady=(0, 10))
        ctk.CTkLabel(conn, text=db_text, font=F_SM, text_color=db_color).pack(padx=14, pady=10)

        ctk.CTkFrame(rail, height=1, fg_color=LINE).pack(fill="x", padx=20, pady=8)
        nav = [
            ("▸ DASHBOARD", CARD,          NEON_B),
            ("  NUEVO GRUPO","transparent", MUTED),
            ("  EXPORTAR",   "transparent", MUTED),
            ("  AJUSTES",    "transparent", MUTED),
        ]
        for label, bg, tc in nav:
            f = ctk.CTkFrame(rail, fg_color=bg, corner_radius=6)
            f.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(f, text=label, font=F_SM, text_color=tc).pack(anchor="w", padx=14, pady=9)

        ctk.CTkLabel(rail, text="v2.0  //  PROD", font=F_SM, text_color=MUTED).pack(side="bottom", pady=14)

    # ── Workspace ─────────────────────────────────────────────────────────────
    def _build_workspace(self):
        ws = ctk.CTkFrame(self, fg_color=BG)
        ws.grid(row=0, column=1, sticky="nsew")
        ws.grid_rowconfigure(1, weight=1)
        ws.grid_columnconfigure(0, weight=1)
        self._build_topbar(ws)

        body = ctk.CTkFrame(ws, fg_color=BG)
        body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
        body.grid_rowconfigure(1, weight=1)
        body.grid_columnconfigure(0, weight=1)
        self._build_form(body)
        self._build_table(body)
        self._build_actions(body)

    def _build_topbar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color=PANEL, height=54, corner_radius=0)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        crumb = ctk.CTkFrame(bar, fg_color="transparent")
        crumb.grid(row=0, column=0, padx=24, sticky="w")
        for txt, color in [("INICIO", MUTED), ("  /  ", LINE), ("GRUPOS", NEON_B)]:
            ctk.CTkLabel(crumb, text=txt, font=F_SM, text_color=color).pack(side="left")

        badge = ctk.CTkFrame(bar, fg_color=NEON_G, corner_radius=4, width=100, height=26)
        badge.grid(row=0, column=2, padx=24, sticky="e")
        badge.grid_propagate(False)
        ctk.CTkLabel(badge, text="● EN LÍNEA", font=F_SM,
                     text_color="#050810").place(relx=.5, rely=.5, anchor="center")

    # ── Formulario ────────────────────────────────────────────────────────────
    def _build_form(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10,
                             border_width=1, border_color=LINE)
        panel.grid(row=0, column=0, sticky="ew", pady=(16, 12))
        panel.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ph = ctk.CTkFrame(panel, fg_color="transparent")
        ph.grid(row=0, column=0, columnspan=4, sticky="ew", padx=16, pady=(14, 0))
        ctk.CTkLabel(ph, text="◈  FORMULARIO DE REGISTRO", font=F_MONO, text_color=NEON_B).pack(side="left")
        self.lbl_mode = ctk.CTkLabel(ph, text="[ INSERTAR ]", font=F_SM, text_color=NEON_Y)
        self.lbl_mode.pack(side="right")

        ctk.CTkFrame(panel, fg_color=LINE, height=1).grid(
            row=1, column=0, columnspan=4, sticky="ew", padx=16, pady=(8, 10))

        def _field(col, label, color, placeholder):
            pad_l = 16 if col == 0 else 8
            ctk.CTkLabel(panel, text=label, font=F_SM, text_color=MUTED).grid(
                row=2, column=col, padx=(pad_l, 8), pady=(0, 4), sticky="w")
            e = ctk.CTkEntry(panel, placeholder_text=placeholder, font=F_ENTRY, height=44,
                             fg_color=CARD2, border_color=LINE, text_color=color,
                             corner_radius=6, placeholder_text_color=MUTED)
            e.grid(row=3, column=col, padx=(pad_l, 8), pady=(0, 16), sticky="ew")
            return e

        self.entry_cve = _field(0, "CLAVE_GRUPO",  NEON_G, "ej. GRP-001")
        self.entry_nom = _field(1, "NOMBRE_GRUPO", NEON_B, "Solo letras...")
        self.entry_cve.bind("<KeyRelease>", self._on_clave_change)
        self.entry_nom.bind("<KeyRelease>", self._on_nombre_change)

        ctk.CTkLabel(panel, text="ESTADO_VAL", font=F_SM, text_color=MUTED).grid(
            row=2, column=2, padx=8, pady=(0, 4), sticky="w")
        self.lbl_status = ctk.CTkLabel(panel, text="── awaiting input",
                                       font=F_BODY, text_color=MUTED, anchor="w", height=44)
        self.lbl_status.grid(row=3, column=2, padx=8, pady=(0, 16), sticky="ew")

        self.btn_save = ctk.CTkButton(
            panel, text="▶  EJECUTAR", font=F_BTN, height=44, width=148,
            fg_color=NEON_G, hover_color="#00cc7a", text_color="#050810",
            corner_radius=6, command=self.registrar)
        self.btn_save.grid(row=3, column=3, padx=(8, 16), pady=(0, 16))

    # ── Tabla ─────────────────────────────────────────────────────────────────
    def _build_table(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10,
                             border_width=1, border_color=LINE)
        panel.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(panel, fg_color=CARD2, corner_radius=0, height=42)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_propagate(False)
        ctk.CTkLabel(hdr, text="◉  INDEX / REGISTROS", font=F_MONO, text_color=NEON_B
                     ).grid(row=0, column=0, padx=18, pady=10, sticky="w")
        self.lbl_total = ctk.CTkLabel(hdr, text="[ 0 docs ]", font=F_SM, text_color=NEON_Y)
        self.lbl_total.grid(row=0, column=2, padx=18, pady=10, sticky="e")

        tf = ctk.CTkFrame(panel, fg_color="transparent")
        tf.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        sty = ttk.Style()
        sty.theme_use("default")
        sty.configure("T.Treeview",
            background=CARD2, foreground=TEXT, fieldbackground=CARD2,
            borderwidth=0, rowheight=38, font=("Consolas", 10))
        sty.configure("T.Treeview.Heading",
            background=CARD, foreground=MUTED, relief="flat", font=("Consolas", 9, "bold"))
        sty.map("T.Treeview",
            background=[("selected", "#003d28")], foreground=[("selected", NEON_G)])

        self.tabla = ttk.Treeview(tf, columns=("#", "Clave", "Nombre"),
                                  show="headings", style="T.Treeview", selectmode="browse")
        cols = [("#", "IDX", 60, "center", False),
                ("Clave", "CLAVE_GRP", 180, "center", False),
                ("Nombre", "NOMBRE_GRUPO", 0, "w", True)]
        for col, heading, width, anchor, stretch in cols:
            self.tabla.heading(col, text=heading)
            self.tabla.column(col, width=width, anchor=anchor, stretch=stretch)

        self.tabla.grid(row=0, column=0, sticky="nsew")
        self.tabla.bind("<<TreeviewSelect>>", self._on_select)

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")

        self.tabla.tag_configure("odd",  background="#0a0d14")
        self.tabla.tag_configure("even", background="#0d1020")

    # ── Acciones ──────────────────────────────────────────────────────────────
    def _build_actions(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="ew")

        btn_cfg = [
            ("btn_edit",   "⊞  EDITAR",   CARD2,         CARD,      self.editar,       "left",  (0, 6), "disabled"),
            ("btn_delete", "⊠  BORRAR",   CARD2,         "#220a0e", self.eliminar,     "left",  (0, 0), "disabled"),
            ("btn_cancel", "✕  CANCELAR", "transparent", CARD2,     self._reset_form,  "right", (0, 0), "normal"),
        ]
        for attr, text, fg, hover, cmd, side, padx, state in btn_cfg:
            btn = ctk.CTkButton(bar, text=text, font=F_BTN, height=36, width=120,
                                fg_color=fg, hover_color=hover,
                                border_width=1, border_color=LINE,
                                text_color=MUTED, state=state, command=cmd)
            btn.pack(side=side, padx=padx)
            setattr(self, attr, btn)

    # ── Validación en vivo ────────────────────────────────────────────────────
    def _on_clave_change(self, _=None):
        r = _validar_clave(self.entry_cve.get().strip(), self._edit_id)
        self.entry_cve.configure(border_color=r.border)
        self.lbl_status.configure(text=r.msg, text_color=r.color)

    def _on_nombre_change(self, _=None):
        r = _validar_nombre(self.entry_nom.get().strip())
        self.entry_nom.configure(border_color=r.border)
        if not r.ok:
            self.lbl_status.configure(text=r.msg, text_color=r.color)

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def registrar(self):
        try:
            datos = GrupoModelo(cveGru=self.entry_cve.get(), nomGru=self.entry_nom.get())
            _require_db()
            ops = {
                True:  lambda: coleccion.update_one(
                    {"_id": self._edit_id},
                    {"$set": {"cveGru": datos.cveGru, "nomGru": datos.nomGru}}),
                False: lambda: (_check_dupes(datos), coleccion.insert_one(datos.model_dump())),
            }
            ops[self._editing]()
            label = "actualizado" if self._editing else "insertado"
            self.lbl_status.configure(text=f"✔  '{datos.cveGru}' {label}", text_color=NEON_G)
            self._reset_form()
            self._load()
        except ValidationError as e:
            messagebox.showerror("Validación",
                "\n".join(f"• {err['loc'][0]}: {err['msg']}" for err in e.errors()))
        except (RuntimeError, ValueError) as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error inesperado", str(e))

    def editar(self):
        vals = self.tabla.item(self.tabla.selection()[0], "values")
        try:
            _require_db()
            doc = coleccion.find_one({"cveGru": vals[1]})
            if not doc:
                raise ValueError("Registro no encontrado en la BD.")
            self._edit_id, self._editing = doc["_id"], True
            for entry, val in [(self.entry_cve, vals[1]), (self.entry_nom, vals[2])]:
                entry.delete(0, "end")
                entry.insert(0, val)
            self.btn_save.configure(text="▶  ACTUALIZAR", fg_color=NEON_Y,
                                    hover_color="#c9a000", text_color="#050810")
            self.lbl_mode.configure(text="[ ACTUALIZAR ]", text_color=NEON_Y)
            self._on_clave_change()
        except (RuntimeError, ValueError) as e:
            messagebox.showerror("Error", str(e))

    def eliminar(self): 
        vals = self.tabla.item(self.tabla.selection()[0], "values")
        try:
            _require_db()
            if not messagebox.askyesno("Confirmar",
                    f"¿Eliminar '{vals[2]}'?\nEsta acción es irreversible."):
                return
            coleccion.delete_one({"cveGru": vals[1]})
            self.lbl_status.configure(text=f"✕  '{vals[1]}' eliminado", text_color=DANGER)
            self._reset_form()
            self._load()
        except (RuntimeError, Exception) as e:
            messagebox.showerror("Error", str(e))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _load(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)
        docs = list(coleccion.find({})) if coleccion is not None else []
        for i, doc in enumerate(docs, 1):
            self.tabla.insert("", "end",
                values=(f"{i:03d}", doc.get("cveGru", ""), doc.get("nomGru", "")),
                tags=("odd" if i % 2 else "even",))
        n = len(docs)
        self.lbl_count.configure(text=f"{n:03d}")
        self.lbl_total.configure(text=f"[ {n} docs ]")

    def _on_select(self, _=None):
        sel = bool(self.tabla.selection())
        for btn in (self.btn_edit, self.btn_delete):
            btn.configure(state="normal" if sel else "disabled",
                          text_color=TEXT if sel else MUTED)

    def _reset_form(self):
        for entry in (self.entry_cve, self.entry_nom):
            entry.delete(0, "end")
            entry.configure(border_color=LINE)
        self.lbl_status.configure(text="── awaiting input", text_color=MUTED)
        self._editing, self._edit_id = False, None
        self.btn_save.configure(text="▶  EJECUTAR", fg_color=NEON_G,
                                hover_color="#00cc7a", text_color="#050810")
        self.lbl_mode.configure(text="[ INSERTAR ]", text_color=NEON_Y)
        with suppress(Exception):
            self.tabla.selection_remove(self.tabla.selection())
        self._on_select()


if __name__ == "__main__":
    App().mainloop()