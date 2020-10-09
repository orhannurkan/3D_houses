# x-api-key=6a25ea34-e812-4344-aba1-0d1d4bce5198
import os
import rasterio
from rasterio.windows import Window
from rasterio.mask import mask
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import requests
from geopandas import GeoSeries
from shapely.geometry import Polygon
import pandas as pd
import geopandas as gpd
from codetiming import Timer
# default address = "Schoenmarkt 35 Antwerpen 2000"  # kbc Boerentoren


@Timer(name="decorator")
def get_address(nb='35', street='Schoenmarkt', city='Antwerpen', pc='2000'):
    ''' default builging = kbc tower antwerpen (Boerentoren)
            adress = Schoenmarkt 35, 2000 Antwerpen
            Ask the user to enter an address '''
    # Check adddress
    req = requests.get(
        f"https://api.basisregisters.dev-vlaanderen.be/v1/adresmatch?gemeentenaam={city}&straatnaam={street}&huisnummer={nb}&postcode={pc}").json()
    # objectID
    objectId = req["adresMatches"][0]["adresseerbareObjecten"][0]["objectId"]
    # building geometry
    req = requests.get(
        f"https://api.basisregisters.dev-vlaanderen.be/v1/gebouweenheden/{objectId}").json()
    objectId = req["gebouw"]["objectId"]
    req = requests.get(
        f"https://api.basisregisters.dev-vlaanderen.be/v1/gebouwen/{objectId}").json()
    # build polygon coordinates
    global polygon
    polygon = [req["geometriePolygoon"]["polygon"]]
    t = []
    for i in polygon[0]['coordinates'][0]:
        t.append(tuple(i))  # Put coordinates
    global house_polygon  # coordinates to Polygon
    house_polygon = Polygon(t)
    global gpd_df  # Polygon to geopanda
    gpd_df = GeoSeries([house_polygon])
    global house_area
    # Area
    house_area = gpd_df.area


get_address()  # 1 - Step


@Timer(name="decorator")
def fast_overlap():
    # Set path to folder with rasters
    path = os.path.abspath('./tiffs')
    # Get file list
    filelist = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".tif"):
                filelist.append(file)
    global dsmfile
    global dtmfile
    for f in filelist:
        filepath = os.path.join(path, f)
        # Open raster and check overlap
        with rasterio.open(filepath) as src:
            # src is raster, polygon is user address
            if rasterio.coords.disjoint_bounds(src.bounds, house_polygon.bounds) == False:
                if "DSM" in src.name:
                    dsmfile = src.name
                elif "DTM" in src.name:
                    dtmfile = src.name


fast_overlap()  # 2 - Step


@Timer(name="decorator")
def calculate_dem():
    path = os.path.abspath('./tiffs')
    dsmpath = os.path.join(path, str(dsmfile))
    dtmpath = os.path.join(path, str(dtmfile))
    with rasterio.open(dsmpath) as src:  # Open DSM raster with mask of building shape
        mask, out_transform, win = rasterio.mask.raster_geometry_mask(
            dataset=src, shapes=gpd_df, invert=False, crop=True, pad=False)
        # Read only pixels within the window/bounds of the building shape
        dsm = src.read(1, window=win)
    with rasterio.open(dtmpath) as src:  # Open DTM raster with mask of building shape
        mask, out_transform, win = rasterio.mask.raster_geometry_mask(
            dataset=src, shapes=gpd_df, invert=False, crop=True, pad=False)
        # Read only pixels within the window/bounds of the building shape
        dtm = src.read(1, window=win)
    global dem  # Calculates raw digital elevation model (no resampling)
    dem = dsm - dtm


calculate_dem()  # 3 - Step


@Timer(name="decorator")
def basic_3Dplot(dem=dem):
    ny, nx = dem.shape
    x = np.linspace(0, 1, nx)
    y = np.linspace(0, 1, ny)
    xv, yv = np.meshgrid(x, y)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    dem3d = ax.plot_surface(xv, yv, dem, cmap='brg', linewidth=0, alpha=0.8)
    ax.set_title('3D house')
    ax.set_zlabel('Height (m)')
    plt.show()


basic_3Dplot(dem)  # 4 - show it in matplotlib
