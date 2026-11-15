# Rehabilitación sostenible · Análisis arquitectónico · 15/11/2026

Versión ampliada de la herramienta del TFM. Incluye importación CSV/ZIP, prioridades por m² y anuales, diagnóstico CEE, escenarios CRREM, entorno social INE, revisión de incidencias, análisis arquitectónico e informe PDF.

## Datos y sesiones

Cada visitante debe importar su CSV o ZIP. Los archivos y las revisiones se conservan durante su sesión, aislados de las demás. Descarga los resultados y el historial antes de salir. No se incluyen archivos de trabajo, bases locales, respuestas de consultas territoriales ni datos de ejemplo en el nuevo paquete. Los archivos antiguos de la raíz pertenecen al historial y no se cargan.

Los CEE contienen valores calculados, no consumos medidos. CRREM conserva los controles de datos insuficientes. La renta describe el entorno censal y no la situación de los hogares. El análisis entre semejantes y el modelo estadístico son exploratorios y mantienen sus advertencias.

## Ejecución

Community Cloud: rama `analisis-arquitectonico-2026-11-15`, archivo `app.py`, Python 3.12. `app.py` comprueba la huella del ZIP, extrae la fuente y adapta el almacenamiento al uso por sesión. Las reglas y los cálculos del programa local se conservan.

Para ejecutar localmente, extrae `version_analisis_2026_11_15.zip`, entra en `Herramienta_TFM`, instala `requirements.txt` y ejecuta `python -m streamlit run app.py`. Esa ejecución directa utiliza almacenamiento local del equipo.

## Versión anterior

La rama `main`, la publicación anterior y la etiqueta `v2026-11-12-estable` se conservan sin cambios. Recuperación: https://github.com/oriolneila/tfm-priorizacion-rehabilitacion/releases/tag/v2026-11-12-estable

La aplicación anterior sigue en https://eqiib5anprgd8p4xkpuy8r.streamlit.app/ . Esta ampliación se despliega por separado.
