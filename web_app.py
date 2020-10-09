# x-api-key=6a25ea34-e812-4344-aba1-0d1d4bce5198
import requests
from geopandas import GeoSeries
from shapely.geometry import Polygon
import os
import rasterio
from rasterio.mask import mask
import plotly.graph_objects as go
from codetiming import Timer
building_address = "Schoenmarkt 35 Antwerpen 2000"  # deafult = kbc Boerentoren


@Timer(name="decorator")
def get_address(nb='35', street='Schoenmarkt', city='Antwerpen', pc='2000'):
    ''' default builging = kbc tower antwerpen (Boerentoren)
            adress = Schoenmarkt 35, 2000 Antwerpen
            Ask the user to enter an address '''
    # *****_____ enable the following 5 lines to enable the address request from the user _____*****
    # nb = str(input("Please Enter house number:"))
    # street = str(input("Please Enter street:"))
    # city = str(input("Please Enter city:"))
    # pc = str(input("Please Enter postcode:"))
    # building_address = f'{street} {nb} {city} {pc}'
    # Check user adddress match using api
    req = requests.get(
        f"https://api.basisregisters.dev-vlaanderen.be/v1/adresmatch?gemeentenaam={city}&straatnaam={street}&huisnummer={nb}&postcode={pc}").json()
    # Retrieve objectID for users address
    objectId = req["adresMatches"][0]["adresseerbareObjecten"][0]["objectId"]
    # Get building geometry
    req = requests.get(
        f"https://api.basisregisters.dev-vlaanderen.be/v1/gebouweenheden/{objectId}").json()
    objectId = req["gebouw"]["objectId"]
    req = requests.get(
        f"https://api.basisregisters.dev-vlaanderen.be/v1/gebouwen/{objectId}").json()
    # Get building polygon coordinates
    global polygon
    polygon = [req["geometriePolygoon"]["polygon"]]
    t = []  # Convert polygon to more useful geopanda series
    for i in polygon[0]['coordinates'][0]:
        t.append(tuple(i))  # Get coordinates
    # Convert coordinates to Polygon format
    global house_polygon
    house_polygon = Polygon(t)
    global gpd_df
    gpd_df = GeoSeries([house_polygon])  # Save Polygon in geopanda series
    global house_area  # Get area of building
    house_area = gpd_df.area  # Area of the building


get_address()


@Timer(name="decorator")
def fast_overlap():
    path = os.path.abspath('./tiffs')
    filelist = []  # Get file list
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".tif"):
                filelist.append(file)
    global dsmfile
    global dtmfile
    for f in filelist:
        filepath = os.path.join(path, f)
        with rasterio.open(filepath) as src:  # src is raster, polygon is user address
            if rasterio.coords.disjoint_bounds(src.bounds, house_polygon.bounds) == False:
                if "DSM" in src.name:
                    dsmfile = src.name
                elif "DTM" in src.name:
                    dtmfile = src.name


fast_overlap()


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


calculate_dem()  # 3 -
fig = go.Figure(data=[go.Surface(z=dem)])  # Plot xyz of building
fig.update_layout(title=str(building_address), autosize=False,
                  width=700, height=700,
                  margin=dict(l=65, r=50, b=65, t=50))
fig.show()
print('The building height is:', round(dem.max(), 1), 'meters')
print('The building floor area is:', round(int(house_area), 1), 'sq meters')
