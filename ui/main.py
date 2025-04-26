import tkinter as tk
from tkinter import messagebox
from tkinter import ttk




class MainWindow:
    def __init__(self, app):
        self.app = app  # Guardar referencia a la aplicación principal
        
        # Variables de control
        self.selected_aspect_ratio = tk.StringVar(value="16:9")
        self.selected_image_prompt = tk.StringVar()
        self.selected_script_prompt = tk.StringVar()

        # Inicializar la interfaz
        self._inicializar_interfaz()

    def _recargar_prompts_imagenes(self):
        """Recarga los prompts disponibles para imágenes"""
        if not self.app.prompt_manager:
            messagebox.showerror("Error", "El gestor de prompts no está disponible")
            return
            
        try:
            # Obtener los IDs y nombres de los prompts disponibles
            prompts = self.app.prompt_manager.get_prompt_names()
            self.combo_prompt_imagenes['values'] = [name for _, name in prompts]
            if prompts:
                self.selected_image_prompt.set(prompts[0][1])  # Usar el nombre del primer prompt
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar prompts de imágenes: {str(e)}")

    def _recargar_prompts_scripts(self):
        """Recarga los prompts disponibles para scripts"""
        if not self.app.prompt_manager:
            messagebox.showerror("Error", "El gestor de prompts no está disponible")
            return
            
        try:
            # Obtener los IDs y nombres de los prompts disponibles
            prompts = self.app.prompt_manager.get_prompt_names()
            self.combo_prompt_scripts['values'] = [name for _, name in prompts]
            if prompts:
                self.selected_script_prompt.set(prompts[0][1])  # Usar el nombre del primer prompt
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar prompts de scripts: {str(e)}")

    def _inicializar_interfaz(self):
        """Inicializa los widgets de la interfaz principal."""
        # Frame principal
        self.frame_principal = ttk.Frame(self.app.root, style="Card.TFrame")
        self.frame_principal.pack(fill="both", expand=True, padx=10, pady=10)

        # Frame para los prompts
        frame_prompts = ttk.LabelFrame(self.frame_principal, text="Prompts", style="Card.TFrame")
        frame_prompts.pack(fill="x", padx=5, pady=5)

        # Prompts de imágenes
        frame_imagenes = ttk.Frame(frame_prompts)
        frame_imagenes.pack(fill="x", padx=5, pady=5)
        ttk.Label(frame_imagenes, text="Prompt de imágenes:").pack(side="left", padx=5)
        self.combo_prompt_imagenes = ttk.Combobox(frame_imagenes, textvariable=self.selected_image_prompt, state="readonly")
        self.combo_prompt_imagenes.pack(side="left", fill="x", expand=True, padx=5)
        btn_recargar_imagenes = ttk.Button(frame_imagenes, text="🔄", command=self._recargar_prompts_imagenes, width=3)
        btn_recargar_imagenes.pack(side="left", padx=5)

        # Prompts de scripts
        frame_scripts = ttk.Frame(frame_prompts)
        frame_scripts.pack(fill="x", padx=5, pady=5)
        ttk.Label(frame_scripts, text="Prompt de scripts:").pack(side="left", padx=5)
        self.combo_prompt_scripts = ttk.Combobox(frame_scripts, textvariable=self.selected_script_prompt, state="readonly")
        self.combo_prompt_scripts.pack(side="left", fill="x", expand=True, padx=5)
        btn_recargar_scripts = ttk.Button(frame_scripts, text="🔄", command=self._recargar_prompts_scripts, width=3)
        btn_recargar_scripts.pack(side="left", padx=5)

        # Frame para aspect ratio
        frame_aspect = ttk.LabelFrame(self.frame_principal, text="Aspect Ratio", style="Card.TFrame")
        frame_aspect.pack(fill="x", padx=5, pady=5)
        
        # Radio buttons para aspect ratio
        frame_ratio = ttk.Frame(frame_aspect)
        frame_ratio.pack(fill="x", padx=5, pady=5)
        ttk.Radiobutton(frame_ratio, text="16:9", variable=self.selected_aspect_ratio, value="16:9").pack(side="left", padx=5)
        ttk.Radiobutton(frame_ratio, text="9:16", variable=self.selected_aspect_ratio, value="9:16").pack(side="left", padx=5)

        # Cargar los prompts iniciales
        self._recargar_prompts_imagenes()
        self._recargar_prompts_scripts() 