"""Motor reproducible de priorización exploratoria para el TFM.

No calcula una evaluación CRREM ni infiere vulnerabilidad individual.
Todos los valores de certificados se interpretan como valores calculados.
"""
from __future__ import annotations

import io
import zipfile
import pandas as pd
import numpy as np

ALIASES = {
    "referencia": ["edif_refcat", "referencia_catastral", "refcat"],
    "municipio": ["edif_muni", "municipio"],
    "direccion": ["edif_direc", "direccion"],
    "tipo_certificado": ["edif_tipo", "tipo_certificado", "tipo_certificacion"],
    "fecha_certificado": ["edif_fecha", "fecha_certificado"],
    "superficie_m2": ["edif_superf", "superficie_m2"],
    "epnren": ["norenov_global", "epnren_kwh_m2_anio"],
    "emisiones": ["norenov_co2global", "co2_kg_m2_anio"],
    "energia_final": ["final_global", "energia_final_kwh_m2_anio"],
    "clase_epnren": ["cal_norenovglobal", "clase_epnren"],
    "renta_territorial": ["renta_media_seccion_eur_persona", "renta_territorial_eur_persona"],
    "seccion_censal": ["seccion_censal"],
    "id": ["id_edificio", "edif_codreg", "id"],
    "origen": ["origen_dato", "origen"],
}

NUMERIC = ["epnren", "emisiones", "energia_final", "superficie_m2", "renta_territorial"]


def _read_csv_bytes(contents: bytes) -> pd.DataFrame:
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            sample = contents[:20000].decode(encoding)
            header = next((line for line in sample.splitlines() if line.strip()), "")
            sep = ";" if header.count(";") > header.count(",") else ","
            return pd.read_csv(io.BytesIO(contents), encoding=encoding, sep=sep, dtype=str,
                               keep_default_na=False, low_memory=False)
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
            last_error = exc
    raise ValueError(f"No se ha podido leer el CSV: {last_error}")


def cargar_archivo(nombre: str, contenido: bytes) -> pd.DataFrame:
    """Lee CSV directo o primer CSV de un ZIP; avisa si contiene varios."""
    if nombre.lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(contenido)) as z:
            candidatos = [n for n in z.namelist() if n.lower().endswith(".csv") and not n.startswith("__MACOSX/")]
            if len(candidatos) != 1:
                raise ValueError(f"El ZIP contiene {len(candidatos)} CSV. Extrae y selecciona un solo CSV.")
            return _read_csv_bytes(z.read(candidatos[0]))
    if not nombre.lower().endswith(".csv"):
        raise ValueError("Se admite únicamente CSV o ZIP con un solo CSV.")
    return _read_csv_bytes(contenido)


