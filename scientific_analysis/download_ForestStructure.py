import yaml

import pandas as pd
import utm
import pyproj
import matplotlib.pyplot as plt
from xcube_multistore import MultiSourceDataStore

def get_download():
    msds = MultiSourceDataStore("config_ForestStructure.yml")
    return msds
