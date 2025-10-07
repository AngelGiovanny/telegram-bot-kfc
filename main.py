import os
import sys

# Agregar el directorio actual al path para importaciones
sys.path.append(os.path.dirname(__file__))

from bot.main import main

if __name__ == '__main__':
    main()