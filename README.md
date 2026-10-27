# App de Diseño Experimental

Aplicación educativa multipágina desarrollada con Streamlit para apoyar el curso
de Diseño Experimental de Ingeniería Agrícola de la Universidad de Sucre. Permite
explorar diseños experimentales, analizar datos y contrastar los resultados con
la interpretación y los cálculos del estudiante.

## Módulos

| Módulo | Diseño | Estado |
|---|---|---|
| DCA | Diseño completamente al azar | Disponible |
| DBCA | Diseño de bloques completos al azar | En construcción |
| DCL | Diseño de cuadrado latino | En construcción |
| DPD | Diseño de parcelas divididas | En construcción |
| Factoriales | Diseños factoriales | En construcción |
| RSM | Metodología de superficie de respuesta | En construcción |

## Estructura del proyecto

```text
.
├── app.py                     # Portada de la aplicación
├── pages/                     # Páginas de cada diseño experimental
├── utils/                     # Funciones reutilizables para análisis y diagnóstico
├── data/                      # Datos de ejemplo en formatos como CSV
├── verificacion/              # Scripts para contrastar análisis, por ejemplo en R
├── requirements.txt           # Dependencias de Python
└── README.md                  # Documentación del proyecto
```

## Instalación y ejecución

### VS Code local en Windows (PowerShell)

Desde la carpeta del proyecto, crea el entorno virtual, actívalo e instala las
dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Después inicia la aplicación:

```powershell
streamlit run app.py
```

### GitHub Codespaces

En la terminal del Codespace, instala las dependencias y ejecuta la aplicación:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit mostrará la dirección para abrir la aplicación en el navegador.

## Autoría y uso de inteligencia artificial

- **Autor:** Escribe aquí tu nombre. Reemplaza este texto por el nombre del autor
  o autores del proyecto.
- **Uso de IA:** Se utilizaron herramientas de inteligencia artificial como apoyo
  para desarrollar y documentar partes del proyecto. El estudiante o autor debe
  revisar el código, verificar los resultados estadísticos y declarar el uso de
  IA según las normas académicas del curso.
