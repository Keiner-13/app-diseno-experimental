from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.stats import f as distribucion_f

from utils.anova_utils import (
    ajustar_dca,
    cargar_datos,
    coeficiente_variacion,
    interpretar_dca,
    resumen_tratamientos,
    tabla_anova,
    tukey,
    validar_dca,
)
from utils.diagnostico_utils import (
    grafico_qq,
    grafico_residuos_vs_ajustados,
    prueba_levene,
    prueba_shapiro,
    residuos_y_ajustados,
)

RUTA_DATOS_EJEMPLO = Path(__file__).resolve().parents[1] / "data" / "dca_secadores.csv"


@st.cache_data
def cargar_datos_cache(contenido: bytes | None, nombre_archivo: str) -> pd.DataFrame:
    """Carga y conserva en caché un archivo experimental.

    Args:
        contenido: Contenido binario del archivo cargado; None usa los datos de ejemplo.
        nombre_archivo: Nombre del archivo, necesario para reconocer su formato.

    Returns:
        Datos experimentales leídos desde CSV o Excel.
    """
    # La lectura delega en la utilidad compartida para mantener iguales las reglas de importación.
    if contenido is None:
        return cargar_datos(RUTA_DATOS_EJEMPLO)

    archivo = BytesIO(contenido)
    archivo.name = nombre_archivo
    return cargar_datos(archivo)


st.title("Diseño completamente al azar (DCA)")
st.write(
    "El DCA compara tratamientos asignados al azar cuando las unidades experimentales "
    "son homogéneas. En este ejemplo se compara la humedad final de yuca secada en "
    "cuatro secadores solares, con cuatro réplicas por secador."
)

archivo_cargado = st.file_uploader(
    "Carga los datos del experimento",
    type=["csv", "xlsx"],
    help="El archivo debe tener una columna de tratamiento y otra de respuesta.",
)

try:
    if archivo_cargado is None:
        st.caption("No se cargó un archivo; se usan los datos de ejemplo data/dca_secadores.csv.")
        datos = cargar_datos_cache(None, RUTA_DATOS_EJEMPLO.name)
    else:
        datos = cargar_datos_cache(archivo_cargado.getvalue(), archivo_cargado.name)
except (OSError, ValueError, ImportError) as error:
    st.error(f"No fue posible cargar el archivo: {error}")
    st.stop()

if datos.empty or len(datos.columns) == 0:
    st.error("El archivo no contiene datos ni columnas para analizar.")
    st.stop()

columnas = datos.columns.tolist()
columnas_numericas = datos.select_dtypes(include="number").columns.tolist()
col_trat_sugerida = next(
    (col for col in columnas if col not in columnas_numericas),
    columnas[0],
)
col_resp_sugerida = (
    columnas_numericas[-1] if columnas_numericas else columnas[-1]
)

col_selector_trat, col_selector_resp = st.columns(2)
with col_selector_trat:
    col_trat = st.selectbox(
        "Columna de tratamiento",
        options=columnas,
        index=columnas.index(col_trat_sugerida),
    )
with col_selector_resp:
    col_resp = st.selectbox(
        "Columna de respuesta",
        options=columnas,
        index=columnas.index(col_resp_sugerida),
    )

alfa = st.slider(
    "Nivel de significancia (α)",
    min_value=0.01,
    max_value=0.10,
    value=0.05,
    step=0.01,
    format="%.2f",
)

errores = validar_dca(datos, col_trat, col_resp)
if errores:
    for mensaje in errores:
        st.error(mensaje)
    st.stop()

try:
    # El modelo estima medias de tratamientos y el error experimental: Y_ij = μ + τ_i + ε_ij.
    modelo = ajustar_dca(datos, col_trat, col_resp)
    anova = tabla_anova(modelo)
    resumen = resumen_tratamientos(datos, col_trat, col_resp)
    cv = coeficiente_variacion(modelo, datos, col_resp)
except (ValueError, KeyError, TypeError) as error:
    st.error(f"No fue posible analizar los datos: {error}")
    st.stop()

p_tratamientos = float(
    anova.loc[anova["Fuente"] == "Tratamientos", "p-valor"].iloc[0]
)
gl_tratamientos = int(
    anova.loc[anova["Fuente"] == "Tratamientos", "gl"].iloc[0]
)
gl_error = int(anova.loc[anova["Fuente"] == "Error", "gl"].iloc[0])

tab_datos, tab_anova, tab_comparaciones, tab_graficos, tab_supuestos = st.tabs(
    ["Datos", "ANOVA", "Comparaciones", "Gráficos", "Supuestos"]
)

with tab_datos:
    st.subheader("Datos del experimento")
    st.dataframe(datos, hide_index=True, width="stretch")
    st.subheader("Resumen por tratamiento")
    st.dataframe(
        resumen.style.format(
            {
                "total": "{:.4f}",
                "media": "{:.4f}",
                "desviación estándar": "{:.4f}",
            },
            na_rep="—",
        ),
        hide_index=True,
        width="stretch",
    )

