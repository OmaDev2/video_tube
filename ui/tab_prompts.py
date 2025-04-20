# -*- coding: utf-8 -*-
# Archivo: ui/tab_prompts.py (Refactorizado para gestión unificada)

import tkinter as tk
from tkinter import ttk, messagebox
import os
import re
from pathlib import Path

# Importar el PromptManager unificado
try:
    # Asume que prompt_manager.py está accesible (ej. en el directorio raíz o en PYTHONPATH)
    from prompt_manager import PromptManager, DEFAULT_STYLE_TEMPLATE
    PROMPT_MANAGER_AVAILABLE = True
except ImportError:
    print("ERROR FATAL: No se pudo importar PromptManager en tab_prompts.")
    PROMPT_MANAGER_AVAILABLE = False
    # Podríamos añadir una clase dummy de PromptManager si queremos que la UI no falle completamente
    class PromptManager: # Dummy class
        def get_prompt_ids(self): return ["error_loading"]
        def get_prompt_names(self): return [("error_loading", "Error: Manager no cargado")]
        def get_style(self, style_id): return None
        def add_style(self, *args, **kwargs): return False
        def update_style_metadata(self, *args, **kwargs): return False
        def update_image_prompt_part(self, *args, **kwargs): return False
        def update_script_prompt_template(self, *args, **kwargs): return False
        def delete_style(self, *args, **kwargs): return False


# Importar la función para actualizar dropdowns en otras pestañas
try:
    from ui.prompt_updater import update_dropdowns_in_other_tabs
except ImportError:
    print("ADVERTENCIA: No se pudo importar prompt_updater. La actualización automática de dropdowns no funcionará.")
    def update_dropdowns_in_other_tabs(app): # Función dummy
        print("INFO: Llamada a update_dropdowns_in_other_tabs (dummy).")

