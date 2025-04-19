#!/usr/bin/env python3
# Script para corregir la indentación en tab_batch.py

import re
import os
from pathlib import Path

def fix_indentation():
    # Ruta al archivo tab_batch.py
    file_path = Path("ui/tab_batch.py")
    
    if not file_path.exists():
        print(f"Error: No se encontró el archivo {file_path}")
        return False
    
    # Leer el contenido del archivo
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Buscar el método _add_project_to_queue
    start_line = -1
    end_line = -1
    
    for i, line in enumerate(lines):
        if "def _add_project_to_queue" in line:
            start_line = i
        elif start_line != -1 and "def _clear_project_fields" in line:
            end_line = i
            break
    
    if start_line == -1 or end_line == -1:
        print("No se pudo encontrar el método _add_project_to_queue o _clear_project_fields")
        return False
    
    # Corregir la indentación de las líneas problemáticas
    fixed_lines = lines.copy()
    
    # Corregir las líneas desde 640 hasta 702 (aproximadamente)
    for i in range(start_line + 89, end_line):  # +89 es aproximadamente la línea 640
        if not lines[i].startswith("        ") and lines[i].strip() and not lines[i].startswith("    def"):
            fixed_lines[i] = "        " + lines[i]
    
    # Guardar el archivo corregido
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(fixed_lines)
    
    print(f"Se ha corregido la indentación en {file_path}")
    return True

if __name__ == "__main__":
    fix_indentation()
