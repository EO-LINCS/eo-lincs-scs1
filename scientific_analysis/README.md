<div style="text-align: right;">
  <figure style="display: inline-flex; align-items: center;">
    <img src="../docs/eo_lincs_logo.png" alt="Logo" style="height: 100px;">
    <figcaption style="font-weight: bold; font-size: 10px; margin-left: 10px;">EO-LINCS</figcaption>
  </figure>
</div>

# Scientific Analysis

This directory contains the notebooks and supporting functions used for the scientific 
analysis. All notebooks apply the methods described in the EO-LINCS Deliverable D5.4: Community Assessment Description.



### Introduction

Scientific Case Study 1 aims to improve estimates of net ecosystem exchange (NEE) across diverse biomes by integrating novel Earth Observation (EO) data streams into data-driven flux up-scaling. The central challenge is twofold: (1) representing spatial differences among sites linked to ecosystem structure and functioning (e.g., vegetation amount, composition, and productivity), and (2) capturing temporal variability driven by weather, management, and disturbances, with water limitation as a dominant control in many regions. The scientific objective is therefore to test whether additional EO information can better constrain these spatial and temporal drivers and, in turn, improve the performance and interpretability of machine-learning flux models.


The case study is based on the FLUXCOM-X framework (Nelson et al., 2024), which trains machine-learning
models on eddy-covariance observations and predicts fluxes using remote sensing predictors. Eddy-covariance
stations provide spatially integrated, temporally continuous measurements of carbon, water, and energy ex-
change (Baldocchi, 2019), typically sampling an upwind footprint of a few hundred metres up to ~1 km de-
pending on conditions (Chu et al., 2021). Being persistance in situ measurments, many sites provide near-
continuous half-hourly records over multiple years, with the longest running sites spanning decades (Pas-
torello et al., 2020).

