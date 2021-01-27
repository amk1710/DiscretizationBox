import geopandas
from geopandas import GeoDataFrame
from shapely.geometry import Polygon
import numpy as np

#maybe to-do: support 8-neighborhood instead of only 4-neighborhood. Should be pretty easy to do
def rectangle_discretization(gdf : GeoDataFrame, nx : int, ny : int, *, neighborhood = '8'):
    '''
        Construct a square discretized gdf from the original region. The final discretization is intended to be a grid of nx per ny rectangles.
        Also construct neighbors data for each rectangle.

        Please be aware that each cell in the returned GeoDataFrame is not necessarily a rectangle: edge regions or 'islands' will fit to their original formats. 
        A data structural consequence of this is that the shapes forming the regions are not all Polygons; they may be Multi-polygons, or Points / Multipoint depending on the original topology

        Arguments:
            gdf : GeoDataFrame - the GeoDataFrame describing the original study region
            nx, ny  - define how many subdivision to use on the discretization, on the x and y axis respectively
        Keyword only arguments:
            neighborhood : ('8', '4') - Defines the type of neighborhood to be added to the returned gdf. 
                '8' uses 8-neighborhood in squares(ie. 4 full edge neighbors + 4 diagonal neighbords), while '4' uses only the full edge neighbors
        
    '''
    if nx <= 0 or ny <= 0:
        raise ValueError("nx and ny must be strictly positive")
    minx, miny, maxx, maxy = gdf.geometry.total_bounds

    deltay = (maxy - miny) / ny
    deltax = (maxx - minx) / nx

    #construct 'squares' GeoDataFrame. Lots of rectangles covering the entire study region
    squares = []
    indices = []
    neighbors = []
    valid_index = lambda ix, iy : True if ix >= 0 and iy >= 0 and ix < nx and iy < ny else False
    index = lambda ix, iy : iy * ny + ix if valid_index(ix, iy) else None

    for iy in range(ny):
        for ix in range(nx):
            cx, cy = minx + ix * deltax, miny + iy * deltay
            pol = Polygon([(cx, cy), (cx + deltax, cy), (cx + deltax, cy + deltay), (cx, cy + deltay)])
            squares.append(pol)
            indices.append(index(ix, iy))
            if neighborhood == '4':
                my_neighbors = [index(ix + 1, iy), index(ix - 1, iy), index(ix, iy + 1), index(ix, iy - 1)]
            elif neighborhood == '8':
                my_neighbors = [index(ix + 1, iy), index(ix - 1, iy), index(ix, iy + 1), index(ix, iy - 1),
                                index(ix + 1, iy + 1), index(ix + 1, iy - 1), index(ix - 1, iy + 1), index(ix - 1, iy - 1)]
            else:
                raise ValueError("Invalid neighborhood type " + neighborhood)
            my_neighbors = [n for n in my_neighbors if n is not None]
            neighbors.append(my_neighbors)

    squares = geopandas.GeoSeries(squares)
    squares_gdf = geopandas.GeoDataFrame({'geometry' : squares, 'myindex' : indices, 'neighbors' : neighbors}, crs = "EPSG:4326")

    #calculate the intersection between this squares gdf and the original region
    res_intersection = geopandas.overlay(squares_gdf, gdf, how='intersection')
    res_intersection.set_crs("EPSG:4326")

    #when calculating the intersection, some rectangles may have been dropped entirely
    #thus, we need to adjust the 'neighbor' column to correctly reflect the new indices
    #that's why we keep a auxiliary 'myindex' column. We just need to adjust 'myindex' to actual indexes
    new_neighbors = []
    for i, row in res_intersection.iterrows():
        new_list = [res_intersection.index[res_intersection['myindex'] == n] for n in row['neighbors']]
        new_list = [item for sublist in new_list for item in sublist] #flatten lists
        new_neighbors.append(new_list)
    res_intersection['neighbors'] = new_neighbors


    return res_intersection.drop(['myindex'], axis = 1)


