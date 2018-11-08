# Data Format Control dictionary
# this is mainly used for holding the confidence values and such used in the
# land cover layers.
# lc -> Land Cover layers
# lcc -> Land Cover Confidence value
dfc = {'lc_inbtw': 9,   # default value for between models
       'lc_insuff': 10,  # insufficient data, such as at the end of a time series
       'lcc_growth': 151,
       'lcc_decline': 152,
       'lcc_nomodel': 201,
       'lcc_forwards': 202,
       'lcc_samelc': 211,
       'lcc_difflc': 212,
       'lcc_back': 213,
       'lcc_afterbr': 214,
       }

lc_map = {'develop': 1,
          'ag': 2,
          'grass': 3,
          'tree': 4,
          'water': 5,
          'wetland': 6,
          'snow': 7,
          'barren': 8}

nlcdxwalk = {11: 5,
             12: 7,
             21: 1,
             22: 1,
             23: 1,
             24: 1,
             31: 8,
             41: 4,
             42: 4,
             43: 4,
             51: 0,
             52: 3,
             71: 3,
             72: 3,
             73: 0,
             74: 0,
             81: 2,
             82: 2,
             90: 6,
             95: 6}

band_names = ('blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'thermal')

chg_magbands = band_names[1:-1]
chg_begining = '1982-01-01'

cu_tileaff = (-2565585, 150000, 0, 3314805, 0, -150000)
cu_chipaff = (-2565585, 3000, 0, 3314805, 0, -3000)
#
# conus-extent:
#   xmin: -2565585
#   ymax: 3314805
#   xmax: 2384415
#   ymin: 14805
# alaska-extent:
#   xmin: -851715
#   ymax: 2474325
#   xmax: 1698285
#   ymin: 374325
# hawaii-extent:
#   xmin: -444345
#   ymax: 2168895
#   xmax: 305655
#   ymin: 1718895
#
conuswkt = 'PROJCS["Albers",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378140,298.2569999999957,AUTHORITY[' \
           '"EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],' \
           'AUTHORITY["EPSG","4326"]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["standard_parallel_1",29.5],' \
           'PARAMETER["standard_parallel_2",45.5],PARAMETER["latitude_of_center",23],PARAMETER["longitude_of_center",' \
           '-96],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]]] '
