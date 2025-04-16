import os

def print_directory_tree(path, prefix=''):
    """
    Imprime un árbol de directorios de forma recursiva.
    
    Args:
        path (str): Ruta del directorio a explorar.
        prefix (str): Prefijo para la indentación de los niveles.
    """
    try:
        # Obtener lista de archivos y directorios
        items = sorted(os.listdir(path))
        for index, item in enumerate(items):
            item_path = os.path.join(path, item)
            # Determinar si es el último elemento para ajustar el prefijo
            if index == len(items) - 1:
                new_prefix = prefix + '└── '
                extension = '    '
            else:
                new_prefix = prefix + '├── '
                extension = '│   '
            # Imprimir el elemento actual
            print(new_prefix + item)
            # Si es un directorio, explorar recursivamente
            if os.path.isdir(item_path):
                print_directory_tree(item_path, prefix + extension)
    except PermissionError:
        print(prefix + '└── [Acceso denegado]')
    except Exception as e:
        print(prefix + f'└── [Error: {str(e)}]')

if __name__ == '__main__':
    project_root = os.path.dirname(os.path.abspath(__file__))
    print(f'Árbol de directorios del proyecto en: {project_root}')
    print_directory_tree(project_root)