class PromptsTabFrame(ttk.Frame):
    """
    Frame para gestionar TODAS las plantillas de prompts (Imagen y Guion).
    """
    def __init__(self, parent_notebook, app_instance, **kwargs):
        super().__init__(parent_notebook, style="Card.TFrame", **kwargs)
        self.app = app_instance
        self.prompt_manager = PromptManager() if PROMPT_MANAGER_AVAILABLE else None

        # Variables para widgets
        self.current_style_id = tk.StringVar() # ID del estilo seleccionado
        self.style_name = tk.StringVar()
        self.style_description = tk.StringVar()

        # Variable para el tipo de prompt seleccionado para edición
        self.selected_prompt_part_key = tk.StringVar()
        # Variable para almacenar la parte específica que se está editando (ej. 'user', 'esquema')
        self.current_editing_prompt_part = tk.StringVar()
        self.current_editing_prompt_category = tk.StringVar() # 'image_prompt' o 'script_prompt'

        # Definir las partes editables y sus placeholders
        self.editable_parts_info = {
            "Imagen: System": {"category": "image_prompt", "part": "system", "placeholders": "Ninguno"},
            "Imagen: User": {"category": "image_prompt", "part": "user", "placeholders": "{titulo}, {escena}"},
            "Imagen: Negative": {"category": "image_prompt", "part": "negative", "placeholders": "Ninguno"},
            "Guion: Esquema": {"category": "script_prompt", "part": "esquema", "placeholders": "{titulo}, {contexto}, {num_secciones}"},
            "Guion: Sección": {"category": "script_prompt", "part": "seccion", "placeholders": "{numero_seccion}, {instruccion_seccion}, {titulo}, {contexto}, {num_palabras}"},
            "Guion: Revisión": {"category": "script_prompt", "part": "revision", "placeholders": "{titulo}, {guion_borrador}"},
            "Guion: Metadata": {"category": "script_prompt", "part": "metadata", "placeholders": "{titulo}, {guion_final}"},
        }

        self._setup_widgets()
        if self.prompt_manager:
            self._load_style_list()
        else:
            messagebox.showerror("Error Fatal", "No se pudo inicializar el PromptManager. La pestaña de gestión de prompts no funcionará.")

    def _setup_widgets(self):
        """Configura la interfaz de usuario para la pestaña unificada."""
        lbl_title = ttk.Label(self, text="Gestor de Estilos y Plantillas de Prompt", style="Header.TLabel", font=("Helvetica", 14, "bold"))
        lbl_title.pack(pady=10)

        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(paned_window, style="Card.TFrame")
        right_frame = ttk.Frame(paned_window, style="Card.TFrame")
        paned_window.add(left_frame, weight=1)
        paned_window.add(right_frame, weight=3)

        self._setup_style_list(left_frame)
        self._setup_prompt_editor(right_frame)

    def _setup_style_list(self, parent_frame):
        """Configura la lista de ESTILOS en el frame izquierdo."""
        frame_list = ttk.LabelFrame(parent_frame, text="Estilos Disponibles")
        frame_list.pack(fill="both", expand=True, padx=5, pady=5)

        self.style_listbox = tk.Listbox(frame_list, height=15, width=30, font=("Helvetica", 11), exportselection=False) # Important: exportselection=False
        self.style_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=self.style_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.style_listbox.config(yscrollcommand=scrollbar.set)
        self.style_listbox.bind('<<ListboxSelect>>', self._on_style_selected)

        frame_buttons = ttk.Frame(parent_frame)
        frame_buttons.pack(fill="x", padx=5, pady=5)
        btn_new = ttk.Button(frame_buttons, text="Nuevo Estilo", command=self._new_style)
        btn_new.pack(side="left", fill="x", expand=True, padx=2, pady=5)
        btn_delete = ttk.Button(frame_buttons, text="Eliminar Estilo", command=self._delete_style)
        btn_delete.pack(side="right", fill="x", expand=True, padx=2, pady=5)

    def _setup_prompt_editor(self, parent_frame):
        """Configura el editor unificado en el frame derecho."""
        # --- Contenedor principal con scroll ---
        editor_container = ttk.Frame(parent_frame)
        editor_container.pack(fill="both", expand=True, padx=5, pady=5)
        editor_scrollbar = ttk.Scrollbar(editor_container, orient="vertical")
        editor_scrollbar.pack(side="right", fill="y")
        editor_canvas = tk.Canvas(editor_container, yscrollcommand=editor_scrollbar.set, highlightthickness=0)
        editor_canvas.pack(side="left", fill="both", expand=True)
        editor_scrollbar.config(command=editor_canvas.yview)
        frame_editor = ttk.Frame(editor_canvas) # Frame interior
        frame_editor_window = editor_canvas.create_window((0, 0), window=frame_editor, anchor="nw")

        def configure_scroll(event): editor_canvas.configure(scrollregion=editor_canvas.bbox("all"))
        def configure_width(event): editor_canvas.itemconfig(frame_editor_window, width=editor_canvas.winfo_width())
        frame_editor.bind("<Configure>", configure_scroll)
        editor_canvas.bind("<Configure>", configure_width)
        def _on_mousewheel(event): editor_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        # Bind to canvas for specific scroll, might need adjustment per OS
        editor_canvas.bind_all("<MouseWheel>", _on_mousewheel) # Or bind specifically if needed

        # Configurar grid del frame interior
        frame_editor.columnconfigure(1, weight=1)

        # --- Fila 0: Título y Guardar ---
        lbl_editor_title = ttk.Label(frame_editor, text="Editar Estilo / Plantilla", font=("Helvetica", 12, "bold"))
        lbl_editor_title.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        btn_save = ttk.Button(frame_editor, text="Guardar Cambios", command=self._save_changes)
        btn_save.grid(row=0, column=2, padx=10, pady=(10, 5), sticky="e")

        # --- Fila 1: ID ---
        lbl_id = ttk.Label(frame_editor, text="ID Estilo:", width=15)
        lbl_id.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_id = ttk.Entry(frame_editor, textvariable=self.current_style_id)
        self.entry_id.grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # --- Fila 2: Nombre ---
        lbl_name = ttk.Label(frame_editor, text="Nombre Estilo:", width=15)
        lbl_name.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entry_name = ttk.Entry(frame_editor, textvariable=self.style_name)
        entry_name.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # --- Fila 3: Descripción ---
        lbl_desc = ttk.Label(frame_editor, text="Descripción Estilo:", width=15)
        lbl_desc.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entry_desc = ttk.Entry(frame_editor, textvariable=self.style_description)
        entry_desc.grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # --- Fila 4: Separador y Selector de Parte ---
        ttk.Separator(frame_editor, orient="horizontal").grid(row=4, column=0, columnspan=3, pady=10, sticky="ew")
        lbl_select_part = ttk.Label(frame_editor, text="Editar Plantilla Específica:")
        lbl_select_part.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.combo_prompt_part = ttk.Combobox(frame_editor, textvariable=self.selected_prompt_part_key,
                                              values=list(self.editable_parts_info.keys()), state="readonly", width=25)
        self.combo_prompt_part.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        self.combo_prompt_part.bind("<<ComboboxSelected>>", self._on_prompt_part_selected)

        # --- Fila 6: Info de Edición (Qué se edita y placeholders) ---
        self.lbl_editing_prompt_type = ttk.Label(frame_editor, text="Editando:", wraplength=500) # Ajustar wraplength
        self.lbl_editing_prompt_type.grid(row=6, column=0, columnspan=3, padx=10, pady=(10, 0), sticky="w")
        self.lbl_placeholders = ttk.Label(frame_editor, text="Placeholders:", wraplength=500) # Ajustar wraplength
        self.lbl_placeholders.grid(row=7, column=0, columnspan=3, padx=10, pady=(0, 5), sticky="w")

        # --- Fila 8: Editor Principal Unificado ---
        # Frame para el editor y sus scrollbars
        editor_text_frame = ttk.Frame(frame_editor)
        editor_text_frame.grid(row=8, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")
        frame_editor.rowconfigure(8, weight=1) # Permitir que esta fila crezca
        editor_text_frame.rowconfigure(0, weight=1)
        editor_text_frame.columnconfigure(0, weight=1)

        self.text_editor = tk.Text(editor_text_frame, height=15, wrap="word", undo=True) # Habilitar undo
        # Scrollbars para el editor principal
        editor_scroll_y = ttk.Scrollbar(editor_text_frame, orient="vertical", command=self.text_editor.yview)
        editor_scroll_x = ttk.Scrollbar(editor_text_frame, orient="horizontal", command=self.text_editor.xview)
        self.text_editor.configure(yscrollcommand=editor_scroll_y.set, xscrollcommand=editor_scroll_x.set)

        self.text_editor.grid(row=0, column=0, sticky="nsew")
        editor_scroll_y.grid(row=0, column=1, sticky="ns")
        editor_scroll_x.grid(row=1, column=0, sticky="ew")

    def _load_style_list(self):
        """Carga la lista de estilos disponibles en el listbox."""
        if not self.prompt_manager: return
        self.style_listbox.delete(0, tk.END)
        style_names_tuples = self.prompt_manager.get_prompt_names()
        for style_id, name in style_names_tuples:
            self.style_listbox.insert(tk.END, f"{name} ({style_id})")
        # Seleccionar el primero por defecto si existe
        if style_names_tuples:
             self.style_listbox.selection_set(0)
             self._on_style_selected(None) # Cargar el primer estilo

    def _on_style_selected(self, event):
        """Maneja el evento de selección de un estilo en la lista."""
        selection = self.style_listbox.curselection()
        if not selection: return
        selected_text = self.style_listbox.get(selection[0])

        # Extraer ID (asumiendo formato "Nombre (id)")
        match = re.search(r'\(([^)]+)\)$', selected_text)
        if not match: return
        style_id = match.group(1)

        self._load_style_data(style_id)

    def _load_style_data(self, style_id):
        """Carga la información del estilo y la primera parte del prompt."""
        if not self.prompt_manager: return
        style_data = self.prompt_manager.get_style(style_id)
        if not style_data: return

        self.current_style_id.set(style_id)
        self.style_name.set(style_data.get("name", ""))
        self.style_description.set(style_data.get("description", ""))

        # Poblar y seleccionar por defecto en el combobox de partes
        available_parts = list(self.editable_parts_info.keys())
        self.combo_prompt_part['values'] = available_parts
        if available_parts:
            default_part_key = available_parts[1] # Seleccionar "Image: User" por defecto
            self.selected_prompt_part_key.set(default_part_key)
            self._load_prompt_part(style_id, default_part_key) # Cargar contenido de la parte por defecto

        # Habilitar/Deshabilitar edición de ID
        self.entry_id.config(state="disabled" if style_id == "default" else "normal")

    def _on_prompt_part_selected(self, event):
        """Maneja la selección de una parte específica del prompt a editar."""
        style_id = self.current_style_id.get()
        part_key = self.selected_prompt_part_key.get()
        if not style_id or not part_key: return
        self._load_prompt_part(style_id, part_key)

    def _load_prompt_part(self, style_id, part_key):
        """Carga el contenido de la parte específica del prompt en el editor principal."""
        if not self.prompt_manager or not part_key in self.editable_parts_info:
             self.text_editor.delete(1.0, tk.END)
             self.lbl_editing_prompt_type.config(text="Editando: (Selecciona parte)")
             self.lbl_placeholders.config(text="Placeholders:")
             return

        part_info = self.editable_parts_info[part_key]
        category = part_info["category"] # 'image_prompt' o 'script_prompt'
        part = part_info["part"] # 'system', 'user', 'esquema', etc.
        placeholders = part_info["placeholders"]

        # Guardar qué se está editando
        self.current_editing_prompt_category.set(category)
        self.current_editing_prompt_part.set(part)

        # Obtener el estilo completo
        style_data = self.prompt_manager.get_style(style_id)
        content = ""
        if style_data:
            category_data = style_data.get(category, {})
            content = category_data.get(part, "")

        # Actualizar el editor y las etiquetas
        self.text_editor.delete(1.0, tk.END)
        self.text_editor.insert(tk.END, content)
        self.lbl_editing_prompt_type.config(text=f"Editando: {part_key}")
        self.lbl_placeholders.config(text=f"Placeholders: {placeholders}")

    def _new_style(self):
        """Prepara el editor para crear un nuevo estilo."""
        if not self.prompt_manager: return

        # Generar ID único
        base_id = "custom_style"; counter = 1; new_id = f"{base_id}_{counter}"
        while new_id in self.prompt_manager.get_prompt_ids(): counter += 1; new_id = f"{base_id}_{counter}"

        # Establecer valores por defecto
        self.current_style_id.set(new_id)
        self.style_name.set("Nuevo Estilo Personalizado")
        self.style_description.set("Descripción del nuevo estilo")

        # Limpiar editor y seleccionar parte por defecto
        self.text_editor.delete(1.0, tk.END)
        available_parts = list(self.editable_parts_info.keys())
        self.combo_prompt_part['values'] = available_parts
        if available_parts:
            default_part_key = available_parts[1] # "Image: User"
            self.selected_prompt_part_key.set(default_part_key)
            # Cargar plantilla por defecto para esta parte
            part_info = self.editable_parts_info[default_part_key]
            default_content = DEFAULT_STYLE_TEMPLATE.get(part_info["category"], {}).get(part_info["part"], "")
            self.text_editor.insert(tk.END, default_content)
            self.lbl_editing_prompt_type.config(text=f"Editando: {default_part_key}")
            self.lbl_placeholders.config(text=f"Placeholders: {part_info['placeholders']}")
            self.current_editing_prompt_category.set(part_info["category"])
            self.current_editing_prompt_part.set(part_info["part"])


        self.entry_id.config(state="normal") # Permitir editar ID para nuevo estilo
        messagebox.showinfo("Nuevo Estilo", f"Introduce los detalles para el nuevo estilo con ID: {new_id}.\nGuarda los cambios cuando termines.")


    def _save_changes(self):
        """Guarda los cambios del estilo actual (metadatos y la parte del prompt editada)."""
        if not self.prompt_manager: return

        style_id = self.current_style_id.get().strip()
        name = self.style_name.get().strip()
        description = self.style_description.get().strip()
        edited_content = self.text_editor.get(1.0, tk.END).strip()
        editing_category = self.current_editing_prompt_category.get() # 'image_prompt' o 'script_prompt'
        editing_part = self.current_editing_prompt_part.get() # 'system', 'user', 'esquema', etc.

        if not style_id or not name:
            messagebox.showerror("Error", "El ID y el Nombre del estilo son obligatorios.")
            return

        # Validar ID si es un nuevo estilo (simple check)
        if self.entry_id.cget('state') == 'normal' and not re.match(r'^[a-zA-Z0-9_]+$', style_id):
             messagebox.showerror("Error", "El ID solo puede contener letras, números y guiones bajos.")
             return

        # --- Lógica de Guardado ---
        is_new_style = style_id not in self.prompt_manager.get_prompt_ids()
        save_successful = False

        if is_new_style:
            # Añadir el nuevo estilo (con plantillas por defecto iniciales)
            added = self.prompt_manager.add_style(style_id, name, description)
            if not added:
                messagebox.showerror("Error", f"No se pudo añadir el nuevo estilo (quizás el ID '{style_id}' ya existe?).")
                return
            else:
                print(f"Nuevo estilo '{style_id}' añadido. Procediendo a guardar la parte editada.")
        else:
            # Actualizar metadatos del estilo existente
            updated_meta = self.prompt_manager.update_style_metadata(style_id, name, description)
            if not updated_meta:
                 print(f"ADVERTENCIA: No se pudieron actualizar los metadatos para '{style_id}'.")
                 # Continuar para intentar guardar la parte del prompt de todos modos

        # Ahora, guardar la parte específica del prompt que se estaba editando
        if editing_category and editing_part:
            if editing_category == "image_prompt":
                updated_part = self.prompt_manager.update_image_prompt_part(style_id, editing_part, edited_content)
            elif editing_category == "script_prompt":
                updated_part = self.prompt_manager.update_script_prompt_template(style_id, editing_part, edited_content)
            else:
                updated_part = False # Categoría desconocida

            if updated_part:
                print(f"Parte '{editing_category}.{editing_part}' guardada para estilo '{style_id}'.")
                save_successful = True # Marcamos éxito si al menos la parte se guardó
            else:
                messagebox.showerror("Error", f"Fallo al guardar la plantilla específica '{editing_part}' para el estilo '{style_id}'.")
                save_successful = False # Falló el guardado de la parte
        else:
             print("ADVERTENCIA: No se estaba editando ninguna parte específica del prompt. Solo se guardaron metadatos.")
             # Consideramos éxito si es un estilo existente y los metadatos se actualizaron (o si es nuevo)
             save_successful = not is_new_style # Si es nuevo, ya se añadió, es éxito. Si es existente, depende de updated_meta (que no guardamos)

        # --- Feedback Final ---
        if save_successful:
             messagebox.showinfo("Éxito", f"Cambios para el estilo '{name}' guardados.")
             self._load_style_list() # Recargar lista por si cambió nombre o se añadió nuevo
             # Opcional: re-seleccionar el estilo actual en la lista
             items = self.style_listbox.get(0, tk.END)
             for i, item in enumerate(items):
                  if f"({style_id})" in item:
                       self.style_listbox.selection_clear(0, tk.END)
                       self.style_listbox.selection_set(i)
                       self.style_listbox.activate(i)
                       self.style_listbox.see(i)
                       break
             self._update_dropdowns_in_other_tabs() # Actualizar otros dropdowns
        else:
             # Ya se mostró un error específico antes si falló el guardado de la parte
             if not is_new_style and not editing_category: # Si solo fallaron metadatos
                  messagebox.showerror("Error", f"No se pudieron guardar los metadatos para '{style_id}'.")


    def _delete_style(self):
        """Elimina el estilo seleccionado."""
        if not self.prompt_manager: return
        style_id = self.current_style_id.get()
        if not style_id:
            messagebox.showwarning("Selección Requerida", "Selecciona un estilo de la lista para eliminar.")
            return
        if style_id == "default":
            messagebox.showerror("Error", "No se puede eliminar el estilo 'default'.")
            return

        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de eliminar el estilo '{style_id}' y todas sus plantillas?"):
            if self.prompt_manager.delete_style(style_id):
                messagebox.showinfo("Éxito", f"Estilo '{style_id}' eliminado.")
                # Limpiar editor
                self.current_style_id.set(""); self.style_name.set(""); self.style_description.set("")
                self.selected_prompt_part_key.set("")
                self.text_editor.delete(1.0, tk.END)
                self.lbl_editing_prompt_type.config(text="Editando:")
                self.lbl_placeholders.config(text="Placeholders:")
                self.current_editing_prompt_category.set("")
                self.current_editing_prompt_part.set("")
                self.combo_prompt_part['values'] = [] # Limpiar combobox

                self._load_style_list() # Recargar lista
                self._update_dropdowns_in_other_tabs() # Actualizar otros dropdowns
            else:
                messagebox.showerror("Error", f"No se pudo eliminar el estilo '{style_id}'.")

    def _update_dropdowns_in_other_tabs(self):
        """Actualiza los dropdowns de estilos en otras pestañas de la app."""
        if self.prompt_manager:
             # Pasar la instancia de la app principal a la función de actualización
             update_dropdowns_in_other_tabs(self.app)
        else:
             print("ERROR: PromptManager no disponible para actualizar dropdowns.")

# Puedes añadir un bloque if __name__ == "__main__": para probar esta pestaña aisladamente si lo necesitas
# import tkinter as tk
# if __name__ == "__main__":
#     root = tk.Tk()
#     root.title("Test Prompts Tab")
#     # Necesitarías crear una instancia 'dummy' de app_instance o pasar None y manejarlo
#     class DummyApp: pass
#     app = DummyApp()
#     # Añadirle las variables tk que PromptsTabFrame espera que existan en app
#     app.selected_prompt_style = tk.StringVar() # Ejemplo
#     # ... añade otras variables tk necesarias por el código ...
#
#     notebook = ttk.Notebook(root)
#     prompts_tab = PromptsTabFrame(notebook, app)
#     notebook.add(prompts_tab, text="Gestor Prompts")
#     notebook.pack(expand=True, fill="both")
#     root.mainloop()