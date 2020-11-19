#!/usr/bin/env python3

import rawpy
import imageio
import pyexiv2
import glob
import numpy as np
import matplotlib.pyplot as plt
from investigate_bias import OnlineStatsCalc, get_stats, make_stats_and_frames
from toy_noise import linear_fit, plot_linear_fit

if __name__ == "__main__":

    fig, ax = plt.subplots()
    isos = ["100","200","400","800","1600"]
    gains = []
    gain_errs = []
    for iso in isos:
        speed_dirs = glob.glob(f"walldata/ISO{iso}/*")
        means = []
        variances = []
        for speed_dir in speed_dirs:
            fns = glob.glob(speed_dir+"/*.cr2")
            stats = None
            for fn in fns:
                img = None
                with rawpy.imread(fn) as raw:
                    try:
                        img = np.array(raw.raw_image[1000:2024,1000:2024],dtype="float64")
                    except Exception:
                        print(f"Error reading image: {fn}")
                        continue
                if stats is None:
                    stats = OnlineStatsCalc(img.shape)
                stats.add_sample(img)
            mean_img = stats.get_mean()
            variance_img = stats.get_sample_variance()
            means.append(np.median(mean_img))
            variances.append(np.median(variance_img))
        if len(means) > 0:
            means = np.array(means)
            variances = np.array(variances)
            ax.scatter(means,variances,label="ISO"+iso)
            print("ISO"+iso)
            fit_results = linear_fit(means,variances)
            gains.append(fit_results[0])
            gain_errs.append(fit_results[2])
            plot_linear_fit(ax,means,*fit_results)
        else:
            gains.append(float('nan'))
            gain_errs.append(float('nan'))
    ax.legend()
    ax.set_xlabel("Pixel Mean [ADUs]")
    ax.set_ylabel("Pixel Variance [(ADUs)$^2$]")
    fig.savefig("wall_varVmean.png")
    fig.savefig("wall_varVmean.pdf")

    print(f"{'ISO':4} Gain [e-/ADU]")
    for iso, gain, gain_err in zip(isos,gains,gain_errs):
        print(f"{iso:4} {gain:6.3f} +/- {gain_err:6.3f}")
