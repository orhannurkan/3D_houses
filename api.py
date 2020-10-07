# https://loc.geopunt.be for API info
import requests
import json
from shapely.geometry import box

address = 'Maaltekouter 2, 9051 Gent'  # IKEA

response = requests.get(
    "http://loc.geopunt.be/geolocation/location?q={}&c=1".format(address))
bounding_box = response.json()["LocationResult"][0]['BoundingBox']
print(bounding_box)

llx = bounding_box['LowerLeft']['X_Lambert72']
lly = bounding_box['LowerLeft']['Y_Lambert72']
urx = bounding_box['UpperRight']['X_Lambert72']
ury = bounding_box['UpperRight']['Y_Lambert72']
bbox = box(llx, lly, urx, ury)
print(bbox)
print()
print()