with tab_anova:
    st.subheader("Análisis de varianza")
    st.dataframe(
        anova.style.format(
            {
                "gl": "{:.0f}",
                "SC": "{:.4f}",
                "CM": "{:.4f}",
                "F": "{:.4f}",
                "p-valor": "{:.4f}",
            },
            na_rep="—",
        ),
        hide_index=True,
        width="stretch",
    )

    # La F crítica es el cuantil 1 - α de la distribución F con gl de tratamientos y del error.
    f_critica = distribucion_f.ppf(1 - alfa, gl_tratamientos, gl_error)
    st.metric("F crítica", f"{f_critica:.4f}")
    st.metric("Coeficiente de variación (CV)", f"{cv:.4f} %")

    interpretacion = interpretar_dca(anova, alfa)
    if p_tratamientos <= alfa:
        st.success(interpretacion)
    else:
        st.info(interpretacion)

with tab_comparaciones:
    st.subheader("Comparaciones múltiples")
    if p_tratamientos < alfa:
        try:
            # Tukey controla el error familiar al comparar todas las parejas de medias.
            tabla_tukey, dms = tukey(datos, col_trat, col_resp, alfa)
            st.dataframe(
                tabla_tukey.style.format(
                    {
                        "Diferencia de medias": "{:.4f}",
                        "p-valor ajustado": "{:.4f}",
                        "Límite inferior": "{:.4f}",
                        "Límite superior": "{:.4f}",
                    },
                    na_rep="—",
                ),
                hide_index=True,
                width="stretch",
            )
            st.metric("DMS de Tukey", f"{dms:.4f}")
            if resumen["n"].nunique() > 1:
                st.warning(
                    "El diseño no está balanceado; la DMS se calculó como aproximación "
                    "usando la media armónica de las réplicas."
                )
        except (ValueError, KeyError, TypeError) as error:
            st.error(f"No fue posible calcular las comparaciones: {error}")
    else:
        st.info(
            "No se realiza la prueba de Tukey porque el ANOVA no detectó diferencias "
            f"significativas entre tratamientos (p = {p_tratamientos:.4f} ≥ α = {alfa:.2f})."
        )

with tab_graficos:
    st.subheader("Distribución de las observaciones")
    grafico_cajas = px.box(
        datos,
        x=col_trat,
        y=col_resp,
        points="all",
        labels={col_trat: "Tratamiento", col_resp: "Respuesta"},
        title="Respuesta por tratamiento",
    )
    st.plotly_chart(grafico_cajas, width="stretch")

    st.subheader("Media de respuesta por tratamiento")
    grafico_medias = px.bar(
        resumen,
        x=col_trat,
        y="media",
        labels={col_trat: "Tratamiento", "media": "Media de la respuesta"},
        title="Medias por tratamiento",
    )
    st.plotly_chart(grafico_medias, width="stretch")

with tab_supuestos:
    st.subheader("Diagnóstico de supuestos del DCA")
    st.write(
        "Los supuestos ayudan a evaluar si el modelo ANOVA describe adecuadamente "
        "la variabilidad observada. Las pruebas son diagnósticas y deben interpretarse "
        "junto con los gráficos y el conocimiento del ensayo."
    )

    st.markdown(
        "**Normalidad:** Shapiro-Wilk evalúa si los residuos del modelo son compatibles "
        "con una distribución normal. En el gráfico Q-Q, los puntos deberían seguir "
        "aproximadamente la línea de referencia."
    )
    st.markdown(
        "**Homogeneidad de varianzas:** Levene, usando la mediana, evalúa si la "
        "variabilidad de la respuesta es semejante entre tratamientos."
    )
    st.markdown(
        "**Independencia:** no se determina con Shapiro-Wilk ni con Levene. En un DCA "
        "se sustenta principalmente en la asignación aleatoria de tratamientos y en "
        "la independencia del manejo y medición de cada unidad experimental."
    )

    try:
        # Los residuos e_i = y_i - ŷ_i permiten revisar normalidad y patrones frente al ajuste.
        datos_residuos = residuos_y_ajustados(modelo)
        estadistico_shapiro, p_shapiro, conclusion_shapiro = prueba_shapiro(
            datos_residuos["Residuos"], alfa
        )
        estadistico_levene, p_levene, conclusion_levene = prueba_levene(
            datos, col_trat, col_resp, alfa
        )
    except (ValueError, KeyError, TypeError) as error:
        st.error(f"No fue posible completar el diagnóstico de supuestos: {error}")
    else:
        st.subheader("Pruebas de supuestos")
        tabla_supuestos = pd.DataFrame(
            [
                {
                    "Supuesto": "Normalidad de los residuos",
                    "Prueba": "Shapiro-Wilk",
                    "Estadístico": estadistico_shapiro,
                    "p-valor": p_shapiro,
                    "Conclusión": conclusion_shapiro,
                },
                {
                    "Supuesto": "Homogeneidad de varianzas",
                    "Prueba": "Levene (centro: mediana)",
                    "Estadístico": estadistico_levene,
                    "p-valor": p_levene,
                    "Conclusión": conclusion_levene,
                },
            ]
        )
        st.dataframe(
            tabla_supuestos.style.format(
                {"Estadístico": "{:.4f}", "p-valor": "{:.4f}"},
                na_rep="—",
            ),
            hide_index=True,
            width="stretch",
        )

        col_qq, col_residuos = st.columns(2)
        with col_qq:
            st.plotly_chart(
                grafico_qq(datos_residuos["Residuos"]),
                width="stretch",
            )
        with col_residuos:
            st.plotly_chart(
                grafico_residuos_vs_ajustados(modelo),
                width="stretch",
            )
