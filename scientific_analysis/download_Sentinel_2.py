import yaml

import pandas as pd
import utm
import pyproj
import matplotlib.pyplot as plt
from xcube_multistore import MultiSourceDataStore

def get_download():
    msds = MultiSourceDataStore("config_Sentinel2.yml")
    msds.generate()
    return msds

if __name__ == '__main__':
    get_download()
