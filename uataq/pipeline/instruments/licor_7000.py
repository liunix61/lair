#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 30 12:35:34 2023

@author: James Mineau (James.Mineau@utah.edu)

Module of uataq pipeline functions for licor 7000 instrument
"""

import os
import pandas as pd

from config import DATA_DIR, data_config, r2py_types
from ..preprocess import preprocessor
from utils.records import DataFile, filter_files, parallelize_file_parser


INSTRUMENT = 'licor_7000'
data_config = data_config[INSTRUMENT]


@preprocessor
def get_files(site, lvl, time_range=None):
    data_dir = os.path.join(DATA_DIR, site, INSTRUMENT, lvl)

    files = []

    for file in os.listdir(data_dir):
        if file.endswith('dat'):
            file_path = os.path.join(data_dir, file)
            date = pd.to_datetime(file[:7], format='%Y_%m')

            files.append(DataFile(file_path, date))

    return filter_files(files, time_range)


def _parse(file, lvl):
    names = data_config[lvl]['col_names']
    types_R = data_config[lvl]['col_types']
    types = {name: r2py_types[t] for name, t in zip(names, types_R)}

    df = pd.read_csv(file, names=names, dtype=types, header=0,
                     on_bad_lines='skip', na_values=['NAN'])

    # Format time col
    df.rename(columns={'TIMESTAMP': 'Time_UTC'}, inplace=True)
    df['Time_UTC'] = pd.to_datetime(df.Time_UTC, errors='coerce',
                                    format='ISO8601')

    return df


@preprocessor
def read_obs(site, specie='CO2', lvl='calibrated', time_range=None,
             num_processes=1):
    assert specie == 'CO2'

    files = get_files(site, lvl, time_range)

    read_files = parallelize_file_parser(_parse, num_processes=num_processes)
    df = pd.concat(read_files(files, lvl=lvl))

    df = df.dropna(subset='Time_UTC').set_index('Time_UTC').sort_index()
    df = df.loc[time_range[0]: time_range[1]]

    return df
