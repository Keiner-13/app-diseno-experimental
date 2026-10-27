import streamlit as st

AUTOR = "Escribe aquí tu nombre"

st.set_page_config(
    page_title="App de Diseño Experimental",
    page_icon="🌱",
    layout="wide",
)

st.title("App de Diseño Experimental")
st.subheader("Ingeniería Agrícola – Universidad de Sucre")
st.write(
    "El diseño experimental permite planear ensayos de campo de forma ordenada, "
    "comparar tratamientos y distinguir sus efectos de la variabilidad natural. "
    "Así se pueden tomar decisiones agrícolas con base en datos y conclusiones "
    "estadísticas apropiadas."
)

st.header("Módulos")
st.dataframe(
    [
        {
            "Módulo": "DCA — Diseño completamente al azar",
            "Cuándo se usa": "Cuando las unidades experimentales son homogéneas y los tratamientos se asignan al azar.",
            "Ejemplo agrícola": "Comparar cuatro fertilizantes en parcelas uniformes de maíz.",
            "Estado": "Disponible",
        },
        {
            "Módulo": "DBCA — Diseño en bloques completos al azar",
            "Cuándo se usa": "Cuando existe una fuente conocida de variación que puede agruparse en bloques.",
            "Ejemplo agrícola": "Comparar variedades de fríjol en bloques definidos por la pendiente del lote.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "DCL — Diseño de cuadrado latino",
            "Cuándo se usa": "Cuando se deben controlar dos fuentes de variación mediante filas y columnas.",
            "Ejemplo agrícola": "Evaluar tratamientos de riego controlando gradientes de suelo en dos direcciones.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "DPD — Diseño de parcelas divididas",
            "Cuándo se usa": "Cuando dos factores requieren distintos tamaños de parcela o niveles de aplicación.",
            "Ejemplo agrícola": "Evaluar sistemas de labranza en parcelas grandes y dosis de fertilizante en subparcelas.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "Factoriales — Diseños factoriales",
            "Cuándo se usa": "Cuando se estudian simultáneamente varios factores y sus interacciones.",
            "Ejemplo agrícola": "Estudiar variedades de arroz y dosis de nitrógeno en un mismo ensayo.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "RSM — Metodología de superficie de respuesta",
            "Cuándo se usa": "Cuando se busca modelar y optimizar una respuesta según factores cuantitativos.",
            "Ejemplo agrícola": "Optimizar la dosis de riego y fertilizante para maximizar el rendimiento de tomate.",
            "Estado": "En construcción",
        },
    ],
    hide_index=True,
    width="stretch",
)

st.header("Instrucciones de uso")
st.markdown(
    "1. Elige un módulo en el menú lateral.\n"
    "2. Carga los datos del ensayo.\n"
    "3. Revisa e interpreta los resultados.\n"
    "4. Verifica los supuestos y compara con tu cálculo manual."
)

st.warning(
    "Esta app apoya el aprendizaje. El estudiante interpreta los resultados, "
    "verifica supuestos y compara con su cálculo manual."
)

with st.sidebar:
    st.header("Información del curso")
    st.write(f"**Autor:** {AUTOR}")
    st.write("**Curso:** Diseño Experimental")
    st.write("**Semestre:** 2026-2")
