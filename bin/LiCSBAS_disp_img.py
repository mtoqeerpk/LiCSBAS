#!/usr/bin/env python3
"""
========
Overview
========
This script displays an image file (only in float format).

=========
Changelog
=========
v1.1 20190828 Yu Morishita, Uni of Leeds and GSI
 - Add --png option
v1.0 20190729 Yu Morishita, Uni of Leeds and GSI
 - Original implementation

=====
Usage
=====
LiCSBAS_disp_img.py -i image_file -p par_file [-c SCM5.roma_r] [--cmin None] [--cmax None] [--auto_crange 99]  [--cycle 3] [--bigendian] [--png [pngname]]

 -i  Input image file in float32
 -p  Parameter file containing width and length (e.g., EQA.dem_par or mli.par)
 -c  Colormap (see below for available colormap)
     - https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html
     - http://www.fabiocrameri.ch/colourmaps.php
     - insar
     (Default: SCM5.roma_r, reverse of SCM5.roma)
 --cmin|cmax    Min|max values of color (Default: auto)
 --auto_crange  % of color range used for automatic determinatin (Default: 99%)
 --cycle        Value*2pi/cycle if cmap=insar (Default: 3*2pi/cycle)
 --bigendian    If input file is in big endian
 --png          Save png (pdf etc also available) instead of displaying

"""


#%% Import
import getopt
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import subprocess as subp
import SCM5

import LiCSBAS_tools_lib as tools_lib
import LiCSBAS_io_lib as io_lib

class Usage(Exception):
    """Usage context manager"""
    def __init__(self, msg):
        self.msg = msg


#%% Main
## Not use def main to use global valuables
if __name__ == "__main__":
    argv = sys.argv

    #%% Set default
    infile = []
    parfile = []
    cmap = "SCM5.roma_r"
    cmin = None
    cmax = None
    auto_crange = 99
    cycle = 3
    endian = 'little'
    pngname = []
    
    
    #%% Read options
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hi:p:c:", ["help", "cmin=", "cmax=", "auto_crange=", "cycle=", "bigendian", "png="])
        except getopt.error as msg:
            raise Usage(msg)
        for o, a in opts:
            if o == '-h' or o == '--help':
                print(__doc__)
                sys.exit(0)
            elif o == '-i':
                infile = a
            elif o == '-p':
                parfile = a
            elif o == '-c':
                cmap = a
            elif o == '--cmin':
                cmin = float(a)
            elif o == '--cmax':
                cmax = float(a)
            elif o == '--auto_crange':
                auto_crange = float(a)
            elif o == '--cycle':
                cycle = float(a)
            elif o == '--bigendian':
                endian = 'big'
            elif o == '--png':
                pngname = a

        if not infile:
            raise Usage('No image file given, -i is not optional!')
        elif not os.path.exists(infile):
            raise Usage('No {} exists!'.format(infile))
        if not parfile:
            raise Usage('No par file given, -p is not optional!')
        elif not os.path.exists(parfile):
            raise Usage('No {} exists!'.format(parfile))

    except Usage as err:
        print("\nERROR:", file=sys.stderr, end='')
        print("  "+str(err.msg), file=sys.stderr)
        print("\nFor help, use -h or --help.\n", file=sys.stderr)
        sys.exit(2)


    #%% Set cmap if SCM5
    if cmap.startswith('SCM5'):
        if cmap.endswith('_r'):
            exec("cmap = {}.reversed()".format(cmap[:-2]))
        else:
            exec("cmap = {}".format(cmap))
    elif cmap == 'insar':
        cdict = tools_lib.cmap_insar()
        plt.register_cmap(name='insar', data=cdict)


    #%% Get info
    try:
        try:
            ### EQA.dem_par
            width = int(subp.check_output(['grep', 'width', parfile]).decode().split()[1].strip())
            length = int(subp.check_output(['grep', 'nlines', parfile]).decode().split()[1].strip())
        except:
            ### slc.mli.par
            width = int(subp.check_output(['grep', 'range_samples', parfile]).decode().split()[1].strip())
            length = int(subp.check_output(['grep', 'azimuth_lines', parfile]).decode().split()[1].strip())
    except:
        print('No fields about width/length found in {}!'.format(parfile), file=sys.stderr)
        sys.exit(2)


    #%% Read data
    data = io_lib.read_img(infile, length, width, endian=endian)
    
    if cmap == 'insar':
        data = np.angle(np.exp(1j*(data/cycle))*cycle)
        cmin = -np.pi
        cmax = np.pi


    #%% Set color range for displacement and vel
    if cmin is None and cmax is None: ## auto
        climauto = True
        cmin = np.nanpercentile(data, 100-auto_crange)
        cmax = np.nanpercentile(data, auto_crange)
    else:
        climauto = False
        if cmin is None: cmin = np.nanpercentile(data, 100-auto_crange)
        if cmax is None: cmax = np.nanpercentile(data, auto_crange)


    #%% Plot figure
    figsize_x = 6 if length > width else 8
    figsize = (figsize_x, ((figsize_x-2)*length/width))
    plt.figure('{}'.format(infile), figsize)
    plt.imshow(data, clim=[cmin, cmax], cmap=cmap)
    if not cmap == 'insar': plt.colorbar()
    plt.tight_layout()
    
    if pngname:
        plt.savefig(pngname)
        print('\nOutput: {}\n'.format(pngname))
    else:
        plt.show()
