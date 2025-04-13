# -*- coding: utf-8 -*-
# Archivo: ui/tab_prompts.py

import tkinter as tk
from tkinter import ttk, messagebox
import os
import re
from pathlib import Path

from prompt_manager import PromptManager, DEFAULT_PROMPT_TEMPLATE
from ui.prompt_updater import update_dropdowns_in_other_tabs

class PromptsTabFrame(ttk.Frame):
    """
    Frame que contiene todos los widgets para la pestaña de 'Gestor de Prompts'.
    Permite crear, editar y eliminar plantillas de prompts personalizados.
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
        
        # Inicializar el gestor de prompts
        self.prompt_manager = PromptManager()
        
        # Variables para los widgets
        self.current_prompt_id = tk.StringVar()
        self.prompt_name = tk.StringVar()
        self.prompt_description = tk.StringVar()
        self.negative_prompt = tk.StringVar()
        
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
        
        # Usar un PanedWindow para dividir la pantalla en dos secciones ajustables
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame izquierdo para la lista de prompts (más estrecho)
        left_frame = ttk.Frame(paned_window, style="Card.TFrame")
        
        # Frame derecho para el editor de prompts (más ancho)
        right_frame = ttk.Frame(paned_window, style="Card.TFrame")
        
        # Añadir los frames al PanedWindow
        paned_window.add(left_frame, weight=1)  # 30% del espacio
        paned_window.add(right_frame, weight=3)  # 70% del espacio
        
        # Configurar el frame izquierdo (lista de prompts)
        self._setup_prompt_list(left_frame)
        
        # Configurar el frame derecho (editor de prompts)
        self._setup_prompt_editor(right_frame)
    
    def _setup_prompt_list(self, parent_frame):
        """Configura la lista de prompts en el frame izquierdo"""
        # Frame para la lista de prompts
        frame_list = ttk.LabelFrame(parent_frame, text="Plantillas Disponibles")
        frame_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Lista de prompts con altura aumentada
        self.prompt_listbox = tk.Listbox(frame_list, height=15, width=30, font=("Helvetica", 11))
        self.prompt_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar para la lista
        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=self.prompt_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.prompt_listbox.config(yscrollcommand=scrollbar.set)
        
        # Vincular evento de selección
        self.prompt_listbox.bind('<<ListboxSelect>>', self._on_prompt_selected)
        
        # Frame para botones de acción
        frame_buttons = ttk.Frame(parent_frame)
        frame_buttons.pack(fill="x", padx=5, pady=5)
        
        # Botón para nueva plantilla
        btn_new = ttk.Button(frame_buttons, text="Nueva Plantilla", command=self._new_prompt)
        btn_new.pack(side="left", fill="x", expand=True, padx=2, pady=5)
        
        # Botón para eliminar plantilla
        btn_delete = ttk.Button(frame_buttons, text="Eliminar", command=self._delete_prompt)
        btn_delete.pack(side="right", fill="x", expand=True, padx=2, pady=5)
    
    def _setup_prompt_editor(self, parent_frame):
        """Configura el editor de prompts en el frame derecho"""
        # Frame para el editor de prompts con scrollbar
        editor_container = ttk.Frame(parent_frame)
        editor_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar vertical para todo el editor
        editor_scrollbar = ttk.Scrollbar(editor_container, orient="vertical")
        editor_scrollbar.pack(side="right", fill="y")
        
        # Canvas para hacer scroll de todo el contenido
        editor_canvas = tk.Canvas(editor_container, yscrollcommand=editor_scrollbar.set)
        editor_canvas.pack(side="left", fill="both", expand=True)
        editor_scrollbar.config(command=editor_canvas.yview)
        
        # Frame dentro del canvas que contendrá todos los widgets
        frame_editor = ttk.Frame(editor_canvas)
        frame_editor_window = editor_canvas.create_window((0, 0), window=frame_editor, anchor="nw")
        
        # Configurar el canvas para que se ajuste al tamaño del frame
        def configure_scroll_region(event):
            editor_canvas.configure(scrollregion=editor_canvas.bbox("all"))
            # Ajustar el ancho del frame al ancho del canvas
            editor_canvas.itemconfig(frame_editor_window, width=editor_canvas.winfo_width())
            
        frame_editor.bind("<Configure>", configure_scroll_region)
        editor_canvas.bind("<Configure>", lambda e: editor_canvas.itemconfig(frame_editor_window, width=editor_canvas.winfo_width()))
        
        # Permitir scroll con la rueda del ratón
        def _on_mousewheel(event):
            editor_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        editor_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Frame para el título y botón de guardar
        header_frame = ttk.Frame(frame_editor)
        header_frame.pack(fill="x", padx=10, pady=(10, 20))
        
        # Título del editor (a la izquierda)
        lbl_editor_title = ttk.Label(header_frame, text="Editar Plantilla de Prompt", 
                                   font=("Helvetica", 12, "bold"))
        lbl_editor_title.pack(side="left")
        
        # Botón para guardar cambios (a la derecha)
        btn_save = ttk.Button(header_frame, text="Guardar Cambios", command=self._save_prompt)
        btn_save.pack(side="right", padx=10)
        
        # ID de la plantilla
        frame_id = ttk.Frame(frame_editor)
        frame_id.pack(fill="x", padx=10, pady=5)
        
        lbl_id = ttk.Label(frame_id, text="ID:", width=15)
        lbl_id.pack(side="left", padx=5)
        
        self.entry_id = ttk.Entry(frame_id, textvariable=self.current_prompt_id)
        self.entry_id.pack(side="left", fill="x", expand=True, padx=5)
        
        # Nombre de la plantilla
        frame_name = ttk.Frame(frame_editor)
        frame_name.pack(fill="x", padx=10, pady=5)
        
        lbl_name = ttk.Label(frame_name, text="Nombre:", width=15)
        lbl_name.pack(side="left", padx=5)
        
        entry_name = ttk.Entry(frame_name, textvariable=self.prompt_name)
        entry_name.pack(side="left", fill="x", expand=True, padx=5)
        
        # Descripción de la plantilla
        frame_desc = ttk.Frame(frame_editor)
        frame_desc.pack(fill="x", padx=10, pady=5)
        
        lbl_desc = ttk.Label(frame_desc, text="Descripción:", width=15)
        lbl_desc.pack(side="left", padx=5)
        
        entry_desc = ttk.Entry(frame_desc, textvariable=self.prompt_description)
        entry_desc.pack(side="left", fill="x", expand=True, padx=5)
        
        # System Prompt
        lbl_system = ttk.Label(frame_editor, text="System Prompt (instrucciones para el modelo):")
        lbl_system.pack(anchor="w", padx=10, pady=(20, 5))
        
        # Frame para el text y scrollbar del system prompt
        system_frame = ttk.Frame(frame_editor)
        system_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Scrollbar vertical para system prompt
        system_scrollbar_y = ttk.Scrollbar(system_frame, orient="vertical")
        system_scrollbar_y.pack(side="right", fill="y")
        
        # Scrollbar horizontal para system prompt
        system_scrollbar_x = ttk.Scrollbar(system_frame, orient="horizontal")
        system_scrollbar_x.pack(side="bottom", fill="x")
        
        # Text widget para system prompt con scrollbars
        self.text_system = tk.Text(system_frame, height=10, wrap="word", 
                                  yscrollcommand=system_scrollbar_y.set,
                                  xscrollcommand=system_scrollbar_x.set)
        self.text_system.pack(side="left", fill="both", expand=True)
        
        # Configurar scrollbars
        system_scrollbar_y.config(command=self.text_system.yview)
        system_scrollbar_x.config(command=self.text_system.xview)
        
        # User Prompt
        lbl_user = ttk.Label(frame_editor, text="User Prompt (usa {titulo} y {escena} como placeholders):")
        lbl_user.pack(anchor="w", padx=10, pady=(20, 5))
        
        # Frame para el text y scrollbar del user prompt
        user_frame = ttk.Frame(frame_editor)
        user_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Scrollbar vertical para user prompt
        user_scrollbar_y = ttk.Scrollbar(user_frame, orient="vertical")
        user_scrollbar_y.pack(side="right", fill="y")
        
        # Scrollbar horizontal para user prompt
        user_scrollbar_x = ttk.Scrollbar(user_frame, orient="horizontal")
        user_scrollbar_x.pack(side="bottom", fill="x")
        
        # Text widget para user prompt con scrollbars
        self.text_user = tk.Text(user_frame, height=10, wrap="word", 
                               yscrollcommand=user_scrollbar_y.set,
                               xscrollcommand=user_scrollbar_x.set)
        self.text_user.pack(side="left", fill="both", expand=True)
        
        # Configurar scrollbars
        user_scrollbar_y.config(command=self.text_user.yview)
        user_scrollbar_x.config(command=self.text_user.xview)
        
        # Nota: El campo 'Plantilla de Prompt' ha sido eliminado ya que no se utiliza
        # El sistema ahora genera los prompts directamente a partir del System Prompt y User Prompt
        
        # Prompt negativo
        lbl_negative = ttk.Label(frame_editor, text="Prompt Negativo:")
        lbl_negative.pack(anchor="w", padx=10, pady=(20, 5))
        
        # Frame para el text y scrollbar del negative prompt
        negative_frame = ttk.Frame(frame_editor)
        negative_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Scrollbar vertical para negative prompt
        negative_scrollbar_y = ttk.Scrollbar(negative_frame, orient="vertical")
        negative_scrollbar_y.pack(side="right", fill="y")
        
        # Scrollbar horizontal para negative prompt
        negative_scrollbar_x = ttk.Scrollbar(negative_frame, orient="horizontal")
        negative_scrollbar_x.pack(side="bottom", fill="x")
        
        # Text widget para negative prompt con scrollbars
        self.text_negative = tk.Text(negative_frame, height=6, wrap="word", 
                                   yscrollcommand=negative_scrollbar_y.set,
                                   xscrollcommand=negative_scrollbar_x.set)
        self.text_negative.pack(side="left", fill="both", expand=True)
        
        # Configurar scrollbars
        negative_scrollbar_y.config(command=self.text_negative.yview)
        negative_scrollbar_x.config(command=self.text_negative.xview)
        
        # Espacio adicional al final para mejorar la visualización
        ttk.Label(frame_editor, text="").pack(pady=20)
    
    def _load_prompt_list(self):
        """Carga la lista de prompts disponibles en el listbox"""
        # Limpiar la lista actual
        self.prompt_listbox.delete(0, tk.END)
        
        # Obtener los IDs de los prompts
        prompt_ids = self.prompt_manager.get_prompt_ids()
        
        # Añadir cada prompt a la lista
        for prompt_id in prompt_ids:
            prompt_info = self.prompt_manager.get_prompt(prompt_id)
            if prompt_info:
                display_text = f"{prompt_info['name']} ({prompt_id})"
                self.prompt_listbox.insert(tk.END, display_text)
    
    def _on_prompt_selected(self, event):
        """Maneja el evento de selección de un prompt en la lista"""
        # Obtener el índice seleccionado
        selection = self.prompt_listbox.curselection()
        if not selection:
            return
        
        # Obtener el texto seleccionado
        selected_text = self.prompt_listbox.get(selection[0])
        
        # Extraer el ID del prompt del texto seleccionado
        prompt_id = selected_text.split("(")[-1].strip(")")
        
        # Cargar la información del prompt
        self._load_prompt(prompt_id)
    
    def _load_prompt(self, prompt_id):
        """Carga la información de un prompt en el editor"""
        prompt_info = self.prompt_manager.get_prompt(prompt_id)
        if not prompt_info:
            return
        
        # Actualizar las variables
        self.current_prompt_id.set(prompt_id)
        self.prompt_name.set(prompt_info["name"])
        self.prompt_description.set(prompt_info["description"])
        
        # Actualizar los text widgets
        self.text_system.delete(1.0, tk.END)
        self.text_system.insert(tk.END, prompt_info.get("system_prompt", ""))
        
        self.text_user.delete(1.0, tk.END)
        self.text_user.insert(tk.END, prompt_info.get("user_prompt", ""))
        
        # El campo text_template ha sido eliminado
        
        self.text_negative.delete(1.0, tk.END)
        self.text_negative.insert(tk.END, prompt_info.get("negative_prompt", ""))
        
        # Deshabilitar la edición del ID si es una plantilla predefinida
        if prompt_id in ["default", "terror", "animacion"]:
            self.entry_id.config(state="disabled")
        else:
            self.entry_id.config(state="normal")
    
    def _new_prompt(self):
        """Prepara el editor para crear una nueva plantilla de prompt"""
        # Generar un ID único
        base_id = "custom"
        prompt_ids = self.prompt_manager.get_prompt_ids()
        
        # Encontrar un ID disponible
        counter = 1
        new_id = f"{base_id}_{counter}"
        while new_id in prompt_ids:
            counter += 1
            new_id = f"{base_id}_{counter}"
        
        # Establecer valores por defecto
        self.current_prompt_id.set(new_id)
        self.prompt_name.set("Nuevo Estilo")
        self.prompt_description.set("Descripción del estilo")
        
        # Actualizar los text widgets
        self.text_system.delete(1.0, tk.END)
        self.text_system.insert(tk.END, DEFAULT_PROMPT_TEMPLATE["system_prompt"])
        
        self.text_user.delete(1.0, tk.END)
        self.text_user.insert(tk.END, DEFAULT_PROMPT_TEMPLATE["user_prompt"])
        
        # El campo text_template ha sido eliminado
        
        self.text_negative.delete(1.0, tk.END)
        self.text_negative.insert(tk.END, DEFAULT_PROMPT_TEMPLATE["negative_prompt"])
        
        # Habilitar la edición del ID
        self.entry_id.config(state="normal")
    
    def _save_prompt(self):
        """Guarda la plantilla de prompt actual"""
        # Obtener los valores
        prompt_id = self.current_prompt_id.get().strip()
        name = self.prompt_name.get().strip()
        description = self.prompt_description.get().strip()
        system_prompt = self.text_system.get(1.0, tk.END).strip()
        user_prompt = self.text_user.get(1.0, tk.END).strip()
        negative = self.text_negative.get(1.0, tk.END).strip()
        
        # Validar los campos
        if not prompt_id or not name or not system_prompt or not user_prompt:
            messagebox.showerror("Error", "Los campos ID, Nombre, System Prompt y User Prompt son obligatorios.")
            return
        
        # Validar que el ID no contenga espacios ni caracteres especiales
        if not re.match(r'^[a-zA-Z0-9_]+$', prompt_id):
            messagebox.showerror("Error", "El ID solo puede contener letras, números y guiones bajos.")
            return
        
        # Validar que el user prompt contenga al menos uno de los placeholders {titulo} o {escena}
        if "{titulo}" not in user_prompt and "{escena}" not in user_prompt:
            messagebox.showerror("Error", "El User Prompt debe contener al menos uno de los placeholders {titulo} o {escena}.")
            return
        
        # Mostrar información de depuración
        print(f"Guardando prompt con ID: {prompt_id}")
        print(f"Ruta del archivo de prompts: {self.prompt_manager.prompts_file}")
        
        # Comprobar si es una actualización o una nueva plantilla
        prompt_ids = self.prompt_manager.get_prompt_ids()
        print(f"Prompts existentes: {prompt_ids}")
        
        if prompt_id in prompt_ids:
            # Es una actualización
            print(f"Actualizando prompt existente: {prompt_id}")
            result = self.prompt_manager.update_prompt(
                prompt_id, name, description, system_prompt, user_prompt, negative
            )
            if result:
                # Verificar que se guardó correctamente
                verificacion = self.prompt_manager.get_prompt(prompt_id)
                if verificacion:
                    messagebox.showinfo("Éxito", f"Plantilla '{name}' actualizada correctamente.")
                    print(f"Verificación exitosa: {verificacion['name']}")
                    # Actualizar los dropdowns en otras pestañas
                    self._update_dropdowns_in_other_tabs()
                else:
                    messagebox.showerror("Error", "La plantilla se actualizó pero no se pudo verificar.")
            else:
                messagebox.showerror("Error", "No se pudo actualizar la plantilla.")
        else:
            # Es una nueva plantilla
            print(f"Creando nuevo prompt: {prompt_id}")
            result = self.prompt_manager.add_prompt(
                prompt_id, name, description, system_prompt, user_prompt, negative
            )
            if result:
                # Verificar que se guardó correctamente
                verificacion = self.prompt_manager.get_prompt(prompt_id)
                if verificacion:
                    messagebox.showinfo("Éxito", f"Plantilla '{name}' creada correctamente.")
                    print(f"Verificación exitosa: {prompt_id}")
                    # Actualizar los dropdowns en otras pestañas
                    self._update_dropdowns_in_other_tabs()
                else:
                    messagebox.showerror("Error", "La plantilla se creó pero no se pudo verificar.")
            else:
                messagebox.showerror("Error", "No se pudo crear la plantilla.")
        
        # Recargar la lista de prompts
        self._load_prompt_list()
        
    def _update_dropdowns_in_other_tabs(self):
        """Actualiza los dropdowns de estilos de prompts en otras pestañas"""
        # Llamar a la función del módulo prompt_updater
        update_dropdowns_in_other_tabs(self.app)
    
    def _delete_prompt(self):
        """Elimina la plantilla de prompt seleccionada"""
        # Obtener el ID del prompt
        prompt_id = self.current_prompt_id.get().strip()
        if not prompt_id:
            messagebox.showerror("Error", "No hay ninguna plantilla seleccionada.")
            return
        
        # Confirmar la eliminación
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de eliminar la plantilla '{prompt_id}'?"):
            result = self.prompt_manager.delete_prompt(prompt_id)
            if result:
                messagebox.showinfo("Éxito", f"Plantilla '{prompt_id}' eliminada correctamente.")
                # Actualizar los dropdowns en otras pestañas
                self._update_dropdowns_in_other_tabs()
                
                # Limpiar el editor
                self.current_prompt_id.set("")
                self.prompt_name.set("")
                self.prompt_description.set("")
                self.text_system.delete(1.0, tk.END)
                self.text_user.delete(1.0, tk.END)
                self.text_negative.delete(1.0, tk.END)
                
                # Recargar la lista de prompts
                self._load_prompt_list()
            else:
                messagebox.showerror("Error", f"No se pudo eliminar la plantilla '{prompt_id}'.")
