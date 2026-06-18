<div style="text-align: right;">
  <figure style="display: inline-flex; align-items: center;">
    <img src="docs/eo_lincs_logo.png" alt="Logo" style="height: 100px;">
    <figcaption style="font-weight: bold; font-size: 10px; margin-left: 10px;">EO-LINCS</figcaption>
  </figure>
</div>


# SCS1: Explanatory power of novel data streams for predicting net carbon fluxes

This repo gathers code for the SCS1 throughout the project. 

## Short description

**Objective:** The SCS1 aims to link EO data streams to in situ data to predict carbon, water, and energy fluxes. The approach is based on the FLUXCOM-X methodologies, where meteorological and reflectance data from satellites are taken as input to train a machine learning model on the target flux. While the data extraction uses the FLUXCOM-X methodology as a test case, the pipeline is applicable to any use case which matches EO data to eddy covariance measurements. The provided test case is based on eddy covariance data as provided by FLUXNET and associated networks such as the Integrated Carbon Observation System (ICOS) and AmeriFLUX.

**Outcomes:** A working data processing chain able to incorporate new EO data, including Sentinel-2 and Sentinel-3 data, into the FLUXCOM-X framework 
that is updatable and expandable to all sites and other data products. The example case demonstrates the utility of these new data streams for predicting NEE and analysis into the added value with regards to interannual variability,
drought responses, and disturbance.


## Repository structure

The repository is structured as follows:

- `data_extraction` - gathers the data extraction process using [xcube Multi-Source Data Store](https://xcube-dev.github.io/xcube-multistore/).
  The final analysis-ready data cubes are stored in the `data` directory.
- `data` - contains the final analysis-ready data cubes. (will be created during data extraction process)
- `scientific_analyis` - contains the notebooks for the scientific analysis.

For further information, please refer to the ReadMe in the directroies 
`data_extraction` and `scientific_analysis`.
