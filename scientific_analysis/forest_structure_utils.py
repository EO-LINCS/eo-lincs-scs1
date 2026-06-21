import pandas as pd
import xarray as xr
import numpy as np
import json
import matplotlib.pyplot as pl

from rasterio.warp import transform
from matplotlib.patches import Polygon

with open("ICOS_rio.json", "r") as f:
    polygons = json.load(f)

sites = pd.read_csv("../data_extraction/sites.csv").set_index("Site ID")


def get_tower_latlon(site):
    return sites.loc[site].latitude, sites.loc[site].longitude

def get_tower_sen2_xy(site):
    tower_lat, tower_lon = get_tower_latlon(site)
    
    tower_x, tower_y = transform({'init': 'EPSG:4326'},
                         xr.open_zarr(f"../data/{site}/sen2.zarr").spatial_ref.crs_wkt,
                         [tower_lon], [tower_lat])
    return tower_x, tower_y
    

def add_tower(ax, site, color):
    crs = xr.open_zarr(f"../data/{site}/sen2.zarr").spatial_ref.crs_wkt
    tower_roi = np.array(polygons[site][0]["geometry"]["coordinates"][0])
    
    x, y = transform({'init': 'EPSG:4326'},
                         crs,
                         tower_roi[:,0], tower_roi[:,1])
    
    tower_x, tower_y = get_tower_sen2_xy(site)
    
    ax.add_patch(Polygon(
        np.stack([x, y]).T,
        fill=True, facecolor=color, alpha=0.4, edgecolor=None
    ))
    ax.add_patch(Polygon(
        np.stack([x, y]).T,
        fill=False, edgecolor=color, linewidth=1.5
    ))
    
    ax.scatter(tower_x, tower_y, marker="o", s=10, color="w")
    ax.scatter(tower_x, tower_y, marker="*", s=8, color=color)

    onekmrad_bk = pl.Circle((tower_x[0], tower_y[0]), 1000, color='w', fill=False, lw=2)
    ax.add_patch(onekmrad_bk)
    onekmrad = pl.Circle((tower_x[0], tower_y[0]), 1000, color=color, fill=False, lw=1.5)
    ax.add_patch(onekmrad)


def s2_dist_from_tower_calc(site):

    """
    Calculate distance from tower for each pixel in the dataset.
    
    Args:
    ds (xr.Dataset): Input dataset.
    tower_lat (float): Latitude of the tower.
    tower_lon (float): Longitude of the tower.
    
    Returns:
    xr.Dataset: Dataset with an additional variable 'dist_from_tower'.
    """
    
    ds = xr.open_zarr(f"../data/{site}/sen2.zarr")
    x, y = np.meshgrid(ds['x'], ds['y'])
    
    tower_x, tower_y = get_tower_sen2_xy(site)
    
    distFromTower = np.sqrt((x - tower_x) ** 2 + (y - tower_y) ** 2)
    
    out = xr.DataArray(distFromTower.T,
        coords=ds[['x', 'y']].coords,
        dims=("y", "x"),
        name="dist_from_tower",
        attrs={'long_name': 'Distance from tower location', 'units': 'meters'}
    )
    return out


def gedi_dist_from_tower_calc(gedi, site):
    # gedi = xr.open_zarr(f"../data/{site}/gedi.zarr/")
    tower_lat, tower_lon = get_tower_latlon(site)
    tower_x, tower_y = transform({'init': 'EPSG:4326'},
                         "EPSG:6933",
                         [tower_lon], [tower_lat])
    x_shot, y_shot  =transform({'init': 'EPSG:4326'},
                         "EPSG:6933",
                         gedi.longitude.values, gedi.latitude.values)
    dist = np.sqrt((np.array(x_shot) - tower_x[0]) ** 2 + (np.array(y_shot) - tower_y[0]) ** 2)
    out = xr.DataArray(
        dist,
        dims=("shot_number",),
        attrs=dict(
            long_name="Distance of GEDI shot from flux tower",
            units="m",
        ),
    )
    return out

def add_tower_gedi(ax, site, color):
    tower_lat, tower_lon = get_tower_latlon(site)
    tower_roi = np.array(polygons[site][0]["geometry"]["coordinates"][0])

    tower_x, tower_y = transform({'init': 'EPSG:4326'},
                         "EPSG:6933",
                         [tower_lon], [tower_lat])
    
    radius_lon, radius_lat = transform({'init': 'EPSG:6933'},
                         "EPSG:4326",
                         tower_x + 1000*np.cos(np.linspace(0, np.pi*2)),
                         tower_y + 1000*np.sin(np.linspace(0, np.pi*2))
                                     )

    
    ax.add_patch(Polygon(
        tower_roi,
        fill=True, facecolor=color, alpha=0.4, edgecolor=None
    ))
    ax.add_patch(Polygon(
        tower_roi,
        fill=False, edgecolor=color, linewidth=1.5
    ))

    ax.scatter(tower_lon, tower_lat, marker="o", s=10, color="w")
    ax.scatter(tower_lon, tower_lat, marker="*", s=8, color=color)
    
    ax.plot(radius_lon, radius_lat, color='w', lw=2)
    ax.plot(radius_lon, radius_lat, color=color, lw=1.5)


def gedi_qc_mask(gedi):
    q = dict(
        use_gs_flag=True,
        gs_flag_value=1,
        quality_flag=1,
        l2a_quality_flag=1,
        l2b_quality_flag=1,
        degrade_flag_allowed=(0,3,8,10,13,18,20,23,28,30,33,38,40,43,48,60,63,68),
        rh98_max=100,
        rh98_min=0,
        rh50_min=0,
        num_detectedmodes_min=1,
        surface_flag=1,
        sensitivity_min=0.9,
    )
    
    rh50 = gedi["rh"].isel(profile_points=50)
    rh98 = gedi["rh"].isel(profile_points=98)
    
    mask = (
        (gedi["quality_flag"] == q["quality_flag"]) &
        (gedi["l2a_quality_flag"] == q["l2a_quality_flag"]) &
        (gedi["l2b_quality_flag"] == q["l2b_quality_flag"]) &
        (gedi["degrade_flag"].isin(q["degrade_flag_allowed"])) &
        (rh98 <= q["rh98_max"]) &
        (rh98 >= q["rh98_min"]) &
        (rh50 >= q["rh50_min"]) &
        (gedi["num_detectedmodes"] >= q["num_detectedmodes_min"]) &
        (gedi["surface_flag"] == q["surface_flag"]) &
        (gedi["sensitivity"] >= q["sensitivity_min"])
    )

    return mask


residual_data = {'BE-Lon': 0.5491401727023678,
  'CD-Ygb': 0.8752077855450568,
  'CH-Dav': -0.8820181453259748,
  'CZ-Lnz': 0.5030513239372677,
  'DE-Hai': 0.3973944780093158,
  'DE-RuR': -0.8943771827841218,
  'DE-Tha': 1.4044495174852416,
  'ES-LMa': -0.11640112911489914,
  'GF-Guy': -0.23782457785660738,
  'IT-Noe': -0.8351959411192529,
  'US-Rpf': -0.008840619293998467,
  'US-SRG': -0.8512773522604116,
  'US-UMB': -0.10998935199889504,
  'US-UMd': 0.6264346734917793,
  'US-Var': -0.34932102276217075,
  'US-xDS': 1.5773855721468055,
}