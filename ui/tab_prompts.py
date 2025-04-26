# -*- coding: utf-8 -*-
# Archivo: ui/tab_prompts.py

import tkinter as tk
from tkinter import ttk, messagebox
import os
import re
from pathlib import Path

from prompt_manager import PromptManager, DEFAULT_PROMPT_TEMPLATE
from ui.prompt_updater import update_dropdowns_in_other_tabs
from script_prompt_manager import ScriptPromptManager

class PromptsTabFrame(ttk.Frame):
    """
    Frame que contiene todos los widgets para la pestaña de 'Gestor de Prompts'.
    Permite crear, editar y eliminar plantillas de prompts personalizados de imágenes y de scripts.
    """
    def __init__(self, parent_notebook, app_instance, **kwargs):
        """
        Inicializa el Frame de la pestaña de Gestor de Prompts.

        Args:
            parent_notebook: El widget ttk.Notebook que contendrá esta pestaña.
            app_instance: La instancia principal de VideoCreatorApp para acceder a variables y métodos.
        """
        super().__init__(parent_notebook, style="Card.TFrame", **kwargs)
        self.app = app_instance  # Guardamos la referencia a la app principal (VideoCreatorApp)
        
        # Gestores
        self.prompt_manager = PromptManager()
        self.script_prompt_manager = ScriptPromptManager()
        
        # Variables para imágenes
        self.current_prompt_id_img = tk.StringVar()
        self.prompt_name_img = tk.StringVar()
        self.prompt_description_img = tk.StringVar()
        self.negative_prompt_img = tk.StringVar()
        
        # Variables para scripts
        self.current_prompt_id_script = tk.StringVar()
        self.prompt_name_script = tk.StringVar()
        self.prompt_description_script = tk.StringVar()
        
        # Variables para la vista previa
        self.preview_title = tk.StringVar(value="Ejemplo de título")
        self.preview_scene = tk.StringVar(value="Ejemplo de escena con personajes en un entorno dramático")
        
        # Llamar al método que crea y posiciona los widgets
        self._setup_widgets()
        
        # Cargar la lista de prompts
        self._load_prompt_list()
    
    def _setup_widgets(self):
        """Configura la interfaz de usuario para la pestaña de gestor de prompts."""
        # Título de la sección
        lbl_title = ttk.Label(self, text="Gestor de Plantillas de Prompts", 
                            style="Header.TLabel", font=("Helvetica", 14, "bold"))
        lbl_title.pack(pady=10)
        
        # Notebook de pestañas
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame para prompts de imágenes
        self.frame_img = ttk.Frame(self.tabs, style="Card.TFrame")
        self.tabs.add(self.frame_img, text="Prompts de Imágenes")
        
        # Frame para prompts de scripts
        self.frame_script = ttk.Frame(self.tabs, style="Card.TFrame")
        self.tabs.add(self.frame_script, text="Prompts de Guion")
        
        # Configurar cada pestaña
        self._setup_prompt_tab(self.frame_img, tipo="imagen")
        self._setup_prompt_tab(self.frame_script, tipo="script")
    
    def _setup_prompt_tab(self, parent_frame, tipo="imagen"):
        # PanedWindow para dividir lista/editor
        paned_window = ttk.PanedWindow(parent_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=10, pady=10)
        left_frame = ttk.Frame(paned_window, style="Card.TFrame")
        right_frame = ttk.Frame(paned_window, style="Card.TFrame")
        paned_window.add(left_frame, weight=1)
        paned_window.add(right_frame, weight=3)
        # Lista y editor según tipo
        if tipo == "imagen":
            self._setup_prompt_list(left_frame, tipo)
            self._setup_prompt_editor(right_frame, tipo)
            self._load_prompt_list(tipo)
        else:
            self._setup_prompt_list(left_frame, tipo)
            self._setup_prompt_editor(right_frame, tipo)
            self._load_prompt_list(tipo)
    
    def _setup_prompt_list(self, parent_frame, tipo="imagen"):
        """Configura la lista de prompts en el frame izquierdo"""
        frame_list = ttk.LabelFrame(parent_frame, text="Plantillas Disponibles")
        frame_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        listbox = tk.Listbox(frame_list, height=15, width=30, font=("Helvetica", 11))
        listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.config(yscrollcommand=scrollbar.set)
        
        if tipo == "imagen":
            self.prompt_listbox_img = listbox
            self.prompt_listbox_img.bind('<<ListboxSelect>>', lambda e: self._on_prompt_selected(e, "imagen"))
        else:
            self.prompt_listbox_script = listbox
            self.prompt_listbox_script.bind('<<ListboxSelect>>', lambda e: self._on_prompt_selected(e, "script"))
        
        # Frame para botones de acción
        frame_buttons = ttk.Frame(parent_frame)
        frame_buttons.pack(fill="x", padx=5, pady=5)
        
        # Botón para nueva plantilla
        btn_new = ttk.Button(frame_buttons, text="Nueva Plantilla", command=lambda: self._new_prompt(tipo))
        btn_new.pack(side="left", fill="x", expand=True, padx=2, pady=5)
        
        # Botón para eliminar plantilla
        btn_delete = ttk.Button(frame_buttons, text="Eliminar", command=lambda: self._delete_prompt(tipo))
        btn_delete.pack(side="right", fill="x", expand=True, padx=2, pady=5)
    
    def _setup_prompt_editor(self, parent_frame, tipo="imagen"):
        """Configura el editor de prompts en el frame derecho"""
        editor_container = ttk.Frame(parent_frame)
        editor_container.pack(fill="both", expand=True, padx=5, pady=5)
        editor_scrollbar = ttk.Scrollbar(editor_container, orient="vertical")
        editor_scrollbar.pack(side="right", fill="y")
        editor_canvas = tk.Canvas(editor_container, yscrollcommand=editor_scrollbar.set)
        editor_canvas.pack(side="left", fill="both", expand=True)
        editor_scrollbar.config(command=editor_canvas.yview)
        frame_editor = ttk.Frame(editor_canvas)
        frame_editor_window = editor_canvas.create_window((0, 0), window=frame_editor, anchor="nw")
        def configure_scroll_region(event):
            editor_canvas.configure(scrollregion=editor_canvas.bbox("all"))
            editor_canvas.itemconfig(frame_editor_window, width=editor_canvas.winfo_width())
        frame_editor.bind("<Configure>", configure_scroll_region)
        editor_canvas.bind("<Configure>", lambda e: editor_canvas.itemconfig(frame_editor_window, width=editor_canvas.winfo_width()))
        def _on_mousewheel(event):
            editor_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        editor_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        header_frame = ttk.Frame(frame_editor)
        header_frame.pack(fill="x", padx=10, pady=(10, 20))
        lbl_editor_title = ttk.Label(header_frame, text="Editar Plantilla de Prompt", font=("Helvetica", 12, "bold"))
        lbl_editor_title.pack(side="left")
        btn_save = ttk.Button(header_frame, text="Guardar Cambios", command=lambda: self._save_prompt(tipo))
        btn_save.pack(side="right", padx=10)
        frame_id = ttk.Frame(frame_editor)
        frame_id.pack(fill="x", padx=10, pady=5)
        lbl_id = ttk.Label(frame_id, text="ID:", width=15)
        lbl_id.pack(side="left", padx=5)
        self.entry_id = ttk.Entry(frame_id, textvariable=self.current_prompt_id_img if tipo == "imagen" else self.current_prompt_id_script)
        self.entry_id.pack(side="left", fill="x", expand=True, padx=5)
        frame_name = ttk.Frame(frame_editor)
        frame_name.pack(fill="x", padx=10, pady=5)
        lbl_name = ttk.Label(frame_name, text="Nombre:", width=15)
        lbl_name.pack(side="left", padx=5)
        entry_name = ttk.Entry(frame_name, textvariable=self.prompt_name_img if tipo == "imagen" else self.prompt_name_script)
        entry_name.pack(side="left", fill="x", expand=True, padx=5)
        frame_desc = ttk.Frame(frame_editor)
        frame_desc.pack(fill="x", padx=10, pady=5)
        lbl_desc = ttk.Label(frame_desc, text="Descripción:", width=15)
        lbl_desc.pack(side="left", padx=5)
        entry_desc = ttk.Entry(frame_desc, textvariable=self.prompt_description_img if tipo == "imagen" else self.prompt_description_script)
        entry_desc.pack(side="left", fill="x", expand=True, padx=5)
        lbl_system = ttk.Label(frame_editor, text="System Prompt (instrucciones para el modelo):")
        lbl_system.pack(anchor="w", padx=10, pady=(20, 5))
        system_frame = ttk.Frame(frame_editor)
        system_frame.pack(fill="both", expand=True, padx=10, pady=5)
        system_scrollbar_y = ttk.Scrollbar(system_frame, orient="vertical")
        system_scrollbar_y.pack(side="right", fill="y")
        system_scrollbar_x = ttk.Scrollbar(system_frame, orient="horizontal")
        system_scrollbar_x.pack(side="bottom", fill="x")
        if tipo == "imagen":
            self.text_system_img = tk.Text(system_frame, height=10, wrap="word", yscrollcommand=system_scrollbar_y.set, xscrollcommand=system_scrollbar_x.set)
            self.text_system_img.pack(side="left", fill="both", expand=True)
            system_scrollbar_y.config(command=self.text_system_img.yview)
            system_scrollbar_x.config(command=self.text_system_img.xview)
            btn_popup_system = ttk.Button(system_frame, text="Editar en ventana", command=lambda: self._open_popup_editor(self.text_system_img, "System Prompt"))
            btn_popup_system.pack(side="left", padx=5)
        else:
            self.text_system_script = tk.Text(system_frame, height=10, wrap="word", yscrollcommand=system_scrollbar_y.set, xscrollcommand=system_scrollbar_x.set)
            self.text_system_script.pack(side="left", fill="both", expand=True)
            system_scrollbar_y.config(command=self.text_system_script.yview)
            system_scrollbar_x.config(command=self.text_system_script.xview)
            btn_popup_system = ttk.Button(system_frame, text="Editar en ventana", command=lambda: self._open_popup_editor(self.text_system_script, "System Prompt"))
            btn_popup_system.pack(side="left", padx=5)
        lbl_user = ttk.Label(frame_editor, text="User Prompt (usa {titulo} y {escena} como placeholders):")
        lbl_user.pack(anchor="w", padx=10, pady=(20, 5))
        user_frame = ttk.Frame(frame_editor)
        user_frame.pack(fill="both", expand=True, padx=10, pady=5)
        user_scrollbar_y = ttk.Scrollbar(user_frame, orient="vertical")
        user_scrollbar_y.pack(side="right", fill="y")
        user_scrollbar_x = ttk.Scrollbar(user_frame, orient="horizontal")
        user_scrollbar_x.pack(side="bottom", fill="x")
        if tipo == "imagen":
            self.text_user_img = tk.Text(user_frame, height=10, wrap="word", yscrollcommand=user_scrollbar_y.set, xscrollcommand=user_scrollbar_x.set)
            self.text_user_img.pack(side="left", fill="both", expand=True)
            user_scrollbar_y.config(command=self.text_user_img.yview)
            user_scrollbar_x.config(command=self.text_user_img.xview)
            btn_popup_user = ttk.Button(user_frame, text="Editar en ventana", command=lambda: self._open_popup_editor(self.text_user_img, "User Prompt"))
            btn_popup_user.pack(side="left", padx=5)
        else:
            self.text_user_script = tk.Text(user_frame, height=10, wrap="word", yscrollcommand=user_scrollbar_y.set, xscrollcommand=user_scrollbar_x.set)
            self.text_user_script.pack(side="left", fill="both", expand=True)
            user_scrollbar_y.config(command=self.text_user_script.yview)
            user_scrollbar_x.config(command=self.text_user_script.xview)
            btn_popup_user = ttk.Button(user_frame, text="Editar en ventana", command=lambda: self._open_popup_editor(self.text_user_script, "User Prompt"))
            btn_popup_user.pack(side="left", padx=5)
        lbl_negative = ttk.Label(frame_editor, text="Prompt Negativo:")
        lbl_negative.pack(anchor="w", padx=10, pady=(20, 5))
        negative_frame = ttk.Frame(frame_editor)
        negative_frame.pack(fill="both", expand=True, padx=10, pady=5)
        negative_scrollbar_y = ttk.Scrollbar(negative_frame, orient="vertical")
        negative_scrollbar_y.pack(side="right", fill="y")
        negative_scrollbar_x = ttk.Scrollbar(negative_frame, orient="horizontal")
        negative_scrollbar_x.pack(side="bottom", fill="x")
        if tipo == "imagen":
            self.text_negative_img = tk.Text(negative_frame, height=6, wrap="word", yscrollcommand=negative_scrollbar_y.set, xscrollcommand=negative_scrollbar_x.set)
            self.text_negative_img.pack(side="left", fill="both", expand=True)
            negative_scrollbar_y.config(command=self.text_negative_img.yview)
            negative_scrollbar_x.config(command=self.text_negative_img.xview)
        else:
            self.text_negative_script = tk.Text(negative_frame, height=6, wrap="word", yscrollcommand=negative_scrollbar_y.set, xscrollcommand=negative_scrollbar_x.set)
            self.text_negative_script.pack(side="left", fill="both", expand=True)
            negative_scrollbar_y.config(command=self.text_negative_script.yview)
            negative_scrollbar_x.config(command=self.text_negative_script.xview)
        ttk.Label(frame_editor, text="").pack(pady=20)
    
    def _load_prompt_list(self, tipo="imagen"):
        """Carga la lista de prompts disponibles en el listbox"""
        if tipo == "imagen":
            self.prompt_listbox_img.delete(0, tk.END)
            prompt_ids = self.prompt_manager.get_prompt_ids()
            for prompt_id in prompt_ids:
                prompt_info = self.prompt_manager.get_prompt(prompt_id)
                if prompt_info:
                    display_text = f"{prompt_info['name']} ({prompt_id})"
                    self.prompt_listbox_img.insert(tk.END, display_text)
        else:
            self.prompt_listbox_script.delete(0, tk.END)
            style_names = self.script_prompt_manager.get_style_names()
            for style_id, name in style_names:
                display_text = f"{name} ({style_id})"
                self.prompt_listbox_script.insert(tk.END, display_text)
    
    def _on_prompt_selected(self, event, tipo="imagen"):
        """Maneja el evento de selección de un prompt en la lista"""
        # Obtener el índice seleccionado
        selection = self.prompt_listbox_img.curselection() if tipo == "imagen" else self.prompt_listbox_script.curselection()
        if not selection:
            return
        
        # Obtener el texto seleccionado
        selected_text = self.prompt_listbox_img.get(selection[0]) if tipo == "imagen" else self.prompt_listbox_script.get(selection[0])
        
        # Extraer el ID del prompt del texto seleccionado
        prompt_id = selected_text.split("(")[-1].strip(")")
        
        # Cargar la información del prompt
        self._load_prompt(prompt_id, tipo)
    
    def _load_prompt(self, prompt_id, tipo="imagen"):
        """Carga la información de un prompt en el editor"""
        if tipo == "imagen":
            prompt_info = self.prompt_manager.get_prompt(prompt_id)
            self.current_prompt_id_img.set(prompt_id)
            self.prompt_name_img.set(prompt_info.get("name", ""))
            self.prompt_description_img.set(prompt_info.get("description", ""))
            self.text_system_img.delete(1.0, tk.END)
            self.text_system_img.insert(tk.END, prompt_info.get("system_prompt", ""))
            self.text_user_img.delete(1.0, tk.END)
            self.text_user_img.insert(tk.END, prompt_info.get("user_prompt", ""))
            self.text_negative_img.delete(1.0, tk.END)
            self.text_negative_img.insert(tk.END, prompt_info.get("negative_prompt", ""))
        else:
            prompt_info = self.script_prompt_manager.get_style_data(prompt_id)
            self.current_prompt_id_script.set(prompt_id)
            self.prompt_name_script.set(prompt_info.get("name", ""))
            self.prompt_description_script.set(prompt_info.get("description", ""))
            self.text_system_script.delete(1.0, tk.END)
            self.text_system_script.insert(tk.END, prompt_info.get("esquema", ""))
            self.text_user_script.delete(1.0, tk.END)
            self.text_user_script.insert(tk.END, prompt_info.get("seccion", ""))
            self.text_negative_script.delete(1.0, tk.END)
            self.text_negative_script.insert(tk.END, prompt_info.get("revision", ""))
        if prompt_id in ["default", "terror", "animacion"]:
            self.entry_id.config(state="disabled")
        else:
            self.entry_id.config(state="normal")
    
    def _new_prompt(self, tipo="imagen"):
        """Prepara el editor para crear una nueva plantilla de prompt"""
        base_id = "custom"
        if tipo == "imagen":
            prompt_ids = self.prompt_manager.get_prompt_ids()
        else:
            prompt_ids = self.script_prompt_manager.get_style_names()
        counter = 1
        new_id = f"{base_id}_{counter}"
        while new_id in prompt_ids:
            counter += 1
            new_id = f"{base_id}_{counter}"
        if tipo == "imagen":
            self.current_prompt_id_img.set(new_id)
            self.prompt_name_img.set("Nuevo Estilo")
            self.prompt_description_img.set("Descripción del estilo")
            self.text_system_img.delete(1.0, tk.END)
            self.text_system_img.insert(tk.END, DEFAULT_PROMPT_TEMPLATE["system_prompt"])
            self.text_user_img.delete(1.0, tk.END)
            self.text_user_img.insert(tk.END, DEFAULT_PROMPT_TEMPLATE["user_prompt"])
            self.text_negative_img.delete(1.0, tk.END)
            self.text_negative_img.insert(tk.END, DEFAULT_PROMPT_TEMPLATE["negative_prompt"])
        else:
            self.current_prompt_id_script.set(new_id)
            self.prompt_name_script.set("Nuevo Estilo")
            self.prompt_description_script.set("Descripción del estilo")
            self.text_system_script.delete(1.0, tk.END)
            self.text_system_script.insert(tk.END, "")
            self.text_user_script.delete(1.0, tk.END)
            self.text_user_script.insert(tk.END, "")
            self.text_negative_script.delete(1.0, tk.END)
            self.text_negative_script.insert(tk.END, "")
        self.entry_id.config(state="normal")
    
    def _save_prompt(self, tipo="imagen"):
        """Guarda la plantilla de prompt actual"""
        if tipo == "imagen":
            prompt_id = self.current_prompt_id_img.get().strip()
            name = self.prompt_name_img.get().strip()
            description = self.prompt_description_img.get().strip()
            system_prompt = self.text_system_img.get(1.0, tk.END).strip()
            user_prompt = self.text_user_img.get(1.0, tk.END).strip()
            negative = self.text_negative_img.get(1.0, tk.END).strip()
        else:
            prompt_id = self.current_prompt_id_script.get().strip()
            name = self.prompt_name_script.get().strip()
            description = self.prompt_description_script.get().strip()
            system_prompt = self.text_system_script.get(1.0, tk.END).strip()
            user_prompt = self.text_user_script.get(1.0, tk.END).strip()
            negative = self.text_negative_script.get(1.0, tk.END).strip()
        if not prompt_id or not name or not system_prompt or not user_prompt:
            messagebox.showerror("Error", "Los campos ID, Nombre, System Prompt y User Prompt son obligatorios.")
            return
        if not re.match(r'^[a-zA-Z0-9_]+$', prompt_id):
            messagebox.showerror("Error", "El ID solo puede contener letras, números y guiones bajos.")
            return
        if tipo == "imagen":
            if "{titulo}" not in user_prompt and "{escena}" not in user_prompt:
                messagebox.showerror("Error", "El User Prompt debe contener al menos uno de los placeholders {titulo} o {escena}.")
                return
        print(f"Guardando prompt con ID: {prompt_id}")
        print(f"Ruta del archivo de prompts: {self.prompt_manager.prompts_file if tipo == 'imagen' else self.script_prompt_manager.filepath}")
        if tipo == "imagen":
            prompt_ids = self.prompt_manager.get_prompt_ids()
        else:
            prompt_ids = self.script_prompt_manager.get_style_names()
        print(f"Prompts existentes: {prompt_ids}")
        if tipo == "imagen":
            if prompt_id in prompt_ids:
                result = self.prompt_manager.update_prompt(
                    prompt_id, name, description, system_prompt, user_prompt, negative
                )
            else:
                result = self.prompt_manager.add_prompt(
                    prompt_id, name, description, system_prompt, user_prompt, negative
                )
        else:
            # Guardar los campos mapeados en el JSON de scripts
            data = {
                "name": name,
                "description": description,
                "esquema": system_prompt,
                "seccion": user_prompt,
                "revision": negative,
                "metadata": ""  # Puedes añadir un campo de metadatos vacío o gestionarlo aparte
            }
            if prompt_id in [id_ for id_, _ in prompt_ids]:
                result = self.script_prompt_manager.update_style(prompt_id, data)
            else:
                result = self.script_prompt_manager.update_style(prompt_id, data)
        if tipo == "imagen":
            verificacion = self.prompt_manager.get_prompt(prompt_id)
        else:
            verificacion = self.script_prompt_manager.get_style_data(prompt_id)
        if result and verificacion:
            messagebox.showinfo("Éxito", f"Plantilla '{name}' guardada correctamente.")
            self._update_dropdowns_in_other_tabs()
        elif not result:
            messagebox.showerror("Error", "No se pudo guardar la plantilla.")
        else:
            messagebox.showerror("Error", "La plantilla se guardó pero no se pudo verificar.")
        self._load_prompt_list(tipo)
    
    def _update_dropdowns_in_other_tabs(self):
        """Actualiza los dropdowns de estilos de prompts en otras pestañas"""
        # Llamar a la función del módulo prompt_updater
        update_dropdowns_in_other_tabs(self.app)
    
    def _delete_prompt(self, tipo="imagen"):
        """Elimina la plantilla de prompt seleccionada"""
        # Obtener el ID del prompt
        prompt_id = self.current_prompt_id_img.get().strip() if tipo == "imagen" else self.current_prompt_id_script.get().strip()
        if not prompt_id:
            messagebox.showerror("Error", "No hay ninguna plantilla seleccionada.")
            return
        
        # Confirmar la eliminación
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de eliminar la plantilla '{prompt_id}'?"):
            if tipo == "imagen":
                result = self.prompt_manager.delete_prompt(prompt_id)
            else:
                result = self.script_prompt_manager.delete_style(prompt_id)
            if result:
                messagebox.showinfo("Éxito", f"Plantilla '{prompt_id}' eliminada correctamente.")
                # Actualizar los dropdowns en otras pestañas
                self._update_dropdowns_in_other_tabs()
                
                # Limpiar el editor
                if tipo == "imagen":
                    self.current_prompt_id_img.set("")
                    self.prompt_name_img.set("")
                    self.prompt_description_img.set("")
                    self.text_system_img.delete(1.0, tk.END)
                    self.text_user_img.delete(1.0, tk.END)
                    self.text_negative_img.delete(1.0, tk.END)
                else:
                    self.current_prompt_id_script.set("")
                    self.prompt_name_script.set("")
                    self.prompt_description_script.set("")
                    self.text_system_script.delete(1.0, tk.END)
                    self.text_user_script.delete(1.0, tk.END)
                    self.text_negative_script.delete(1.0, tk.END)
                
                # Recargar la lista de prompts
                self._load_prompt_list(tipo)
            else:
                messagebox.showerror("Error", f"No se pudo eliminar la plantilla '{prompt_id}'.")
    
    def _open_popup_editor(self, text_widget, title):
        """Abre un pop-up grande para editar el contenido de un campo de texto."""
        popup = tk.Toplevel(self)
        popup.title(f"Editar {title}")
        popup.geometry("800x500")
        popup.transient(self)
        popup.grab_set()
        lbl = ttk.Label(popup, text=title, font=("Helvetica", 12, "bold"))
        lbl.pack(pady=10)
        text_popup = tk.Text(popup, wrap="word", font=("Helvetica", 12))
        text_popup.pack(fill="both", expand=True, padx=10, pady=10)
        # Copiar el contenido actual
        text_popup.insert(tk.END, text_widget.get(1.0, tk.END))
        def guardar_y_cerrar():
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, text_popup.get(1.0, tk.END))
            popup.destroy()
        btn_guardar = ttk.Button(popup, text="Guardar y cerrar", command=guardar_y_cerrar)
        btn_guardar.pack(pady=10)
