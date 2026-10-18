import io
import pandas as pd
from motor import cargar_archivo, normalizar, calidad, calcular_escenarios, porcentaje_relativo


def test_csv_espanol_y_alias():
    blob = 'edif_muni;norenov_global;norenov_co2global;edif_superf\nMadrid;123,5;22,2;100,0\n'.encode('utf-8')
    d, aliases = normalizar(cargar_archivo('archivo.csv', blob))
    assert d.loc[0, 'epnren'] == 123.5
    assert d.loc[0, 'emisiones'] == 22.2
    assert aliases['epnren'] == 'norenov_global'


def test_no_imputa_faltantes():
    df = pd.DataFrame({'norenov_global':['100','200'], 'norenov_co2global':['20',''], 'renta_media_seccion_eur_persona':['10000','12000']})
    n,_ = normalizar(df)
    v = calcular_escenarios(calidad(n))
    assert pd.isna(v.loc[1,'escenario_3_con_contexto_social'])
    assert pd.notna(v.loc[1,'escenario_1_energia'])


def test_score_sentido_y_empates():
    s = pd.Series([100,200,300])
    p=porcentaje_relativo(s)
    assert p.tolist() == [0,50,100]
    assert porcentaje_relativo(pd.Series([2,2,2])).tolist() == [50,50,50]


def test_alerta_duplicados():
    n,_=normalizar(pd.DataFrame({'edif_refcat':['123','123'], 'norenov_global':[20,40]}))
    assert calidad(n)['alerta_refcat_repetida'].tolist()==[True,True]


def test_componente_con_peso_cero_no_exige_dato():
    df = pd.DataFrame({'norenov_global':['100','200'], 'norenov_co2global':['20','30']})
    n,_ = normalizar(df)
    v = calcular_escenarios(calidad(n), pesos=(0.5,0.5,0.0))
    assert v['escenario_3_con_contexto_social'].notna().all()


def test_sin_datos_climaticos_solo_energia():
    df = pd.DataFrame({'norenov_global':['100','200']})
    n,_ = normalizar(df)
    v = calcular_escenarios(calidad(n), pesos=(1.0,0.0,0.0))
    assert v['escenario_3_con_contexto_social'].notna().all()
