
from geopandas import GeoDataFrame, read_file

from .h3_utils import generate_H3_discretization
from .travel_times.graphhopper import distance_matrix_from_gdf
from .squares import rectangle_discretization

import numpy as np

'''
This file defines functions for ease of use, redirecting to the correct implementation in other files
'''

def generate_discretization(gdf, shape = 'hexagons', *, nx = 10, ny = 10, neighborhood_type = '8', h3_discretization_level = 6, export_friendly = False) -> GeoDataFrame:
    '''
    Generate an enriched, discretized GeoDataFrame from the original geodataframe. The GeoDataFrame returned should work seamlessly with
        other functions provided within this module.

    Arguments:
        gdf : (string, GeoDataFrame) - a path to a GeoDataFrame or a GeoDataFrame object
        shape : ('rectangles', 'hexagons', 'none', False) - the shape in which the space should be discretized. If 'none' or False, no discretization is done
    Keyword only arguments:
        nx, ny : (int) - if using 'rectangles', define how many subdivision to use on the discretization, on the x and y axis respectively
        neighborhood : ('8', '4') - if using 'rectangles', defines the type of neighborhood to be added to the returned gdf. See squares.py for further details
        h3_discretization_level : (int)- if using 'hexagons', this sets the resolution level passed to the H3 library. A bigger number means smaller hexagons. Valid range [0,15]
        export_friendly : (bool) - if True, the returned geodataframe is transformed to contain only columns that can be easily exported
    Returns:
        (GeoDataFrame)  - a discretized geodataframe with columns filled as expected by the other functions in this package
    
    '''
    if(isinstance(gdf, str)):
        gdf = geopandas.read_file(gdf).reset_index()
        gdf = gdf.to_crs(epsg=4326) #convert coordinate system to lat long
    elif (isinstance(gdf, GeoDataFrame)):
        #for now, we're converting everything to lat long. This may not be strictly necessary but made thing easier for now
        gdf = gdf.to_crs(epsg=4326) #convert coordinate system to lat long
    else:
        raise TypeError

    discretized_gdf = None
    if(shape == 'hexagons'):
        discretized_gdf = generate_H3_discretization(gdf, h3_discretization_level)
    elif(shape == 'rectangles'):
        discretized_gdf = rectangle_discretization(gdf, nx, ny, neighborhood=neighborhood_type)
    elif shape == 'none' or shape == False:
        discretized_gdf = gdf
        #fill neighbors column using the geometry itself:
        #be aware, tho: this process is not 100% fail-proof, and is prone to numerical errors!
        #calculate neighbors:
        neighborss = []
        for i, row in discretized_gdf.iterrows():
            # get indices of 'touching' geometries
            #print(numpy.flatnonzero(res_intersection[res_intersection.geometry.touches(poly.geometry)]).tolist())
            neighbors = [i for i in gdf.index[gdf.geometry.touches(row.geometry)]]

            # remove own index of the row itself from the list
            neighbors = [ index for index in neighbors if i != index ]

            # add names of neighbors as NEIGHBORS value
            neighborss.append(neighbors)
        discretized_gdf['neighbors'] = neighborss

    #fills center_lat and center_lon
    centers = [shape.centroid for shape in discretized_gdf.geometry]
    discretized_gdf['center_lat'] = [p.y for p in centers]
    discretized_gdf['center_lon'] = [p.x for p in centers]

    if not 'area' in discretized_gdf:
        #fills area
        area = [shape.area for shape in discretized_gdf.geometry]
        discretized_gdf['area'] = area
  
    
    discretized_gdf = reindex(discretized_gdf)

    if export_friendly:
        discretized_gdf = to_export_friendly(discretized_gdf)
    
    return discretized_gdf

def save_gdf(gdf : GeoDataFrame, path, driver = 'ESRI Shapefile'):
    '''
        Saves the familiar gdf to path, using driver. For supported drivers, see geopandas / fiona documentation
    '''
    return to_export_friendly(gdf).to_file(path, driver = driver)

def load_gdf(path, driver = None) -> GeoDataFrame:
    '''
        Loads and returns a familiar gdf. If no driver is specified, geopandas tries to use the correct one automatically
    '''
    if driver == None:
        return reindex(from_export_friendly(read_file(path).reset_index()))
    else:
        return reindex(from_export_friendly(read_file(path, driver = driver).reset_index()))



def to_export_friendly(gdf : GeoDataFrame) -> GeoDataFrame:
    '''
        Takes the familiar format for gdf and transforms it into an io friendly format
    '''

    #transform list into string separated by -
    copy_gdf = gdf.copy()
    temp_neighbors = ['-'.join(map(str, lista)) for lista in copy_gdf['neighbors']]
    copy_gdf['neighbors'] = temp_neighbors

    return copy_gdf


def from_export_friendly(gdf : GeoDataFrame) -> GeoDataFrame:
    '''
        Detransforms the transformation done by to_export_friendly
    '''

    temp_neighbors = [list(map(int, mystring.split('-'))) for mystring in gdf['neighbors']]
    gdf['neighbors'] = temp_neighbors
    return gdf

def reindex(gdf : GeoDataFrame) -> GeoDataFrame:
    #set desired order of columns
    col = ['geometry', 'area', 'center_lat', 'center_lon', 'neighbors']
    col = col + [c for c in gdf.columns if c not in col] # but don't drop any
    re_gdf = gdf.reindex(columns=col)
    return re_gdf
