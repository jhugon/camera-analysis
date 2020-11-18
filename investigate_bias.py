#!/usr/bin/env python3

import rawpy
import imageio
import pyexiv2
import glob
import numpy as np
import matplotlib.pyplot as plt

def make_stats_and_frames(image,fname_base):
        print_stats(image)
        scaled = np.array(image,dtype="float64")
        scaled /= 4096.
        fig, ax = plt.subplots()
        ax.hist(scaled.flatten(),bins=512, histtype="stepfilled",label="Original")
        scaled -= np.quantile(scaled,0.001)
        scaled /= np.quantile(scaled,0.999)
        scaled = np.minimum(scaled,1.)
        scaled = np.maximum(scaled,0.)
        ax.hist(scaled.flatten(),bins=np.linspace(0,1,512), histtype="stepfilled",label="Scaling")
        scaled = scaled**(gamma)
        ax.hist(scaled.flatten(),bins=np.linspace(0,1,512), histtype="stepfilled",label="Gamma")
        ax.legend()
        ax.set_xlim(0,1)
        fig.savefig(fname_base+"_hist.png")
        # now return to 8 bit
        scaled *= 255
        scaled = np.floor(scaled)
        outimg = np.array(scaled,dtype="uint8")
        imageio.imsave(fname_base+".tiff",outimg)

def print_stats(image):
    print(f"mean:  {np.mean(image):.3f}")
    print(f"std:   {np.std(image):.3f}")
    print(f"min:   {np.min(image):.3f}")
    print(f"0.1%:  {np.percentile(image,0.1,interpolation='midpoint'):.3f}")
    print(f" 1%:   {np.percentile(image,1,interpolation='midpoint'):.3f}")
    print(f"25%:   {np.percentile(image,25,interpolation='midpoint'):.3f}")
    print(f"50%:   {np.percentile(image,50,interpolation='midpoint'):.3f}")
    print(f"75%:   {np.percentile(image,75,interpolation='midpoint'):.3f}")
    print(f"99%:   {np.percentile(image,99,interpolation='midpoint'):.3f}")
    print(f"99.9%: {np.percentile(image,99.9,interpolation='midpoint'):.3f}")
    print(f"max:   {np.max(image):.3f}")

class OnlineStatsCalc:
    def __init__(self,shape):
        self.mean = np.zeros(shape)
        self.ss = np.zeros(shape)
        self.n = 0

    def add_sample(self,sample):
        self.n += 1
        delta = sample-self.mean
        self.mean += delta/self.n
        delta2 = sample-self.mean
        self.ss += delta * delta2

    def get_mean(self):
        return self.mean

    def get_sample_std(self):
        return np.sqrt(self.ss/(self.n-1))

bias_fnames = glob.glob("BIAS/*.cr2")

gamma = 0.5
fns_by_iso_shutter_speed = {}
#for i in [100,200,400,800,1600]:
for i in [800,1600]:
    fns_by_iso_shutter_speed[i] = {}

for fname in bias_fnames:
    md = pyexiv2.ImageMetadata(fname)
    md.read()
    shutter_speed = md.get_shutter_speed()
    iso = md.get_iso()
    try:
        fns_by_iso_shutter_speed[iso][shutter_speed].append(fname)
    except KeyError:
        fns_by_iso_shutter_speed[iso][shutter_speed] = [fname]

print("Bias Frames:")
for iso in sorted(fns_by_iso_shutter_speed):
    for shutter_speed in sorted(fns_by_iso_shutter_speed[iso]):
        fn_list = fns_by_iso_shutter_speed[iso][shutter_speed]
        #fn_list = fn_list[:10]
        nFiles = len(fn_list)
        print(f"ISO: {iso}, Shutter Speed: {shutter_speed}, N frames: {nFiles}")
        stats = None
        for fn in fn_list:
            img = None
            with rawpy.imread(fn) as raw:
                try:
                    img = np.array(raw.raw_image,dtype="float64")
                except Exception:
                    print(f"Error reading image: {fn}")
                    continue
            #img = img[1000:2024,1000:2024]
            if stats is None:
                stats = OnlineStatsCalc(img.shape)
            stats.add_sample(img)
        mean_img = stats.get_mean()
        std_img = stats.get_sample_std()
        print("Mean Frame:")
        make_stats_and_frames(mean_img,f"bias_mean_iso{iso}")
        print("Stddev Frame:")
        make_stats_and_frames(std_img,f"bias_std_iso{iso}")

dark_fnames = glob.glob("DARK/*.cr2")

gamma = 0.5
fns_by_iso_shutter_speed = {}
#for i in [100,200,400,800,1600]:
for i in [800,1600]:
    fns_by_iso_shutter_speed[i] = {}

for fname in dark_fnames:
    md = pyexiv2.ImageMetadata(fname)
    md.read()
    shutter_speed = md.get_shutter_speed()
    iso = md.get_iso()
    try:
        fns_by_iso_shutter_speed[iso][shutter_speed].append(fname)
    except KeyError:
        fns_by_iso_shutter_speed[iso][shutter_speed] = [fname]

print("Dark Frames:")
shutter_speeds_by_iso = {}
stds_by_iso = {}
for iso in sorted(fns_by_iso_shutter_speed):
    shutter_speeds_by_iso[iso] = []
    stds_by_iso[iso] = []
    for shutter_speed in sorted(fns_by_iso_shutter_speed[iso]):
        fn_list = fns_by_iso_shutter_speed[iso][shutter_speed]
        #fn_list = fn_list[:10]
        nFiles = len(fn_list)
        print(f"ISO: {iso}, Shutter Speed: {shutter_speed}, N frames: {nFiles}")
        mean_img = None
        for fn in fn_list:
            img = None
            with rawpy.imread(fn) as raw:
                try:
                    img = np.array(raw.raw_image,dtype="float64")
                except Exception:
                    print(f"Error reading image: {fn}")
                    continue
            #img = img[1000:2024,1000:2024]
            if stats is None:
                stats = OnlineStatsCalc(img.shape)
            stats.add_sample(img)
        mean_img = stats.get_mean()
        std_img = stats.get_sample_std()
        print("Mean Frame:")
        make_stats_and_frames(mean_img,f"dark_mean_iso{iso}_{shutter_speed}s")
        print("Stddev Frame:")
        make_stats_and_frames(std_img,f"dark_std_iso{iso}_{shutter_speed}s")
        stds_by_iso[iso].append(np.median(std_img))
        shutter_speeds_by_iso[iso].append(float(shutter_speed))

fig, ax = plt.subplots()
for iso in sorted(stds_by_iso):
    shutter_speeds = np.array(shutter_speeds_by_iso[iso])
    stds = np.array(stds_by_iso[iso])
    print(iso)
    print(shutter_speeds)
    print(stds)
    ax.scatter(shutter_speeds,stds,label=f"ISO={iso}")
ax.legend()
ax.set_xlabel("Shutter Speed [s]")
ax.set_ylabel("Pixel Standard Deviation (ADUs)")
fig.savefig("dark_stdsVspeed.png")
fig.savefig("dark_stdsVspeed.pdf")
