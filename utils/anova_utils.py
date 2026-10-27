"""Funciones reutilizables para el análisis de un diseño completamente al azar."""

import json
import warnings
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pandas as pd
from scipy.stats import studentized_range
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.regression.linear_model import RegressionResultsWrapper


def cargar_datos(archivo: str | Path | BinaryIO) -> pd.DataFrame:
    """Carga datos desde un archivo CSV o Excel.

    Args:
        archivo: Ruta o archivo binario con extensión `.csv` o `.xlsx`.

    Returns:
        Un DataFrame con los datos del archivo.

    Raises:
        ValueError: Si la extensión no corresponde a CSV o Excel XLSX.
    """
    # Paso 1: identificar la extensión, incluyendo archivos cargados desde Streamlit.
    nombre = getattr(archivo, "name", archivo)
    extension = Path(str(nombre)).suffix.lower()

    # Paso 2: leer Excel directamente; en CSV, pandas infiere si el separador es coma o punto y coma.
    if extension == ".xlsx":
        return pd.read_excel(archivo)
    if extension == ".csv":
        return pd.read_csv(archivo, sep=None, engine="python")

    raise ValueError("Formato no compatible. Cargue un archivo CSV o Excel (.xlsx).")


def validar_dca(df: pd.DataFrame, col_trat: str, col_resp: str) -> list[str]:
    """Valida las columnas y las réplicas necesarias para analizar un DCA.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna con los tratamientos.
        col_resp: Nombre de la columna con la respuesta.

    Returns:
        Lista de errores en español; queda vacía si los datos son válidos.
    """
    errores: list[str] = []

    # Paso 1: comprobar que las dos variables del modelo estén presentes.
    faltantes = [col for col in (col_trat, col_resp) if col not in df.columns]
    if faltantes:
        return [f"Falta la columna requerida: {col}." for col in faltantes]

    # Paso 2: reportar celdas vacías en las variables que intervienen en el análisis.
    if df[[col_trat, col_resp]].isna().any().any():
        errores.append("Hay datos faltantes en las columnas de tratamiento o respuesta.")

    # Paso 3: comprobar que la respuesta pueda interpretarse como una variable numérica.
    respuesta_numerica = pd.to_numeric(df[col_resp], errors="coerce")
    valores_no_numericos = respuesta_numerica.isna() & df[col_resp].notna()
    if valores_no_numericos.any():
        errores.append("La columna de respuesta debe contener valores numéricos.")

    # Paso 4: comprobar que se comparen al menos dos tratamientos.
    conteos = df[col_trat].value_counts(dropna=True)
    if len(conteos) < 2:
        errores.append("Se requieren al menos dos tratamientos.")

    # Paso 5: cada tratamiento necesita al menos dos réplicas para estimar el error experimental.
    if (conteos < 2).any():
        errores.append("Cada tratamiento debe tener al menos dos réplicas.")

    return errores


