#!/usr/bin/env python3
# Script para corregir el problema con script_mode en tab_batch.py

import re
import os
from pathlib import Path

def fix_tab_batch():
    # Ruta al archivo tab_batch.py
    file_path = Path("ui/tab_batch.py")
    
    if not file_path.exists():
        print(f"Error: No se encontró el archivo {file_path}")
        return False
    
    # Leer el contenido del archivo
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Realizar la sustitución de script_mode por modo_seleccionado
    new_content = re.sub(r'\bscript_mode\b', 'modo_seleccionado', content)
    
    # Guardar el contenido modificado
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"Se ha corregido el archivo {file_path}")
    return True

if __name__ == "__main__":
    fix_tab_batch()
