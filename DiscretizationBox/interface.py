
from geopandas import GeoDataFrame, read_file

from .h3_utils import generate_H3_discretization
from .travel_times.graphhopper import distance_matrix_from_gdf

'''
This file defines functions for ease of use, redirecting to the correct implementation in other files
'''

def generate_discretization(gdf, shape = 'hexagons', h3_discretization_level = 6, export_friendly = False):
    '''
    Generate an enriched, discretized GeoDataFrame from the original geodataframe. The GeoDataFrame returned should work seamlessly with
        other functions provided within this module.

    Params:
        gdf : (string, GeoDataFrame) - a path to a GeoDataFrame or a GeoDataFrame object
        shape : ('rectangles', 'hexagons', 'none', False) - the shape in which the space should be discretized. If 'none' or False, no discretization is done
        h3_discretization_level - if using 'hexagons', this sets the resolution level passed to the H3 library. A bigger number means smaller hexagons. Valid range [0,15]
        export_friendly : (bool) - if True, the returned geodataframe is transformed to contain only columns that can be easily exported
    '''
    if(isinstance(gdf, str)):
        gdf = geopandas.read_file(gdf).reset_index()
    elif (isinstance(gdf, GeoDataFrame)):
        pass
    else:
        raise TypeError

    discretized_gdf = None
    if(shape == 'hexagons'):
        discretized_gdf = generate_H3_discretization(gdf, h3_discretization_level)
    elif(shape == 'rectangles'):
        raise NotImplementedError
    elif shape == 'none' or shape == False:
        discretized_gdf = gdf
        raise NotImplementedError
        #fill missing columns: center_lon, center_lat, neighbors, area

    #fills center_lat and center_lon
    centers = [shape.centroid for shape in discretized_gdf.geometry]
    discretized_gdf['center_lat'] = [p.y for p in centers]
    discretized_gdf['center_lon'] = [p.x for p in centers]

    if not 'area' in discretized_gdf:
        #fills area
        area = [shape.area for shape in discretized_gdf.geometry]
        discretized_gdf['area'] = area
  
        
    if export_friendly:
        discretized_gdf = to_export_friendly(discretized_gdf)

    #set desired order of columns
    col = ['area', 'center_lat', 'center_lon', 'neighbors']
    col = col + [c for c in discretized_gdf.columns if c not in col] # but don't drop any
    col = col + ['geometry']
    discretized_gdf = discretized_gdf.reindex(columns=col)
    
    return discretized_gdf


def save_gdf(gdf : GeoDataFrame, path, driver = 'ESRI Shapefile'):
    '''
        Saves the familiar gdf to a file. Driver can be any driver supported by geopandas / fiona. 
    '''
    return to_export_friendly(gdf).to_file(path, driver = driver)

def load_gdf(path, driver = None):
    '''
        Loads the familiar gdf from file
    '''
    if driver == None:
        return from_export_friendly(geopandas.read_file(path).reset_index())
    else:
        return from_export_friendly(geopandas.read_file(path, driver = driver).reset_index())


def to_export_friendly(gdf : GeoDataFrame):
    '''
        Takes the familiar format for gdf and transforms it into an io friendly format
    '''

    #transform list into string separated by -
    temp_neighbors = ['-'.join(map(str, lista)) for lista in gdf['neighbors']]
    gdf['neighbors'] = temp_neighbors

    return gdf

    


def from_export_friendly(gdf : GeoDataFrame):
    '''
        Detransforms the transformation done by to_export_friendly
    '''

    temp_neighbors = [list(map(int, mystring.split('-'))) for mystring in gdf['neighbors']]
    gdf['neighbors'] = temp_neighbors
    return gdf

