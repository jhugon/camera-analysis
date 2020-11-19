#!/usr/bin/env python3

import rawpy
import imageio
import pyexiv2
import sys
import gphoto2 as gp
import glob
import os
import shutil
import tempfile
import numpy as np
import matplotlib.pyplot as plt

from investigate_bias import get_stats

class Camera:

    def __init__(self):
        self.camera = gp.Camera()
        self.camera.init()

        self.iso_config = self.camera.get_single_config("iso")
        self.shutterspeed_config = self.camera.get_single_config("shutterspeed")

    def __del__(self):
        self.camera.exit()

    def __str__(self):
        result = "Camera("
        for key in ["iso","bulb","shutterspeed","aperture"]:
            value = self.camera.get_single_config(key).get_value()
            result += f"{key}={value},"
        result = result[:-1] + ")"
        return result

    def set_iso(self,val):
        allowed_choices = list(self.iso_config.get_choices())
        if not (val in allowed_choices):
            exceptionStr = f"{val} is not one of the allowed iso choices: {allowed_choices}"
            raise Exception(exceptionStr)
        self.iso_config.set_value(val)
        self.camera.set_single_config("iso",self.iso_config)

    def set_shutterspeed(self,val):
        allowed_choices = list(self.shutterspeed_config.get_choices())
        if not (val in allowed_choices):
            exceptionStr = f"{val} is not one of the allowed shutterspeed choices: {allowed_choices}"
            raise Exception(exceptionStr)
        self.shutterspeed_config.set_value(val)
        self.camera.set_single_config("shutterspeed",self.shutterspeed_config)

    def get_isos(self):
        return list(self.iso_config.get_choices())

    def get_shutterspeeds(self):
        return list(self.shutterspeed_config.get_choices())

    def set_config_val(self,key,val):
        camera = self.camera
        config = camera.get_single_config(key)
        allowed_choices = config.get_choices()
        if not (val in allowed_choices):
            exceptionStr = f"{val} is not one of the allowed choices: {list(allowed_choices)}"
            raise Exception(exceptionStr)
        config.set_value(val)
        camera.set_single_config(key,config)

    def capture_image(self,outfn):
        camera_file_path = self.camera.capture(gp.GP_CAPTURE_IMAGE)
        camera_file = self.camera.file_get(camera_file_path.folder, camera_file_path.name, gp.GP_FILE_TYPE_NORMAL)
        camera_file.save(outfn)
        self.camera.file_delete(camera_file_path.folder, camera_file_path.name)

if __name__ == "__main__":

    camera = Camera()

    N = 2
    
    iso_choices = camera.get_isos()[1:]
    shutterspeed_choices = list(reversed(camera.get_shutterspeeds()))
    shutterspeed_choices = shutterspeed_choices[15:]
    print(shutterspeed_choices)
    
    print(f"{'iso':4} {'shutterspeed':14} "+get_stats(None,table_header=True))
    for iso in iso_choices:
        for shutterspeed in shutterspeed_choices:
            shutterspeed_for_fn = shutterspeed
            if "/" in shutterspeed_for_fn:
                shutterspeed_for_fn = shutterspeed_for_fn[2:] + "th"
            elif "." in shutterspeed_for_fn:
                shutterspeed_for_fn = shutterspeed_for_fn.replace('.','p')
            dirname = f"walldata/ISO{iso}/shutter{shutterspeed_for_fn}"
            fname_base = os.path.join(dirname,f"wall_ISO{iso}_shutter{shutterspeed_for_fn}_")
            #print(f"ISO: {iso} shutter speed: {shutterspeed}")
            camera.set_iso(iso)
            camera.set_shutterspeed(shutterspeed)
            with tempfile.NamedTemporaryFile() as tmpf:
                fname = tmpf.name
                camera.capture_image(fname)
                #print(f"  image captured into {fname}")
                img = None
                with rawpy.imread(fname) as raw:
                    try:
                        img = np.array(raw.raw_image[1000:2024,1000:2024],dtype="float32")
                    except Exception:
                        print(f"Error reading image: {fn}")
                        continue
                if np.percentile(img,1.) < 280.:
                    continue
                if np.percentile(img,99.9) > 4000.:
                    break
                print(f"{iso:4} {shutterspeed:14} "+get_stats(img,table=True))
                try:
                    os.makedirs(dirname)
                except FileExistsError:
                    pass
                copy_fn = fname_base + "0001.cr2"
                #print(copy_fn)
                shutil.copyfile(fname,copy_fn)
            for i in range(2,N+1):
                fname = f"{fname_base}{i:04d}.cr2"
                #print(fname)
                camera.capture_image(fname)
        break
