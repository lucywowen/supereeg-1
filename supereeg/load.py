from __future__ import print_function
import os
import warnings
import requests
import numpy as np
import deepdish as dd
import pandas as pd
from .brain import Brain
from .model import Model
from .nifti import Nifti
from .helpers import tal2mni, _gray, _std, _resample_nii

BASE_URL = 'https://docs.google.com/uc?export=download'
homedir = os.path.expanduser('~/')
datadir = os.path.join(homedir, 'supereeg_data')

datadict = {
    'example_data' : ['1kijSKt-QLEZ1O3J5Pk-8aByn33bPCAFl', 'bo'],
    'example_model' : ['1l4s7mE0KbPMmIcIA9JQzSZHCA8LWFq1I', 'mo'],
    'example_nifti' : ['1a8wptBaMIFEl4j8TFhlTQVUAbyC0sN4p', 'nii'],
    'example_filter' : ['1eHcYg1idIK8y2LMLK_tqSxB7jI_l7OsL', 'bo'],
    'std' : ['1P-WcEBVYnoMQAYhvSCf1BBMIDMe9VZIM', 'nii'],
    'gray' : ['1a8wptBaMIFEl4j8TFhlTQVUAbyC0sN4p', 'nii'],
}

def load(fname, vox_size=None, return_type=None):
    """
    Load nifti file, brain or model object, or example data.

    This function can load in example data, as well as nifti objects (.nii), brain objects (.bo)
    and model objects (.mo) by detecting the extension and calling the appropriate
    load function.  Thus, be sure to include the file extension in the fname
    parameter.

    Parameters
    ----------
    fname : str

        The name of the example data or a filepath.


        Examples includes :

            example_data - example brain object (n = 64)

            example_filter - load example patient data with kurtosis thresholded channels (n = 40)

            example_model - example model object with locations from gray masked brain downsampled to 20mm (n = 210)

            example_nifti - example nifti file from gray masked brain downsampled to 20mm (n = 210)


        Nifti templates :

            gray - load gray matter masked MNI 152 brain

            std - load MNI 152 standard brain


        Models :

            pyfr - model used for analyses from Owen LLW and Manning JR (2017) Towards Human Super EEG. bioRxiv: 121020`

                vox_size options: 6mm and 20mm


    vox_size : int or float

        Voxel size for loading and resampling nifti image

    return_type : str

        Option for loading data

            'bo' - returns supereeg.Brain

            'mo' - returns supereeg.Model

            'nii' - returns supereeg.Nifti

    Returns
    ----------
    data : supereeg.Nifti, supereeg.Brain or supereeg.Model
        Data to be returned

    """

    if fname in datadict.keys():
        data = _load_example(fname, datadict[fname])
    else:
        data = _load_from_path(fname)
    return _convert(data, return_type, vox_size)

def _convert(data, return_type, vox_size):
    """ Converts between bo, mo and nifti """
    if return_type is None:
        return data
    elif return_type is 'nii':
        if type(data) is not Nifti:
            data = Nifti(data)
        if vox_size:
            return _resample_nii(data, target_res=vox_size)
        else:
            return data
    elif return_type is 'bo':
        if type(data) is not Brain:
            data = Brain(data)
        return data
    elif return_type is 'mo':
        if type(data) is not Model:
            data = Model(data)
        return data

def _load_example(fname, fileid):
    """ Loads in dataset given a google file id """
    fullpath = os.path.join(homedir, 'supereeg_data', fname)
    if not os.path.exists(datadir):
        os.makedirs(datadir)
    if not os.path.exists(fullpath):
        _download(fname, _load_stream(fileid[0]), fileid[1])
        data = _load_from_cache(fname, fileid[1])
    else:
        data = _load_from_cache(fname, fileid[1])
    return data

def _load_stream(fileid):
    """ Retrieve data from google drive """
    def _get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value
        return None
    url = BASE_URL + fileid
    session = requests.Session()
    response = session.get(BASE_URL, params = { 'id' : fileid }, stream = True)
    token = _get_confirm_token(response)
    if token:
        params = { 'id' : fileid, 'confirm' : token }
        response = session.get(BASE_URL, params = params, stream = True)
    return response

def _download(fname, data, ext):
    """ Download data to cache """
    fullpath = os.path.join(homedir, 'supereeg_data', fname)
    with open(fullpath + '.' + ext, 'wb') as f:
        f.write(data.content)

def _load_from_path(fpath):
    """ Load a file from a local path """
    try:
        ext = fpath.split('.')[-1]
    except:
        raise ValueError("Must specify a file extension.")
    if ext=='bo':
        return Brain(**dd.io.load(fpath))
    elif ext=='mo':
        return Model(**dd.io.load(fpath))
    elif ext=='nii':
        return Nifti(fpath)
    else:
        raise ValueError("Filetype not recognized. Must be .bo, .mo or .nii.")

def _load_from_cache(fname, ftype):
    """ Load a file from local data cache """
    fullpath = os.path.join(homedir, 'supereeg_data', fname + '.' + ftype)
    if ftype is 'bo':
        return Brain(**dd.io.load(fullpath))
    elif ftype is 'mo':
        return Model(**dd.io.load(fullpath))
    elif ftype is 'nii':
        return Nifti(fullpath)