def ajustar_dca(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> RegressionResultsWrapper:
    """Ajusta el modelo lineal de un diseño completamente al azar.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna con los tratamientos.
        col_resp: Nombre de la columna con la respuesta.

    Returns:
        Modelo OLS ajustado.

    Raises:
        ValueError: Si los datos no cumplen las condiciones básicas para un DCA.
    """
    # Paso 1: impedir que el modelo se ajuste cuando hay problemas en los datos.
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError("No se puede ajustar el DCA: " + " ".join(errores))

    # Paso 2: Q protege nombres de columna con espacios, tildes o caracteres especiales.
    respuesta = json.dumps(col_resp, ensure_ascii=False)
    tratamiento = json.dumps(col_trat, ensure_ascii=False)
    formula = f"Q({respuesta}) ~ C(Q({tratamiento}))"

    # Paso 3: ajustar Y_ij = mu + tau_i + epsilon_ij por mínimos cuadrados ordinarios.
    return ols(formula, data=df).fit()


def tabla_anova(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Construye la tabla ANOVA tipo II de un modelo DCA.

    Args:
        modelo: Modelo OLS ajustado para un DCA.

    Returns:
        Tabla ANOVA con fuentes, grados de libertad, sumas de cuadrados,
        cuadrados medios, estadístico F y p-valor.
    """
    # Paso 1: obtener la partición de variabilidad mediante ANOVA tipo II.
    anova = anova_lm(modelo, typ=2)
    fila_trat = anova.iloc[0]
    fila_error = anova.iloc[-1]

    # Paso 2: calcular cada cuadrado medio como CM = SC / gl.
    cm_trat = fila_trat["sum_sq"] / fila_trat["df"]
    cm_error = fila_error["sum_sq"] / fila_error["df"]

    # Paso 3: completar la fila total sumando las fuentes de variación del DCA.
    suma_total = fila_trat["sum_sq"] + fila_error["sum_sq"]
    gl_total = fila_trat["df"] + fila_error["df"]

    # Paso 4: presentar resultados con encabezados en español.
    return pd.DataFrame(
        [
            {
                "Fuente": "Tratamientos",
                "gl": fila_trat["df"],
                "SC": fila_trat["sum_sq"],
                "CM": cm_trat,
                "F": fila_trat["F"],
                "p-valor": fila_trat["PR(>F)"],
            },
            {
                "Fuente": "Error",
                "gl": fila_error["df"],
                "SC": fila_error["sum_sq"],
                "CM": cm_error,
                "F": np.nan,
                "p-valor": np.nan,
            },
            {
                "Fuente": "Total",
                "gl": gl_total,
                "SC": suma_total,
                "CM": np.nan,
                "F": np.nan,
                "p-valor": np.nan,
            },
        ],
        columns=["Fuente", "gl", "SC", "CM", "F", "p-valor"],
    )


def resumen_tratamientos(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> pd.DataFrame:
    """Resume el número de réplicas y la respuesta por tratamiento.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna con los tratamientos.
        col_resp: Nombre de la columna con la respuesta.

    Returns:
        DataFrame con n, total, media y desviación estándar para cada tratamiento.
    """
    # Paso 1: agrupar las observaciones para calcular n_i, suma, media y desviación estándar.
    return (
        df.groupby(col_trat, dropna=False)[col_resp]
        .agg(
            n="count",
            total="sum",
            media="mean",
            **{"desviación estándar": "std"},
        )
        .reset_index()
    )


def coeficiente_variacion(
    modelo: RegressionResultsWrapper, df: pd.DataFrame, col_resp: str
) -> float:
    """Calcula el coeficiente de variación residual del experimento.

    Args:
        modelo: Modelo OLS ajustado para un DCA.
        df: Datos del experimento.
        col_resp: Nombre de la columna con la respuesta.

    Returns:
        Coeficiente de variación en porcentaje.

    Raises:
        ValueError: Si la media general es cero o no está definida.
    """
    # Paso 1: obtener la media general de la respuesta experimental.
    media_general = pd.to_numeric(df[col_resp], errors="raise").mean()
    if not np.isfinite(media_general) or media_general == 0:
        raise ValueError("El CV no se puede calcular si la media general es cero o no está definida.")

    # Paso 2: estimar el error experimental con el cuadrado medio residual (CME).
    cme = modelo.mse_resid

    # Paso 3: expresar el error típico como porcentaje de la media: CV = sqrt(CME) / media * 100.
    return float(np.sqrt(cme) / media_general * 100)


def tukey(
    df: pd.DataFrame,
    col_trat: str,
    col_resp: str,
    alfa: float = 0.05,
) -> tuple[pd.DataFrame, float]:
    """Realiza comparaciones de Tukey y calcula una DMS para el DCA.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna con los tratamientos.
        col_resp: Nombre de la columna con la respuesta.
        alfa: Nivel de significancia entre cero y uno.

    Returns:
        Tupla con comparaciones de Tukey en español y la DMS calculada.

    Raises:
        ValueError: Si los datos del DCA no son válidos o alfa no está entre cero y uno.
    """
    # Paso 1: validar el nivel de significancia y las observaciones usadas en las comparaciones.
    if not 0 < alfa < 1:
        raise ValueError("Alfa debe ser mayor que cero y menor que uno.")
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError("No se puede realizar Tukey: " + " ".join(errores))

    # Paso 2: calcular Tukey HSD sobre las respuestas agrupadas por tratamiento.
    comparacion = pairwise_tukeyhsd(
        endog=pd.to_numeric(df[col_resp], errors="raise"),
        groups=df[col_trat],
        alpha=alfa,
    )
    tabla = pd.DataFrame(
        comparacion._results_table.data[1:],
        columns=[
            "Tratamiento 1",
            "Tratamiento 2",
            "Diferencia de medias",
            "p-valor ajustado",
            "Límite inferior",
            "Límite superior",
            "Rechaza H0",
        ],
    )
    tabla["Diferencia de medias"] = pd.to_numeric(tabla["Diferencia de medias"])
    tabla["p-valor ajustado"] = pd.to_numeric(tabla["p-valor ajustado"])
    tabla["Límite inferior"] = pd.to_numeric(tabla["Límite inferior"])
    tabla["Límite superior"] = pd.to_numeric(tabla["Límite superior"])
    tabla["Rechaza H0"] = tabla["Rechaza H0"].map(
        lambda valor: bool(valor)
        if isinstance(valor, (bool, np.bool_))
        else str(valor).lower() == "true"
    )

    # Paso 3: usar las réplicas comunes; en un desbalance, aproximarlas con la media armónica.
    conteos = df.groupby(col_trat)[col_resp].count().to_numpy(dtype=float)
    balanceado = np.all(conteos == conteos[0])
    if balanceado:
        replicas = float(conteos[0])
    else:
        replicas = float(len(conteos) / np.sum(1 / conteos))
        warnings.warn(
            "El diseño no está balanceado; la DMS calculada con la media armónica "
            "de réplicas es aproximada.",
            UserWarning,
            stacklevel=2,
        )

    # Paso 4: calcular CME residual y el cuantil q(alfa; t; glE) de rango studentizado.
    modelo = ajustar_dca(df, col_trat, col_resp)
    cme = modelo.mse_resid
    tratamientos = len(conteos)
    gl_error = modelo.df_resid
    q_critico = studentized_range.ppf(1 - alfa, tratamientos, gl_error)

    # Paso 5: aplicar DMS = q(alfa; t; glE) * sqrt(CME / r).
    dms = q_critico * np.sqrt(cme / replicas)
    return tabla, float(dms)


def interpretar_dca(tabla: pd.DataFrame, alfa: float = 0.05) -> str:
    """Interpreta la prueba F de tratamientos en palabras sencillas.

    Args:
        tabla: Tabla ANOVA generada por `tabla_anova`.
        alfa: Nivel de significancia entre cero y uno.

    Returns:
        Interpretación de la decisión sobre la hipótesis nula de igualdad de medias.

    Raises:
        ValueError: Si alfa no es válido o la tabla no contiene el p-valor de tratamientos.
    """
    # Paso 1: comprobar que alfa y la fila de tratamientos permitan tomar una decisión.
    if not 0 < alfa < 1:
        raise ValueError("Alfa debe ser mayor que cero y menor que uno.")
    if "Fuente" not in tabla.columns or "p-valor" not in tabla.columns:
        raise ValueError("La tabla debe incluir las columnas 'Fuente' y 'p-valor'.")
    filas = tabla.loc[tabla["Fuente"] == "Tratamientos", "p-valor"]
    if filas.empty or pd.isna(filas.iloc[0]):
        raise ValueError("La tabla no contiene un p-valor válido para Tratamientos.")
    p_valor = float(filas.iloc[0])

    # Paso 2: comparar p con alfa; H0 plantea igualdad de medias entre todos los tratamientos.
    if p_valor <= alfa:
        return (
            f"Se rechaza H0 (p = {p_valor:.4g} <= alfa = {alfa:.4g}). "
            "Hay evidencia de diferencias entre las medias de los tratamientos; "
            "la decisión agrícola debe considerar cuáles tratamientos difieren."
        )
    return (
        f"No se rechaza H0 (p = {p_valor:.4g} > alfa = {alfa:.4g}). "
        "No hay evidencia suficiente de diferencias entre las medias; "
        "con estos datos no se justifica elegir un tratamiento como superior."
    )
