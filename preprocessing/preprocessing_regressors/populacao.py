import os
import pandas as pd
import geopandas as gpd
import re
import string

#  definição de paths
DATA_PATH = 'C:/Users/andrekrauss/Documents/DadosProjetoAmbulancias/'

ENTR_DATA_PATH = os.path.join(DATA_PATH,'1_entrada')
RAW_FOLDER_PATH = os.path.join(ENTR_DATA_PATH,'regressores','populacao','raw')

def myreplace(s : str):
    s = s.replace("ç", "c")
    s = s.replace("á", "a")
    s = s.replace("à", "a")
    s = s.replace("ú", "u")
    s = s.replace("ù", "u")
    s = s.replace("ó", "o")
    s = s.replace("ò", "o")
    s = s.replace("ã", "a")
    s = s.replace("â", "a")
    return s

# leitura do dado de populacao por bairros
population_df = pd.read_excel(os.path.join(RAW_FOLDER_PATH,'2974.xls'))

roman_regex = '^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$' # regex for roman numerals

# formatar o dado
pop_rows = []
for ind,row in population_df.iterrows():
    ident = population_df.iloc[ind,0]
    
    if ident in ['Homens','Mulheres'] or re.search(roman_regex, ident.split(' ', 1)[0]):
        continue
    
    bairro = ident
    
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

population_df2.drop(labels = ['sexo', 'Bairro'], axis = 1, inplace = True)

#fix weird names
population_df2['bairro'] = pd.Series(myreplace(s.lower().strip()) for s in population_df2['bairro'])

# leitura dos dados geográficos dos bairros
bairros_df = gpd.read_file(os.path.join(RAW_FOLDER_PATH,'bairros_rj'))
#bairros_df = bairros_df[bairros_df.geometry.is_valid] #only keep valid geometries
bairros_df = bairros_df.set_crs(epsg=29183)
bairros_df = bairros_df.to_crs(epsg=4326)

#fix weird names
bairros_df['NOME'] = pd.Series(myreplace(s.lower().strip()) for s in bairros_df['NOME'])

#fix typo in data: w vs v in Oswaldo Cruz!
bairros_df.loc[bairros_df['NOME'] == 'osvaldo cruz', 'NOME'] = 'oswaldo cruz'

#merge two 'bairros' columns:
bairros_df = bairros_df.rename(columns={'NOME': 'bairro'})

merge_columns = 'bairro'
wanted_columns = ['populacao_infantil', 'populacao_jovem_adulta', 'populacao_adulta', 'populacao_idosa']

new_gdf = bairros_df.join(population_df2.set_index(merge_columns), on = merge_columns)
new_gdf.to_file(os.path.join(ENTR_DATA_PATH,'regressores','populacao','populacao.shp'))


'''
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

population_df.to_file(os.path.join(ENTR_DATA_PATH,'regressores','populacao','populacao.shp'))
'''