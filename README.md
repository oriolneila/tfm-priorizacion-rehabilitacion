# Herramienta MVP — TFM de rehabilitación sostenible

**Proyecto académico:** TFM de rehabilitación sostenible.

**Estado:** prototipo exploratorio v0.1 (19/10/2026). **No** es una evaluación CRREM ni un resultado empírico del TFM.

## Cómo arrancar en Windows

1. Instala **Python 3.10 o posterior** desde python.org (marca «Add Python to PATH»).
2. Descomprime la carpeta completa en tu ordenador.
3. Haz doble clic en `iniciar_WINDOWS.bat`. La primera ejecución requiere conexión a Internet para instalar bibliotecas.
4. Se abrirá en el navegador la interfaz (habitualmente `http://localhost:8501`). Si no, copia la dirección que aparezca en la consola.

Alternativamente, en una terminal dentro de la carpeta:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Lo que permite hoy

- Importar CSV o ZIP con un único CSV, incluido el formato de columnas del **registro de certificados de Madrid**.
- Interpretar separador `;` o `,`, codificación UTF-8/Windows y números con coma decimal.
- Reconocer columnas originales (`edif_refcat`, `edif_muni`, `edif_tipo`, `edif_fecha`, `edif_superf`, `norenov_global`, `norenov_co2global`, `final_global`, etc.) o las simplificadas del ejemplo.
- Detectar valores ausentes, valores negativos, superficies inválidas, referencias catastrales repetidas o múltiples.
- Filtrar y **apartar** duplicados o múltiples referencias para revisión, sin eliminar ni fusionar silenciosamente edificios.
- Comparar tres criterios exploratorios: energía, energía+emisiones calculadas CEE y energía+emisiones CEE+renta territorial.
- Descargar la tabla completa y las alertas para documentar resultados.

## Qué NO permite ni demuestra

- **NO calcula CRREM**: EPNR (energía primaria no renovable) y emisiones CEE no son consumos operacionales completos. CRREM requiere condiciones específicas de perímetro, cobertura de energía y superficie.
- **NO se puede decir que calcula vulnerabilidad individual**: menor renta media de la sección censal es solo una variable territorial ilustrativa, si el usuario aporta un dato correspondiente a cada edificio mediante un cruce geográfico comprobado.
- **NO enlaza automáticamente Catastro ni INE** ni conoce la geometría del edificio: esos cruces son trabajos posteriores.
- **NO certifica unidades de análisis**: una fila del registro CEE puede ser edificio completo o parte de edificio; `edif_tipo` se muestra para revisión.
- **NO aplica todavía una validación estadística externa**, ni optimiza pesos para una política pública.
- Los escenarios segundo y tercero **no son metodológicamente independientes**: energía primaria y emisiones del CEE suelen estar relacionadas. La diferencia entre rankings es demostrativa, no prueba de mejora decisional.
- **NO asigna una prioridad absoluta**: los percentiles son relativos a los registros incluidos; la muestra y sus sesgos importan.
- **NO conoce si un edificio fue rehabilitado recientemente**.

## Columnas para un CSV propio

Mínimas: `id_edificio`, `municipio`, `tipo_certificado`, `epnren_kwh_m2_anio`, `co2_kg_m2_anio`.

Recomendadas: `referencia_catastral`, `superficie_m2`, `fecha_certificado`, `renta_media_seccion_eur_persona`, `seccion_censal`, `origen_dato`.

En el CSV oficial, los alias relevantes son: `edif_codreg`, `edif_muni`, `edif_tipo`, `norenov_global`, `norenov_co2global`, `edif_refcat`, `edif_superf`, `edif_fecha`, `final_global`.

El CSV de ejemplo contiene **solo valores inventados para probar el software**. No debe emplearse como resultados del TFM.

## Cómo se calcula el ranking experimental

1. Para cada variable se calcula su puesto percentil relativo dentro de los datos válidos (0 a 100). Los empates reciben el mismo valor. Si todos tienen el mismo valor, reciben 50 (no discriminan). Los registros faltantes no se imputan.
2. EPNR mayor implica puntaje relativo mayor; emisiones CEE mayores también. Para el indicador social, menor renta media territorial implica mayor puntaje (este supuesto político/normativo tiene que justificarse y discutirse).
3. **Escenario 1:** `EPNR` (100%). **Escenario 2:** energía (60%) + emisiones CEE (40%). **Escenario 3:** energía (50%) + emisiones CEE (30%) + entorno social (20%); en la interfaz se ajustan estos pesos, que suman 100%.
4. Falta cualquiera de las variables con peso positivo → resultado para esa fila es `NA`, no cero. Se asigna puesto de mayor puntaje a menor puntaje.

**Limitación:** el percentil relativo puede variar al filtrar municipios y cambiar la muestra; una validación formal deberá contrastar estabilidad, cambios de orden y representatividad.

## Fuentes y trazabilidad

- Registro de Certificados de Eficiencia Energética de Edificios, **Comunidad de Madrid**: https://datos.comunidad.madrid/dataset/registro_certificados_eficiencia_energetica
- Diccionario oficial de columnas, recurso CEEE 2026: https://datos.comunidad.madrid/dataset/registro_certificados_eficiencia_energetica/resource/4e42b49c-bb6b-485a-a7b7-8f760f356855
- **CRREM Assessment Guide** (mayo de 2026, guía oficial): https://crrem.org/wp-content/uploads/crrem-library/assessment-guide-v1.03.pdf

No se ha descargado ni analizado aún la base CEEE completa. Para una prueba con datos reales será necesario comprobar las unidades, los valores ausentes, la consistencia de tipos y los identificadores. Los CSV del registro de Madrid contienen **direcciones**: tratar con cuidado los datos potencialmente identificables y verificar licencias/usos permitidos antes de publicar extractos.

## Evolución propuesta (pendiente de investigación)

1. Auditar una muestra real plurifamiliar del CEEE con reglas de inclusión documentadas.
2. Conciliar edificios / viviendas / varias referencias / certificados sucesivos y comprobar el enlace con Catastro.
3. Incorporar renta por sección censal mediante geometría oficial y año correspondiente.
4. Diseñar y contrastar un indicador climático más pertinente; evaluar si se dispone de energía **final operativa** suficiente para un módulo CRREM aparte.
5. Comparar rankings contra un criterio externo y hacer análisis de sensibilidad.
6. Registrar cualquier uso de IA y validar su aportación concreta; el motor actual es **multicriterio transparente, no aprendizaje automático**.

## Pruebas automáticas

```sh
python -m pip install pytest
python -m pytest -q
```

## Registro de IA / autoría

- 19/10/2026 — ChatGPT (OpenAI, GPT-6): diseño y primera implementación de código Python, interfaz Streamlit, reglas de calidad, ejemplo sintético y documentación. Todo debe revisarse, probarse y comprenderse por el autor. La herramienta no ha generado resultados empíricos de edificios.