def _a_numero(series: pd.Series) -> pd.Series:
    s = series.astype("string").str.strip().str.replace("\u00a0", "", regex=False)
    # Convención española: 1.234,56 -> 1234.56; 1234,56 -> 1234.56
    tiene_coma = s.str.contains(",", regex=False, na=False)
    s = s.where(~tiene_coma, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(s, errors="coerce")


def normalizar(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Renombra sin perder filas, con trazabilidad del origen de cada columna."""
    normalized_headers = {str(c).strip().lower(): c for c in raw.columns}
    result = pd.DataFrame(index=raw.index)
    matched = {}
    for dest, possibilities in ALIASES.items():
        source = next((normalized_headers[key.lower()] for key in possibilities if key.lower() in normalized_headers), None)
        if source is not None:
            result[dest] = raw[source]
            matched[dest] = str(source)
        else:
            result[dest] = pd.NA
    for c in NUMERIC:
        result[c] = _a_numero(result[c])
    for c in ("id", "referencia", "municipio", "direccion", "tipo_certificado", "fecha_certificado", "clase_epnren", "origen", "seccion_censal"):
        result[c] = result[c].astype("string").str.strip().replace({"": pd.NA, "nan": pd.NA})
    result["id_visual"] = result["id"].fillna("Fila-" + (pd.Series(range(1, len(result) + 1), index=result.index)).astype(str))
    return result, matched


def calidad(df: pd.DataFrame) -> pd.DataFrame:
    """No elimina registros silenciosamente; señala problemas para revisión."""
    q = df.copy()
    q["alerta_epnren"] = q["epnren"].isna() | (q["epnren"] < 0)
    q["alerta_emisiones"] = q["emisiones"].isna() | (q["emisiones"] < 0)
    q["alerta_area"] = q["superficie_m2"].isna() | (q["superficie_m2"] <= 0)
    q["alerta_tipo"] = q["tipo_certificado"].isna()
    # refcat plural / multi-referencia no resuelta automáticamente
    q["alerta_refcat_multiple"] = q["referencia"].fillna("").str.contains(r"[,;]", regex=True)
    refval = q["referencia"].str.upper().str.replace(" ", "", regex=False)
    q["alerta_refcat_repetida"] = refval.notna() & refval.duplicated(keep=False)
    q["alerta_renta"] = q["renta_territorial"].isna() | (q["renta_territorial"] <= 0)
    alert_cols = [c for c in q if c.startswith("alerta_")]
    q["numero_alertas"] = q[alert_cols].sum(axis=1).astype(int)
    return q


def porcentaje_relativo(s: pd.Series, ascendente: bool = True) -> pd.Series:
    """Percentil 0–100 con empates, comparable solo dentro de la muestra."""
    x = s.astype(float)
    valido = x.notna() & np.isfinite(x)
    result = pd.Series(np.nan, index=s.index, dtype=float)
    subset = x[valido]
    if len(subset) == 0:
        return result
    if subset.nunique() == 1:
        result.loc[valido] = 50.0  # no discrimina: todos empatan
        return result
    ranks = subset.rank(method="average", ascending=ascendente)
    result.loc[valido] = 100 * (ranks - 1) / (len(subset) - 1)
    return result


def calcular_escenarios(q: pd.DataFrame, pesos=(0.5, 0.3, 0.2)) -> pd.DataFrame:
    """Scenarios exploratory. Missing components prevent score; no reweighting by row."""
    if len(pesos) != 3 or any(w < 0 for w in pesos) or not np.isclose(sum(pesos), 1):
        raise ValueError("Los pesos deben ser >=0 y sumar 1.")
    out = q.copy()
    for name in ("epnren", "emisiones", "renta_territorial"):
        out.loc[out[name] < 0, name] = np.nan
    out.loc[out["renta_territorial"] == 0, "renta_territorial"] = np.nan
    # Más energía o emisiones -> mayor urgencia; menos renta territorial -> mayor vulnerabilidad
    out["punt_energia"] = porcentaje_relativo(out["epnren"], ascendente=True)
    out["punt_emisiones_cee"] = porcentaje_relativo(out["emisiones"], ascendente=True)
    out["punt_entorno_social"] = porcentaje_relativo(out["renta_territorial"], ascendente=False)
    out["escenario_1_energia"] = out["punt_energia"]
    out["escenario_2_energia_emisiones"] = 0.6*out["punt_energia"] + 0.4*out["punt_emisiones_cee"]
    a,b,c = pesos
    # Ignorar componentes con peso 0 sin exigir datos ausentes.
    componentes = [(a, "punt_energia"), (b, "punt_emisiones_cee"), (c, "punt_entorno_social")]
    score = pd.Series(0.0, index=out.index, dtype=float)
    for weight, key in componentes:
        if weight > 0:
            score = score + weight * out[key]
    out["escenario_3_con_contexto_social"] = score
    for col in ("escenario_1_energia", "escenario_2_energia_emisiones", "escenario_3_con_contexto_social"):
        out["puesto_" + col] = out[col].rank(method="min", ascending=False).astype("Int64")
    return out


def resumen_calidad(q: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in q if c.startswith("alerta_")]
    return pd.DataFrame({"control": cols, "registros_afectados": [int(q[c].sum()) for c in cols]})


def exportar_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig").encode("utf-8-sig")