The case study is based on the FLUXCOM-X framework [Nelson et al., 2024](https://doi.org/10.5194/bg-21-5079-2024), which trains machine-learning models on eddy-covariance observations and predicts fluxes using remote sensing predictors. Eddy-covariance stations provide spatially integrated, temporally continuous measurements of carbon, water, and energy exchange [Baldocchi, 2019](https://doi.org/10.1111/gcb.14807), typically sampling an upwind footprint of a few hundred metres up to ~1 km depending on conditions [Chu et al., 2021](https://doi.org/10.1016/j.agrformet.2021.108350). Because they provide persistent in situ monitoring, many sites deliver near-continuous half-hourly records over multiple years, with the longest running sites spanning decades [Pastorello et al., 2020](https://doi.org/10.1038/s41597-020-0534-3).

Currently, the FLUXCOM-X framework is based on MODIS- and VIIRS-based reflectance and land-surface temperature, together with meteorological inputs measured at each tower and plant functional type classifications, as predictors to the model. The inclusion of remote sensing data has been shown to be an important predictor in FLUXCOM-X, providing key information on ecosystem states not reflected in the immediate meteorology, such as phenology or stress conditions [Kraft et al., 2025](https://doi.org/10.5194/bg-22-3965-2025). Linking these in situ observations with EO data is therefore essential for scaling local ecosystem behaviour to regional and global flux estimates.

The key limitation to FLUXCOM-X like up-scaling problems is that we are currently data limited, both in the number of sites sampled and the predictors available to describe the ecosystem functions driving biogenic carbon fluxes. However, many EO products come with a fundamental trade-off between spatial and temporal resolution. For example, Sentinel‑2 (~20 m resolution) can better resolve heterogeneous landscapes and small tower footprints (e.g., croplands), but revisit frequency (~5 days) is often insufficient to capture rapid dynamics such as green-up and senescence. Moreover, because eddy-covariance fluxes integrate over footprints far larger than 20 m pixels, aggregation is always required. Attempting to predict fluxes at resolutions much finer than a few hundred metres is likely to introduce representativeness and extrapolation errors. Therefore, the integration of multiple data sources is needed, which can incorporate new information (e.g. biomass, forest structure, finer spectral information such as red edge bands) in a way which can capture both spatial representativeness and temporal signals.

One key piece of information needed to go to higher spatial resolutions is explicit tower footprints or regions of interests for all towers, information that is still in development by the eddy covariance networks. This information is starting to come online, with regions of interest now published for ICOS Class 1 sites, and current projects such as NextGenCarbon are expected to develop operational footprint predictions for all sites within the next two years, which will be a major advance for improving eddy covariance and EO data. The EO-LINCS pipelines therefore can play a key role in facilitating the extraction of data products from different sources and with different spatial and temporal resolutions in a flexible and dynamic way. Here we present a proof of concept of this framework by exploring the potential of incorporating new data sources based on what is currently available and feasible within the time frame of the project, but with the idea that these same pipelines can be expanded and repurposed by both FLUXCOM-X and the broader carbon cycle community beyond the project.

This proof of concept can be separated into the spatial and temporal components:

**Spatial variability:** NEE remains harder to model than gross primary productivity (GPP) because respiration-related variability is only weakly constrained by optical “greenness” signals. In the current FLUXCOM-X X-BASE products, much of the spatial pattern is driven by categorical plant functional type (PFT) information, which increases the risk of over-fitting and poor extrapolation outside the conditions represented by the training data. For example, X-BASE can produce unrealistic behaviour across cropland regions in the Indian subcontinent and the Sahel, where relevant crop systems are sparsely sampled by the existing eddy-covariance network and therefore weakly constrained. Similar issues appear in preliminary runs with updated site sets, where sparsely treed Siberian systems can be classified as “savannah-like” and then mapped to dryland savannah behaviour learned from better-sampled regions. Incorporating EO-derived site characteristics that vary continuously in space, such as vegetation structure, biomass, and canopy condition, offers a potential pathway to reduce reliance on discrete classes and improve spatial generalisation. Here we explore the use of high-resolution forest structure products such as ESA CCI biomass, GEDI data, and the compiled products from the [EO Forest STAC Catalog](https://simonbesnard1.github.io/eoforeststac) as replacements for PFT information.

**Temporal variability:** Another challenging aspect of NEE variability to capture comes from short-term shifts in ecosystem state, particularly water stress and associated down-regulation of carbon uptake and changes in respiration. Sentinel-3 OLCI provides red-edge bands that are sensitive to vegetation biochemical and structural properties and have shown strong potential for improving retrievals of biophysical variables relevant to stress and phenology [Li et al., 2024](https://doi.org/10.1016/j.scitotenv.2023.168594). In addition, spatial representativeness remains a practical limitation: VIIRS reflectance products are typically available at ~1 km resolution, which can exceed the effective footprint of many towers. Sentinel-3 SYNERGY reflectances at ~300 m offer improved alignment with tower sampling areas, potentially strengthening both temporal signal quality and site-level representativeness.


In addition to direct comparisons of these projects, we also present an initial analysis of Sentinel-2 data. Its higher spatial resolution could serve as a valuable bridge between high-resolution forest structure products, typically static or updated only annually, and coarser-resolution but higher-temporal-resolution products like those from Sentinel-3. In particular, we demonstrate the implementation of an additional cloud mask to remove clouds not identified in the standard L2A Scene Classification Layer (SCL). While the integration of Sentinel-2 into FLUXCOM-X is not done within this project, as it would require eddy covariance footprints for each half hour, which are not currently available, the initial analysis is presented here as a demonstration of analysis ready data which incorporates multiple EO data sources with eddy covariance fluxes.

#### FLUXCOM-X residuals

As an initial test of each dataset’s potential to improve NEE prediction, we related candidate EO metrics to the cross-validation residuals from the baseline FLUXCOM-X model. The baseline setup included meteorological drivers, plant functional type information, and VIIRS-based land surface temperature and vegetation indices (EVI, NIRv, NDWI). Models were trained using gradient-boosted regression trees (XGBoost) in a 10-fold cross-validation scheme. For each fold, we computed NEE residuals as observed NEE minus cross-validated model predictions, which represent the variance not explained by the baseline predictors. Comparing new EO metrics to these residuals provides a first-order indication of their added value beyond the existing FLUXCOM-X feature set.


The workflow can be run in any order and is structured as follows:

1. `ForestStructure.ipynb` An example looking at spatial variability from forest structure characteristics.
2. `Sentinel2.ipynb` A short demonstration of additional Sentinel-2 Cloud Masking.
3. `Sentinel3.ipynb` An example of Sentinel-3 temporal variability at a dryland site. *Note: This script is still in development*

As the example data extraction pipeline in `data_extraction/data_extraction.ipynb` is minimizeds to only one site and a short timeperiod, expanded data extraction configurations are provided, along with an associated download script:

| example notebook | config file | download script | additional utilities |
|----|----|----|----|
| `ForestStructure.ipynb` | `config_ForestStructure.yml` | `download_ForestStructure.py` | `forest_structure_utils.py` |
| `Sentinel2.ipynb` | `config_Sentinel2.yml` | `download_Sentinel_2.py` | `cloud_mask_utils.py` |

Additionally, there are pre-defined regions of interest for some ICOS sites in `ICOS_rio.json`.

## Methods

In all cases, EO products are extracted as spatial cut-outs covering a **2 km radius** centred on each flux tower. This larger domain supports flexible spatial aggregation and sensitivity tests. For the initial analyses reported here, we used a **1 km radius mean** as a consistent first-order footprint proxy that can be applied across all sites.

**Sentinel‑3 SYNERGY (SYN):** We computed standard vegetation indices (NDVI, EVI, NIRv) to enable direct comparison with VIIRS-based predictors, and tested red-edge indices including $NDVI_{705}$ and OTCI to assess added value from Sentinel-3 spectral capabilities. Pixel-level screening relied primarily on `SYN_flags` to remove poor-quality retrievals and mask clouds and snow. Initial analysis here focused on responses to dryness at the Santa Rita Grassland (US-SRG), a seasonally dry grassland. As an initial assessment, all vegetation indices were smoothed using a 27 day locally estimated scatterplot smoothing (LOESS) filter to smooth effects from sun–sensor geometry.

**Sentinel‑2 L2A:** Analyses focused on improving cloud and cloud-shadow detection. All spectral bands were extracted together with the SCL for baseline masking, and additional cloud/shadow filtering was applied using OmniCloudMask. Initial analysis focused on the scaled wide dynamic range vegetation index (sWDRVI).

**Above-ground biomass:** We used above-ground biomass from [Saatchi et al.](https://doi.org/10.1073/pnas.1019576108) and ESA CCI Biomass v5.0. For the initial assessment, ESA CCI biomass was averaged across available years to provide a stable structural constraint.

**Canopy height:** Mean canopy height was taken from the global canopy height product of [Potapov et al.](https://doi.org/10.1016/j.rse.2020.112165).

**Tree cover:** Percent tree cover for the year 2000 was taken from [Hansen et al.](https://doi.org/10.1126/science.1244693).

**Chapman–Richards parameters:** We included Chapman–Richards growth-curve parameters and derived metrics describing secondary-forest above-ground carbon accumulation, with emphasis on the maximum annual accumulation rate and the asymptotic maximum above-ground carbon stock.

**GEDI:** All GEDI LiDAR shots within a 1 km radius of each tower were extracted, along with derived structural variables where available (e.g., canopy height metrics and above-ground biomass density). After applying standard quality filtering, shots were spatially aggregated to produce a site-level mean.

