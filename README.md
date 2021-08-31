# dNBR Calculator For Sentinel 2

This script is used to calculate difference Normalized Burn Ratio from Sentinel 2 images that have processing level 2A. Script calculates and classifies dNBR result and then writes it to an output file (".tiff" extension is recommended).

## Requirements

```bash
pip install rasterio sentinelsat numpy
```

## Usage

To use this script you need to register [Copernicus Open Access Hub](https://scihub.copernicus.eu/dhus/#/self-registration). And also you should use [Copernicus Map](https://scihub.copernicus.eu/dhus/#/home) to select pre and post wildfire images. My recommendation is to use advanced search for filtering. After the search you can select the title, or you can view the product details and select identifier from there. You should find pre and post fire images' identifiers (titles). Then you just use script basically like this:

```bash
python dnbr.py "username" "password" "image title 1" "image title 2" "output_file_name.tiff"
```

### Example (Manavgat Wildfire)

You should use your username and password.

```bash
python dnbr.py "username" "password" "S2B_MSIL2A_20210720T083559_N0301_R064_T36SUF_20210720T113645" "S2B_MSIL2A_20210809T083559_N0301_R064_T36SUF_20210809T115822" "Manavgat_dnbr.tiff"
```
