import os
import pandas as pd
import geopandas as gpd

#  definição de paths
DATA_PATH = r'C:\Users\Elogroup\GiovanniAmorim\Personal\ProjetoAmbulancias\dados'

ENTR_DATA_PATH = os.path.join(DATA_PATH,'1_entrada')
RAW_FOLDER_PATH = os.path.join(ENTR_DATA_PATH,'regressores','populacao','raw')

# leitura do dado de populacao por bairros
population_df = pd.read_excel(os.path.join(RAW_FOLDER_PATH,'2974.xls'),index_col=0)

# formatar o dado
pop_rows = []
for ind,row in population_df.iterrows():
    
    if not (ind in ['Homens','Mulheres']):
        bairro = ind
    
    r = [bairro,ind]
    for col in population_df.columns:
        r.append(row[col])
    
    pop_rows.append(r)

population_df2 = pd.DataFrame(pop_rows,columns=['bairro','sexo']+[str(c) for c in population_df.columns])
population_df2.drop(population_df2[population_df2['bairro']==population_df2['sexo']].index,inplace=True)

# calcular grupos etários
population_df2['populacao_infantil'] = (
    population_df2['<1']+
    population_df2['1']+
    population_df2['2']+
    population_df2['3']+
    population_df2['4']+
    population_df2['5 a 9']+
    population_df2['10 a 14']+
    population_df2['15']
)

population_df2['populacao_jovem_adulta'] = (
    population_df2['16 a 17']+
    population_df2['18 a 19']+
    population_df2['20 a 24']+
    population_df2['25 a 29']
)

population_df2['populacao_adulta'] = (
    population_df2['30 a 34']+
    population_df2['35 a 39']+
    population_df2['40 a 44']+
    population_df2['45 a 49']+
    population_df2['50 a 54']+
    population_df2['55 a 59']
)

population_df2['populacao_idosa'] = (
    population_df2['60 a 64']+
    population_df2['65 a 69']+
    population_df2['70 a 74']+
    population_df2['75 a 79']+
    population_df2['>=80']
)

population_df2 = population_df2[['bairro','sexo','populacao_infantil','populacao_jovem_adulta','populacao_adulta','populacao_idosa']].groupby('bairro').sum().reset_index()

# leitura dos dados geográficos dos bairros
bairros_df = gpd.read_file(os.path.join(RAW_FOLDER_PATH,'bairros_rj'))
bairros_df = bairros_df.set_crs(epsg=29183)
bairros_df = bairros_df.to_crs(epsg=4326)

population_rows = []
for ind,row in population_df2.iterrows():
    bairro = row['bairro']
    geom = bairros_df[[n in row['bairro'] for n in bairros_df['NOME'].values]]
    
    if len(geom) > 0:
        geom = geom['geometry'].values[0]
    else:
        geom = None
    
    population_rows.append([geom]+list(row.values))

population_df = gpd.GeoDataFrame(population_rows,columns=['geometry']+list(population_df2.columns))
population_df = population_df.set_crs('EPSG:4326')
population_df.drop('bairro',axis=1,inplace=True)

population_df.to_file(os.path.join(ENTR_DATA_PATH,'regressores','populacao','populacao.shp'))