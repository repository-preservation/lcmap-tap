"""Some well known text projection information"""

# <str> Well known text containing the Albers Equal Area WGS 84 projected coordinate system
#       This is the currently used projected coordinate system for collection 01 ARD
AEA_WKT = 'PROJCS["Albers",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378140,298.2569999999957,' \
          'AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",' \
          '0.0174532925199433],AUTHORITY["EPSG","4326"]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER[' \
          '"standard_parallel_1",29.5],PARAMETER["standard_parallel_2",45.5],PARAMETER["latitude_of_center",23],' \
          'PARAMETER["longitude_of_center",-96],PARAMETER["false_easting",0],PARAMETER["false_northing",0],' \
          'UNIT["metre",1,AUTHORITY["EPSG","9001"]]] '

# <str> Well known text containing WGS 84 geographic coordinate system
WGS_84_WKT = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],' \
             'AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSGS","8901"]],UNIT["degree",' \
             '0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]] '

