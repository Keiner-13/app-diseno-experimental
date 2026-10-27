# Instrucciones permanentes del repositorio

- **Proyecto:** App de Diseño Experimental desarrollada en Python y Streamlit para el curso de Diseño Experimental de Ingeniería Agrícola, Universidad de Sucre.
- **Estructura:** `app.py` para la portada; `pages/` con un archivo por diseño; `utils/` para funciones reutilizables e incluir `utils/__init__.py`; `data/` para archivos CSV de ejemplo; y `verificacion/` para scripts de R.
- Escribe todo el código, comentarios, docstrings y mensajes de la interfaz en español.
- Añade en cada paso estadístico un comentario que explique qué se calcula y por qué, con una explicación adecuada para estudiantes de Ingeniería Agrícola.
- Define las funciones con anotaciones de tipos (type hints) y docstrings en estilo Google.
- Usa únicamente estas librerías: `streamlit`, `pandas`, `numpy`, `scipy`, `statsmodels`, `plotly` y `openpyxl`. No agregues otras librerías sin pedir permiso.
- Ajusta los modelos ANOVA con `statsmodels.formula.api.ols` y calcula la tabla con `statsmodels.stats.anova.anova_lm(typ=2)`.
- Realiza las comparaciones de Tukey con `statsmodels.stats.multicomp.pairwise_tukeyhsd`.
- No inventes resultados: todos los números presentados deben provenir de los cálculos ejecutados.
- Antes de terminar una tarea, ejecuta el código pertinente y corrige los errores que aparezcan.
