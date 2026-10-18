"""Interfaz del MVP para el TFM de rehabilitación sostenible."""
import streamlit as st
import pandas as pd
from pathlib import Path
from motor import cargar_archivo, normalizar, calidad, calcular_escenarios, resumen_calidad, exportar_csv

st.set_page_config(page_title="Priorización de rehabilitación | TFM", page_icon="🏘️", layout="wide")
st.title("🏘️ Priorización de rehabilitación sostenible")
st.caption("Prototipo de investigación · Desempeño energético, emisiones calculadas y entorno social")
st.warning("**Importante:** no calcula CRREM ni consumo operacional real. El ranking es exploratorio, relativo a la muestra, y NO indica qué edificio debe rehabilitarse sin revisión técnica.")

st.sidebar.header("1. Datos")
origen = st.sidebar.radio("Conjunto de trabajo", ["Ejemplo sintético (prueba)", "Importar CSV / ZIP"], index=0)
if origen.startswith("Ejemplo"):
    path = Path(__file__).parent / "ejemplo_SINTETICO.csv"
    raw = cargar_archivo(path.name, path.read_bytes())
    st.info("🧪 **DATOS SINTÉTICOS:** los edificios, valores y rentas del archivo de ejemplo son ficticios y no representan inmuebles reales de Madrid.")
else:
    file = st.sidebar.file_uploader("Registro CEEE Madrid o CSV propio", type=["csv", "zip"])
    if file is None:
        st.info("Sube un CSV del registro energético o un archivo CSV propio. En la carpeta hay un ejemplo para ver qué columnas admite.")
        st.stop()
    try:
        raw = cargar_archivo(file.name, file.getvalue())
    except Exception as exc:
        st.error(f"No se ha podido abrir el archivo: {exc}")
        st.stop()

with st.expander("Ver origen y equivalencia de los campos", expanded=False):
    st.write("Columnas leídas:", list(raw.columns))

try:
    data, matched = normalizar(raw)
    flags = calidad(data)
except Exception as exc:
    st.error(f"Error al interpretar los datos: {exc}")
    st.stop()

with st.expander("Columnas reconocidas", expanded=False):
    st.dataframe(pd.DataFrame([{"campo_interno": k, "columna_en_archivo": v} for k,v in matched.items()]), hide_index=True)

st.sidebar.header("2. Filtrado")
mun = sorted(flags["municipio"].dropna().unique().tolist())
sel = st.sidebar.multiselect("Municipios (vacío = todos)", mun, default=[]) if len(mun) > 1 else []
fil = flags[flags["municipio"].isin(sel)].copy() if sel else flags.copy()
# Selección explícita de tipologías; nunca asumimos "edificio completo" por defecto.
tipos = sorted(flags["tipo_certificado"].dropna().unique().tolist())
sel_tipos = st.sidebar.multiselect("Tipo certificado (vacío = todos; revisar manualmente)", tipos, default=[])
if sel_tipos:
    fil = fil[fil["tipo_certificado"].isin(sel_tipos)].copy()
# No se infiere que un certificado de parte del edificio sea un edificio completo.
exclude_duplicates = st.sidebar.checkbox("Apartar referencias catastrales repetidas", value=False)
if exclude_duplicates:
    fil = fil[~fil["alerta_refcat_repetida"]].copy()
exclude_multiref = st.sidebar.checkbox("Apartar certificados con varias referencias", value=False)
if exclude_multiref:
    fil = fil[~fil["alerta_refcat_multiple"]].copy()
exclude_missing_type = st.sidebar.checkbox("Apartar registros sin tipo de inmueble", value=False)
if exclude_missing_type:
    fil = fil[~fil["alerta_tipo"]].copy()

st.sidebar.header("3. Pesos del escenario social")
st.sidebar.caption("Tres pesos suman 100 %. No sustituyen una justificación metodológica.")
w_e = st.sidebar.slider("Energía (%)", 0, 100, 50)
w_c = st.sidebar.slider("Emisiones CEE (%)", 0, 100, 30)
w_s = 100 - w_e - w_c
if w_s < 0:
    st.sidebar.error("Energía + emisiones no puede superar el 100 %.")
    st.stop()
st.sidebar.markdown(f"**Entorno social: {w_s} %**")

