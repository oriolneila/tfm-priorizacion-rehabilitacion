"""Arranque público del análisis arquitectónico, 15/11/2026. Datos aislados por sesión."""
from pathlib import Path
import hashlib
import runpy
import sys
import tempfile
from zipfile import ZipFile
import streamlit as st


@st.cache_resource
def fuente_estable():
    archive=Path(__file__).with_name('version_analisis_2026_11_15.zip')
    if hashlib.sha256(archive.read_bytes()).hexdigest() != '18a47cc0c684645eb117b1c49fd230d475e9ddb0f0013837046569254bbf031d':
        raise ValueError('El paquete de la aplicación no coincide con su huella publicada.')
    target=Path(tempfile.mkdtemp(prefix='tfm_analisis_2026_11_15_'))
    with ZipFile(archive) as z:
        for name in z.namelist():
            path=(target/name).resolve()
            if not path.is_relative_to(target.resolve()):raise ValueError('Ruta de archivo no válida')
        z.extractall(target)
    source=target/'Herramienta_TFM'
    substitutions={
        'Guardado en este equipo. Se recupera al volver a abrir la herramienta.':'Guardado durante esta sesión. Descarga tus resultados antes de salir.',
        'Archivo activo guardado en este equipo:':'Archivo activo en esta sesión:',
        'Importa tu archivo CSV o ZIP. Se conserva una copia local para continuar al volver a abrir la herramienta.':'Importa tu CSV o ZIP. En esta publicación, los archivos y las revisiones se conservan durante la sesión.',
    }
    for filename in ('datos_ui.py','portada.py'):
        path=source/filename;content=path.read_text(encoding='utf8')
        for old,new in substitutions.items():content=content.replace(old,new)
        path.write_text(content,encoding='utf8')
    return source


root=fuente_estable()
if str(root) not in sys.path:sys.path.insert(0,str(root))
for path in root.glob('*.py'):
    old=sys.modules.get(path.stem)
    if old and Path(getattr(old,'__file__','')).parent!=root:sys.modules.pop(path.stem,None)

# El programa original conserva su persistencia local. En la publicación, cada
# visitante utiliza su sesión y un historial temporal propio, sin compartir CSV.
import conjunto_guardado
def guardar(nombre,contenido):
    if Path(nombre).suffix.lower() not in ('.csv','.zip') or not contenido:raise ValueError('Importa un CSV o ZIP con contenido.')
    st.session_state['_archivo_nube']=(nombre,contenido)
def recuperar():return st.session_state.get('_archivo_nube')
def retirar():st.session_state.pop('_archivo_nube',None)
conjunto_guardado.guardar=guardar
conjunto_guardado.recuperar=recuperar
conjunto_guardado.retirar=retirar

import incidencias
if not hasattr(incidencias,'_historial_local'):
    incidencias._historial_local=incidencias.historial
    incidencias._guardar_local=incidencias.guardar_revision
def ruta_revision():
    if '_directorio_revision_nube' not in st.session_state:
        st.session_state['_directorio_revision_nube']=tempfile.TemporaryDirectory(prefix='tfm_sesion_')
    return Path(st.session_state['_directorio_revision_nube'].name)/'revisiones.sqlite3'
def historial(cohort,path=None):return incidencias._historial_local(cohort,path=path or ruta_revision())
def guardar_revision(*args,**kwargs):
    kwargs.setdefault('path',ruta_revision())
    return incidencias._guardar_local(*args,**kwargs)
incidencias.historial=historial
incidencias.guardar_revision=guardar_revision
runpy.run_path(str(root/'app.py'),run_name='__main__')
if st.session_state.get('acceso_abierto'):
    st.sidebar.caption('Versión ampliada · 15/11/2026 · Análisis arquitectónico · Los archivos y las revisiones de esta publicación se conservan durante la sesión. Descarga tus resultados antes de salir.')
