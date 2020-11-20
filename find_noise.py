#!/usr/bin/env python3

import rawpy
import imageio
import pyexiv2
import sys
import glob
import pickle
import numpy as np
import matplotlib.pyplot as plt
from investigate_bias import OnlineStatsCalc, get_stats, make_stats_and_frames
from toy_noise import linear_fit, plot_linear_fit

if __name__ == "__main__":

    fig, (ax1,ax2) = plt.subplots(figsize=(4,8),nrows=2)
    isos = ["100","200","400","800","1600"]
    gains = None
    try:
        with open("gain.pkl","rb") as gain_file:
            gains = pickle.load(gain_file)
    except FileNotFoundError as e:
        print("Warning: Couldn't open gain file: ",e)
    maxstd = 0.
    maxvariance = 0.
    for iso in isos:
        gain = None
        if gains:
            gain = gains[iso]["gain"] # in ADUs / e-
        speed_dirs = glob.glob(f"darkdata/ISO{iso}/*")
        speeds = []
        means = []
        variances = []
        stds = []
        for speed_dir in speed_dirs:
            fns = glob.glob(speed_dir+"/*.cr2")
            stats = None
            shutter_speed = None
            for fn in fns:
                if shutter_speed is None:
                    md = pyexiv2.ImageMetadata(fn)
                    md.read()
                    shutter_speed = md.get_shutter_speed()
                img = None
                with rawpy.imread(fn) as raw:
                    try:
                        img = np.array(raw.raw_image[1000:2024,1000:2024],dtype="float64")
                    except Exception:
                        print(f"Error reading image: {fn}")
                        continue
                if gains:
                    img /= gain # now image is in e-
                if stats is None:
                    stats = OnlineStatsCalc(img.shape)
                stats.add_sample(img)
            mean_img = stats.get_mean()
            variance_img = stats.get_sample_variance()
            std_img = stats.get_sample_std()
            speeds.append(shutter_speed)
            means.append(np.median(mean_img))
            variances.append(np.median(variance_img))
            stds.append(np.median(std_img))
        if len(means) > 0:
            speeds = np.array(speeds,dtype="float32")
            means = np.array(means)
            variances = np.array(variances)
            stds = np.array(stds)
            ax1.scatter(speeds,stds,label="ISO"+iso)
            ax2.scatter(speeds,variances)
            if len(means) > 6:
                print("ISO"+iso)
                fit_results = linear_fit(speeds,variances)
                plot_linear_fit(ax2,speeds,*fit_results)
            for std,variance in zip(stds,variances):
                maxstd = max(std,maxstd)
                maxvariance = max(variance,maxvariance)
    maxstd *= 1.1 
    maxvariance *= 1.1
    ax1.legend()
    ax1.set_xlabel("Exposure Length [s]")
    ax2.set_xlabel("Exposure Length [s]")
    ax1.set_ylim(0,maxstd)
    ax2.set_ylim(0,maxvariance)
    if gains:
        ax1.set_ylabel("Pixel Stddev [e$^-$]")
        ax2.set_ylabel("Pixel Variance [(e$^-$)$^2$]")
    else:
        ax1.set_ylabel("Pixel Stddev [ADUs]")
        ax2.set_ylabel("Pixel Variance [(ADUs)$^2$]")
    fig.savefig("dark_varVmean.png")
    fig.savefig("dark_varVmean.pdf")
