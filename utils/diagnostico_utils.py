"""Funciones para diagnosticar supuestos de modelos de diseño experimental."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import levene, probplot, shapiro
from statsmodels.regression.linear_model import RegressionResultsWrapper


def residuos_y_ajustados(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Obtiene los residuos y valores ajustados del modelo.

    Args:
        modelo: Modelo OLS ajustado para el experimento.

    Returns:
        DataFrame con los valores ajustados y los residuos correspondientes.
    """
    # Paso 1: extraer los valores observados menos los estimados: e_i = y_i - ŷ_i.
    return pd.DataFrame(
        {
            "Ajustados": np.asarray(modelo.fittedvalues),
            "Residuos": np.asarray(modelo.resid),
        }
    )


def prueba_shapiro(
    residuos: pd.Series | np.ndarray | list[float], alfa: float = 0.05
) -> tuple[float, float, str]:
    """Evalúa la normalidad de los residuos con la prueba de Shapiro-Wilk.

    Args:
        residuos: Residuos del modelo ajustado.
        alfa: Nivel de significancia para la decisión.

    Returns:
        Estadístico W, p-valor y conclusión en español.

    Raises:
        ValueError: Si hay menos de tres residuos o alfa no es válido.
    """
    # Paso 1: preparar observaciones finitas; Shapiro-Wilk requiere al menos tres datos.
    valores = np.asarray(residuos, dtype=float)
    valores = valores[np.isfinite(valores)]
    if not 0 < alfa < 1:
        raise ValueError("Alfa debe ser mayor que cero y menor que uno.")
    if len(valores) < 3:
        raise ValueError("La prueba de Shapiro-Wilk requiere al menos tres residuos válidos.")

    # Paso 2: calcular W; la hipótesis nula plantea que los residuos siguen una distribución normal.
    estadistico, p_valor = shapiro(valores)
    if p_valor > alfa:
        conclusion = (
            f"No se rechaza la normalidad (p = {p_valor:.4g} > α = {alfa:.4g}); "
            "no se detecta evidencia suficiente contra el supuesto."
        )
    else:
        conclusion = (
            f"Se rechaza la normalidad (p = {p_valor:.4g} ≤ α = {alfa:.4g}); "
            "los residuos muestran evidencia de desviación de la normalidad."
        )
    return float(estadistico), float(p_valor), conclusion


def prueba_levene(
    df: pd.DataFrame,
    col_trat: str,
    col_resp: str,
    alfa: float = 0.05,
) -> tuple[float, float, str]:
    """Evalúa la igualdad de varianzas entre tratamientos con Levene.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna con los tratamientos.
        col_resp: Nombre de la columna con la respuesta.
        alfa: Nivel de significancia para la decisión.

    Returns:
        Estadístico de Levene, p-valor y conclusión en español.

    Raises:
        ValueError: Si faltan columnas, hay menos de dos grupos válidos o alfa no es válido.
    """
    # Paso 1: comprobar columnas y nivel de significancia antes de formar grupos.
    if col_trat not in df.columns or col_resp not in df.columns:
        raise ValueError("No se encontró la columna de tratamiento o de respuesta.")
    if not 0 < alfa < 1:
        raise ValueError("Alfa debe ser mayor que cero y menor que uno.")

    # Paso 2: preparar respuestas numéricas por grupo, excluyendo faltantes.
    grupos: list[np.ndarray] = []
    for _, datos_grupo in df.groupby(col_trat, dropna=True):
        respuestas = pd.to_numeric(datos_grupo[col_resp], errors="coerce").dropna()
        if len(respuestas):
            grupos.append(respuestas.to_numpy(dtype=float))
    if len(grupos) < 2:
        raise ValueError("La prueba de Levene requiere al menos dos tratamientos con datos.")
    if any(len(grupo) < 2 for grupo in grupos):
        raise ValueError("Cada tratamiento necesita al menos dos observaciones para Levene.")

    # Paso 3: usar medianas por grupo para mayor robustez: Levene evalúa H0 de varianzas iguales.
    estadistico, p_valor = levene(*grupos, center="median")
    if p_valor > alfa:
        conclusion = (
            f"No se rechaza la igualdad de varianzas (p = {p_valor:.4g} > α = {alfa:.4g}); "
            "no se detecta evidencia suficiente de heterogeneidad."
        )
    else:
        conclusion = (
            f"Se rechaza la igualdad de varianzas (p = {p_valor:.4g} ≤ α = {alfa:.4g}); "
            "hay evidencia de varianzas diferentes entre tratamientos."
        )
    return float(estadistico), float(p_valor), conclusion


def grafico_residuos_vs_ajustados(
    modelo: RegressionResultsWrapper,
) -> go.Figure:
    """Crea un gráfico para detectar patrones en residuos y valores ajustados.

    Args:
        modelo: Modelo OLS ajustado para el experimento.

    Returns:
        Gráfico de dispersión de residuos frente a valores ajustados.
    """
    # Paso 1: comparar e_i = y_i - ŷ_i con ŷ_i; una nube aleatoria alrededor de cero es esperada.
    datos_grafico = residuos_y_ajustados(modelo)
    figura = px.scatter(
        datos_grafico,
        x="Ajustados",
        y="Residuos",
        labels={"Ajustados": "Valores ajustados", "Residuos": "Residuos"},
        title="Residuos frente a valores ajustados",
    )
    figura.add_hline(y=0, line_dash="dash", line_color="red")
    figura.update_layout(template="plotly_white")
    return figura


def grafico_qq(residuos: pd.Series | np.ndarray | list[float]) -> go.Figure:
    """Crea un gráfico Q-Q para comparar residuos con una distribución normal.

    Args:
        residuos: Residuos del modelo ajustado.

    Returns:
        Gráfico Q-Q con cuantiles observados y línea de referencia normal.

    Raises:
        ValueError: Si hay menos de dos residuos finitos.
    """
    # Paso 1: obtener cuantiles teóricos y observados; bajo normalidad deben aproximarse a una recta.
    valores = np.asarray(residuos, dtype=float)
    valores = valores[np.isfinite(valores)]
    if len(valores) < 2:
        raise ValueError("El gráfico Q-Q requiere al menos dos residuos válidos.")
    (cuantiles_teoricos, cuantiles_observados), (pendiente, intercepto, _) = probplot(
        valores, dist="norm"
    )

    # Paso 2: contrastar cuantiles muestrales con los teóricos y mostrar la referencia lineal.
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=cuantiles_teoricos,
            y=cuantiles_observados,
            mode="markers",
            name="Residuos",
        )
    )
    extremos = np.array([cuantiles_teoricos[0], cuantiles_teoricos[-1]])
    figura.add_trace(
        go.Scatter(
            x=extremos,
            y=intercepto + pendiente * extremos,
            mode="lines",
            name="Referencia normal",
        )
    )
    figura.update_layout(
        title="Gráfico Q-Q de los residuos",
        xaxis_title="Cuantiles teóricos normales",
        yaxis_title="Cuantiles observados",
        template="plotly_white",
    )
    return figura