res = calcular_escenarios(fil, pesos=(w_e/100, w_c/100, w_s/100))
if res.empty:
    st.warning("No quedan registros con los filtros actuales.")
    st.stop()

st.subheader("1. Alcance de la muestra")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Registros cargados", f"{len(raw):,}".replace(",", "."))
col2.metric("Registros incluidos", f"{len(res):,}".replace(",", "."))
col3.metric("Con EPNR válida", f"{res['epnren'].ge(0).sum():,}".replace(",", "."))
col4.metric("Con renta territorial", f"{res['renta_territorial'].gt(0).sum():,}".replace(",", "."))
st.caption("**Unidad de análisis pendiente de verificar:** cada fila puede ser un edificio, una parte o una vivienda; la referencia catastral por sí sola no resuelve esa diferencia.")

st.subheader("2. Control de calidad")
st.write("Incidencias del archivo completo (antes de filtros):")
st.dataframe(resumen_calidad(flags), hide_index=True)
st.write("Incidencias de los registros incluidos:")
st.dataframe(resumen_calidad(res), hide_index=True)
with st.expander("Revisar filas e incidencias"):
    st.dataframe(res[["id_visual", "referencia", "municipio", "tipo_certificado", "numero_alertas", "alerta_epnren", "alerta_emisiones", "alerta_refcat_repetida", "alerta_refcat_multiple", "alerta_renta"]], hide_index=True)

st.subheader("3. Comparación de escenarios")
st.write("**Escenario 1:** solo energía primaria no renovable del certificado (CEE). **Escenario 2:** 60 % energía y 40 % emisiones calculadas del CEE. **Escenario 3:** combinación ajustable de energía, emisiones CEE y renta territorial (menor renta = mayor valor relativo de vulnerabilidad).")
st.info("La dimensión climática en estos escenarios es **emisiones calculadas del CEE**, no alineamiento con CRREM. Las dos magnitudes energéticas pueden estar correlacionadas; los pesos son de demostración.")
cols = {"escenario_1_energia": "Energía", "escenario_2_energia_emisiones": "Energía + CO₂ CEE", "escenario_3_con_contexto_social": "Energía + CO₂ CEE + entorno social"}
selected = st.selectbox("Escenario para ordenar", list(cols), format_func=lambda x: cols[x])
if res[selected].notna().sum() == 0:
    st.warning("No se puede calcular este escenario: faltan campos obligatorios o algún peso requiere indicadores ausentes.")
else:
    visible = res.sort_values(selected, ascending=False, na_position="last")
    display = ["id_visual", "municipio", "tipo_certificado", "epnren", "emisiones", "renta_territorial", selected, "puesto_"+selected]
    st.dataframe(visible[display], hide_index=True, use_container_width=True)
    graph = visible.head(20).dropna(subset=[selected])[["id_visual", selected]].set_index("id_visual")
    if not graph.empty:
        st.bar_chart(graph, horizontal=True)

st.subheader("4. Cambios entre rankings")
if res["escenario_1_energia"].notna().sum() and res["escenario_2_energia_emisiones"].notna().sum():
    rank_cols = ["id_visual", "puesto_escenario_1_energia", "puesto_escenario_2_energia_emisiones", "puesto_escenario_3_con_contexto_social"]
    rank_view = res[rank_cols].copy()
    rank_view["cambio_S1_a_S2"] = rank_view["puesto_escenario_1_energia"] - rank_view["puesto_escenario_2_energia_emisiones"]
    rank_view["cambio_S1_a_S3"] = rank_view["puesto_escenario_1_energia"] - rank_view["puesto_escenario_3_con_contexto_social"]
    st.dataframe(rank_view, hide_index=True, use_container_width=True)
    st.caption("Cambio positivo = sube hacia las primeras posiciones. Si falta un indicador, el puesto queda vacío; no se sustituye por cero.")

st.subheader("5. Exportación y trazabilidad")
st.download_button("📥 Descargar resultados completos (CSV)", data=exportar_csv(res), file_name="tfm_ranking_exploratorio.csv", mime="text/csv")
st.write("Columnas reconocidas:", ", ".join(f"{k} ← {v}" for k,v in matched.items()) or "Ninguna")
st.caption("Los porcentajes son posiciones relativas dentro del conjunto analizado: cambiar la muestra puede cambiar el ranking. No existe todavía un test externo de validez ni una evaluación CRREM.")
