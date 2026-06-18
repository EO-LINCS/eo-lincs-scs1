## SCS1: Explanatory power of novel data streams for predicting net carbon fluxes

This repo gathers code for the SCS1 throughout the project. 

### Short description

**Objective:** The SCS1 aims to link EO data streams to in situ data to predict carbon, water, and energy fluxes. The approach is based on the FLUXCOM-X methodologies, where meteorological and reflectance data from satellites are taken as input to train a machine learning model on the target flux. While the data extraction uses the FLUXCOM-X methodology as a test case, the pipeline is applicable to any use case which matches EO data to eddy covariance measurements. The provided test case is based on eddy covariance data as provided by FLUXNET and associated networks such as the Integrated Carbon Observation System (ICOS) and AmeriFLUX.

**Outcomes:** A working data processing chain able to incorporate new EO data, including Sentinel-2 and Sentinel-3 data, into the FLUXCOM-X framework
that is updatable and expandable to all sites and other data products. The example case demonstrates the utility of these new data streams for predicting NEE and analysis into the added value with regards to interannual variability,
drought responses, and disturbance.


### How to Generate the Data Cubes

#### Set up the Environment

Before proceeding, ensure that all required dependencies are installed. The recommended approach is to create a Conda environment using the provided environment specification:

`conda env create -f environment.yml`

The corresponding file can be found here: https://github.com/EO-LINCS/eo-lincs-scs1/blob/main/cube_generation/environment.yml

After creation, activate the environment:

`conda activate eo-lincs-scs1`

Next, accessing ERA5 reanalysis data via the Copernicus Data Store (CDS) requires a valid CDS API key. This can be obtained by following the instructions in the [xcube-cds documentation](https://github.com/xcube-dev/xcube-cds#obtain-a-cds-personal-access-token).

Once obtained, the credentials must be added to the configuration file, which will be described in the notebook.
___ 

#### Execute the Cube Generation Pipeline

All scripts and notebooks required for cube generation are located in the `cube_generation` folder.

The main workflow is implemented in `scs1_xcube_multistore.ipynb`, which provides a step-by-step guide through the full cube generation process.

