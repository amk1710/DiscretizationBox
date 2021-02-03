import os
import geopandas as gpd

#  definição de paths
DATA_PATH = r'C:\Users\Elogroup\GiovanniAmorim\Personal\ProjetoAmbulancias\dados'

ENTR_DATA_PATH = os.path.join(DATA_PATH,'1_entrada')
RAW_FILE_PATH = os.path.join(ENTR_DATA_PATH,'regressores','uso de solo','raw','Uso_do_Solo_2018.shp',encoding='utf-8')

# leitura do dado de uso de solo
regr_df = gpd.read_file(RAW_FILE_PATH)

# agrupar classificações de uso
regr_df['TipoUso2'] = regr_df['UsoAgregad'].replace({
    'Cobertura arbórea e arbustiva': 'Áreas de mata',
    'Cobertura gramíneo lenhosa': 'Áreas de mata',
    'Afloramentos rochosos e depósitos sedimentares': 'Áreas rochosas',
    'Áreas de exploração mineral': 'Áreas rochosas',
})

regr_df = regr_df.dissolve(by='TipoUso2')[['geometry']].reset_index()
regr_df['area'] = regr_df['geometry'].area

# editar crs para unificar coordenadas
regr_df = regr_df.to_crs('EPSG:4326')

# criar novo dataframe
regr_rows = []
cols = regr_df['TipoUso2'].unique()
for ind, row in regr_df.iterrows():
    values = [row['geometry']]
    for c in cols:
        if row['TipoUso2'] == c:
            values.append(row['area'])
        else:
            values.append(0)
    regr_rows.append(values)

regr_df = gpd.GeoDataFrame(regr_rows,columns=['geometry']+list('UsoSolo - '+cols))
regr_df.to_file(os.path.join(ENTR_DATA_PATH,'regressores','uso de solo','uso do solo.shp'))
