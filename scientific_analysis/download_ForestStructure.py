import yaml

import pandas as pd
import utm
import pyproj
import matplotlib.pyplot as plt
from xcube_multistore import MultiSourceDataStore

def get_download():
    msds = MultiSourceDataStore("config_ForestStructure.yml")
    return msds



# import pyproj
# from xcube_multistore.utils import get_utm_zone

# def get_bbox(lat, lon):
#     # lat, lon = 51.07916667, 10.453
#     cube_width = 4000
    
#     crs_utm = get_utm_zone(lat, lon)
#     transformer = pyproj.Transformer.from_crs("EPSG:4326", crs_utm, always_xy=True)
#     x, y = transformer.transform(lon, lat)
    
#     # create bbox in meter
#     half_size = cube_width / 2
    
#     bbox_utm = [x - half_size, y - half_size, x + half_size, y + half_size]
    
#     bbox_utm
    
#     # reproject bbox
#     t = pyproj.Transformer.from_crs(crs_utm, "EPSG:4326", always_xy=True)
#     target_bbox = t.transform_bounds(*bbox_utm, densify_pts=21)
#     # print(target_bbox)
#     return target_bbox

# sites = pd.read_csv("../data_extraction/sites.csv")

# foresteo_data_ids = [
#     ('biomass-carbon/CCI_BIOMASS/CCI_BIOMASS_v6.0/CCI_BIOMASS_v6.0.json', "modify_cci_biomass"),
#     ('biomass-carbon/SAATCHI_BIOMASS/SAATCHI_BIOMASS_v2.0/SAATCHI_BIOMASS_v2.0.json', None),
#     ('biomass-carbon/ROBINSON_CR/ROBINSON_CR_v1.0/ROBINSON_CR_v1.0.json', None),
#     ('disturbance-change/HANSEN_GFC/HANSEN_GFC_v1.12/HANSEN_GFC_v1.12.json', None),
#     ('structure-demography/GAMI/GAMI_v3.1/GAMI_v3.1.json', "modify_gami"),
#     ('structure-demography/POTAPOV_HEIGHT/POTAPOV_HEIGHT_v1.0/POTAPOV_HEIGHT_v1.0.json', None),
# ]

# time_range = ["2020-04-15", "2020-04-30"]



# config = dict(datasets=[])
# for index, site in sites.iterrows():
#     # append config for Sentinel-2
#     config_ds = dict(
#         identifier=f"{site['Site ID']}/sen2",
#         store="stac-pc",
#         data_id="sentinel-2-l2a",
#         open_params=dict(
#             time_range=time_range,
#             point=[site["longitude"], site["latitude"]],
#             bbox_width=4000,
#             spatial_res=10,
#             asset_names=[
#                 "SCL",
#             ],
#         ),
#     )
#     config["datasets"].append(config_ds)


#     # append config for forestEO products
#     for (data_id, func_name) in foresteo_data_ids:
#         config_ds = dict(
#             identifier=f"{site['Site ID']}/{data_id.split('/')[1]}",
#             store="store_foresteo",
#             data_id=data_id,
#             grid_mapping=f"{site['Site ID']}/sen2",
#         )
    
#         if func_name is not None:
#             config_ds["custom_processing"] = {
#                 "module_path": "utils",
#                 "function_name": func_name,
#             }
    
#         config["datasets"].append(config_ds)
    
#     # append config for GEDI
#     config_ds = dict(
#         identifier=f"{site['Site ID']}/gedi",
#         store="store_gedi",
#         data_id="all",
#         open_params=dict(
#             bbox=list(get_bbox(site["latitude"], site["longitude"])),
#             time_range=["2019-04-01", "2025-12-31"],
#             variables= [
#                 'agbd',
#                 'agbd_pi_lower',
#                 'agbd_pi_upper',
#                 'agbd_se',
#                 'agbd_t',
#                 'agbd_t_se',
#                 'algorithmrun_flag',
#                 'beam_type',
#                 'degrade_flag',
#                 'fhd_normal',
#                 'l2a_quality_flag',
#                 'l2b_quality_flag',
#                 'landsat_treecover',
#                 'leaf_off_flag',
#                 'num_detectedmodes',
#                 'omega',
#                 'quality_flag',
#                 'rh',
#                 'sensitivity',
#                 'solar_elevation',
#                 'surface_flag',
#                 'wsci',
#                 'wsci_pi_lower',
#                 'wsci_pi_upper',
#                 'wsci_quality_flag',
#                 'wsci_xy',
#                 'wsci_xy_pi_lower',
#                 'wsci_xy_pi_upper',
#                 'wsci_z',
#                 'wsci_z_pi_lower',
#                 'wsci_z_pi_upper' 
#             ]
#         ),
#     )
#     config["datasets"].append(config_ds)

# # define stores
# config["data_stores"] = []
# # add storage data store
# config_store = dict(
#     identifier="storage",
#     store_id="file",
#     store_params=dict(root="../data"),
# )
# config["data_stores"].append(config_store)
# # add ESA CCI data store
# config_store = dict(
#     identifier="esa_cci",
#     store_id="cciodp",
# )
# config["data_stores"].append(config_store)
# # add STAC data store
# config_store = dict(
#     identifier="stac-pc",
#     store_id="stac-pc-ardc",
# )
# config["data_stores"].append(config_store)
# # add ForestEO STAC data store
# config_store = dict(
#     identifier="store_foresteo",
#     store_id="stac",
#     store_params={
#       "url": "https://s3.gfz-potsdam.de/dog.atlaseo-glm.eo-gridded-data/collections/public/catalog.json",
#     }
# )
# config["data_stores"].append(config_store)
# # add GEDI data store
# config_store = dict(
#     identifier="store_gedi",
#     store_id="gedidb",
# )
# config["data_stores"].append(config_store)

# with open("config_ForestStructure.yml", "w") as file:
#     yaml.dump(config, file, sort_keys=False)

