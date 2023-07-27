from osgeo import gdal
import numpy as np
import pandas as pd
import tqdm
import argparse
import os


parser = argparse.ArgumentParser(description="preprocess tif files")
parser.add_argument("--region", type=str, help="name of region")
parser.add_argument(
    "--band", type=str, default="pdsi", help="name of variable to process"
)
parser.add_argument("--endyear", type=int, default=2020, help="last year of data")
parser.add_argument(
    "--endmonth", type=int, default=1, help="last month of data, from 1 to 12"
)
args = parser.parse_args()
region = args.region
feature = args.band
endyear = args.endyear
endmonth = args.endmonth

save_path = "data/preprocessed/"


ds = gdal.Open("data/raw/" + region + "_" + feature + ".tif")
print(ds.GetMetadata())
print("number of months ", ds.RasterCount)
print("x dim ", ds.RasterXSize)
print("y dim ", ds.RasterYSize)

num_of_months = ds.RasterCount
xsize = ds.RasterXSize
ysize = ds.RasterYSize
all_data = np.zeros((num_of_months, 1, ysize, xsize))

curr_month = endmonth
curr_year = endyear
total_df = pd.DataFrame(columns=["date", "x", "y", "value"])


for i in tqdm.tqdm(range(num_of_months - 1, 1, -1)):
    if curr_month == 0:
        curr_month = 12
        curr_year -= 1

    curr_date = str(curr_year) + "-" + str(curr_month)
    band = ds.GetRasterBand(i)
    data = band.ReadAsArray()
    # pdsi needs to be normalized by 100
    if feature == "pdsi":
        data = data / 100
    all_data[i][0] = data
    for x in range(xsize):
        for y in range(ysize):
            total_df = total_df.append(
                {"date": curr_date, "x": x, "y": y, "value": data[x][y]},
                ignore_index=True,
            )

    curr_month -= 1

np.save(save_path + region + "_" + feature + ".npy", all_data)
total_df.to_csv(save_path + region + "_" + feature + ".csv")
print(f"{region} global stats")
print(f"mean: {np.mean(all_data)}")
print(f"std: {np.std(all_data)}")
num_of_channels = 1
global_means = np.zeros((1, num_of_channels, 1, 1))
global_stds = np.zeros((1, num_of_channels, 1, 1))
global_means[0, 0, 0, 0] = np.mean(all_data)
global_stds[0, 0, 0, 0] = np.std(all_data)
np.save(save_path + region + "_" + feature + "_global_means.npy", global_means)
np.save(save_path + region + "_" + feature + "_global_stds.npy", global_stds)
