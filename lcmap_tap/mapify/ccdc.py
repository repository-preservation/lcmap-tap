"""
Reading CCDC raw results, typically JSON or pickle formats for test data.
"""
import os
import json
import pickle
import logging
from typing import Tuple, List, Sequence

import numpy as np

from mapify.products import BandModel, CCDCModel
from mapify.spatial import buildaff, transform_geo
from mapify.app import band_names as _band_names


log = logging.getLogger()


def jsonpaths(root: str) -> list:
    """
    Create a list of file paths to files that end in .json in the given directory.

    Args:
        root: directory path

    Returns:
        sorted list of JSON file paths
    """
    return [os.path.join(root, f)
            for f in sorted(os.listdir(root))
            if f[-5:] == '.json']


def picklepaths(root: str) -> list:
    """
    Create a list of file paths to files that end in .p in the given directory.

    Args:
        root: directory path

    Returns:
        sorted list of pickle file paths
    """
    return [os.path.join(root, f)
            for f in sorted(os.listdir(root))
            if f[-2:] == '.p']


def pathcoords(path: str) -> Tuple[int, int]:
    """
    Pull the Chip X and Chip Y coords from the file path.

    Args:
        path: file path

    Returns:
        chip upper left x/y based on the file name
    """
    parts = os.path.split(path)[-1].split('_')
    return int(parts[1]), int(parts[2][:-5])


def loadjfile(path: str) -> list:
    """
    Load a JSON formatted file into a dictionary.

    Args:
        path: file path

    Returns:
        dictionary representation of the JSON
    """
    return json.load(open(path, 'r'))


def loadjstr(string: str) -> dict:
    """
    Load a JSON formatted string into a dictionary.

    Args:
        string: JSON formatted string

    Returns:
        dictionary representation of the JSON
    """
    return json.loads(string)


def loadpfile(path: str) -> list:
    """
    Loads whatever object is contained in the pickle file.

    Args:
        path: file path

    Returns:
        some object
    """
    return pickle.load(open(path, 'rb'))


def empty(band_names: Sequence=_band_names) -> CCDCModel:
    """
    Return an empty CCDC model

    Args:
        band_names: bands to build

    Returns:
        CCDCModel
    """
    bands = [BandModel(name=b, magnitude=0.0, rmse=0.0, intercept=0.0, coefficients=tuple([0.0] * 6))
             for b in band_names]

    return CCDCModel(start_day=0,
                     end_day=0,
                     break_day=0,
                     obs_count=0,
                     change_prob=0.0,
                     curve_qa=0,
                     bands=tuple(bands),
                     class_split=0,
                     class_probs1=tuple([0] * 9),
                     class_probs2=tuple([0] * 9),
                     class_vals=tuple(range(9)))


def buildband(chgmodel: dict, name: str) -> BandModel:
    """
    Build an individual band namedtuple from a change model

    Args:
        chgmodel: dictionary repesentation of a change model
        name: which band to build
    
    Returns:
        individual band model
    """
    return BandModel(name=name,
                     magnitude=chgmodel[name]['magnitude'],
                     rmse=chgmodel[name]['rmse'],
                     coefficients=tuple(chgmodel[name]['coefficients']),
                     intercept=chgmodel[name]['intercept'])


def buildccdc(chgmodel: dict, cl1model: dict=None,
              cl2model: dict=None, band_names: Sequence=_band_names) -> CCDCModel:
    """
    Build a complete CCDC model

    Args:
        chgmodel: dictionary representation of a change model
        cl1model: dictionary representation of a classification model
        cl2model: dictionary representation of the second part of annualized classification (if it exists for this segment)
        band_names: band names present in the change model

    Returns:
        a unified CCDC model
    """
    bands = [buildband(chgmodel, b) for b in band_names]

    if cl1model is None:
        return CCDCModel(start_day=chgmodel['start_day'],
                         end_day=chgmodel['end_day'],
                         break_day=chgmodel['break_day'],
                         obs_count=chgmodel['observation_count'],
                         change_prob=chgmodel['change_probability'],
                         curve_qa=chgmodel['curve_qa'],
                         bands=tuple(bands),
                         class_split=0,
                         class_probs1=np.zeros(shape=(8,)),
                         class_probs2=np.zeros(shape=(8,)),
                         class_vals=tuple([0] * 9))
    elif cl2model is None:
        return CCDCModel(start_day=chgmodel['start_day'],
                         end_day=chgmodel['end_day'],
                         break_day=chgmodel['break_day'],
                         obs_count=chgmodel['observation_count'],
                         change_prob=chgmodel['change_probability'],
                         curve_qa=chgmodel['curve_qa'],
                         bands=tuple(bands),
                         class_split=0,
                         class_probs1=np.array(cl1model['class_probs']),
                         class_probs2=np.zeros(shape=(8,)),
                         class_vals=cl1model['class_vals'])
    else:
        return CCDCModel(start_day=chgmodel['start_day'],
                         end_day=chgmodel['end_day'],
                         break_day=chgmodel['break_day'],
                         obs_count=chgmodel['observation_count'],
                         change_prob=chgmodel['change_probability'],
                         curve_qa=chgmodel['curve_qa'],
                         bands=tuple(bands),
                         class_split=cl2model['start_day'],
                         class_probs1=np.array(cl1model['class_probs']),
                         class_probs2=np.array(cl2model['class_probs']),
                         class_vals=cl1model['class_vals'])


def unify(ccd: dict, classified: list) -> List[CCDCModel]:
    """
    Combine the two disparate models for a given pixel and make a list of unified models.

    Args:
        ccd: pyccd results for a pixel
        classified: test classification results for the pixel from a pickle file
    
    Returns:
        unified CCDC models
    """
    models = []
    # log.debug(len(classified))
    # log.debug(len(ccd['change_models']))
    for change in ccd['change_models']:
        found = False
        for cl1 in classified:
            # One for one
            if cl1['start_day'] == change['start_day'] and cl1['end_day'] == change['end_day']:
                models.append(buildccdc(change, cl1))
                found = True
                break

            # Looks like we have a twofer ...
            elif cl1['start_day'] == change['start_day']:
                for cl2 in classified:
                    if cl2['end_day'] == change['end_day']:
                        models.append(buildccdc(change, cl1, cl2))
                        found = True
                        break
                break

        # Looks like a segment that didn't fall on July 1st ... blah
        if found is False:
            models.append(buildccdc(change))

    return models


def spatialccd(jdata: list) -> list:
    """
    We can't really guarantee what order (pixel wise) the CCD data is in. This aligns it 
    in a way that makes sense spatially, which is good for output to rasters.

    Args:
        jdata: initial JSON deserialization of change results for a chip

    Returns:
        ndarray of dictionaries
    """
    outdata = np.full(fill_value=None, shape=(100, 100), dtype=object)

    if jdata is not None:
        chip_x, chip_y = (jdata[0]['chip_x'], jdata[0]['chip_y'])
        aff = buildaff(chip_x, chip_y, 30)
        for d in jdata:
            row, col = transform_geo(d['x'], d['y'], aff)

            try:
                result = d.get('result', 'null')
                outdata[row][col] = loadjstr(result)
            except:
                raise ValueError

    return list(outdata.flatten())
#
#
# def spatialcl(pdata: list) -> np.ndarray:
#     """
#     This is here more for consistency's sake. During classification, the change results are spatially
#     aligned, so these are already aligned as well ...
#
#     Args:
#         pdata: pickle deserialization of classification results for a chip
#
#     Returns:
#         ndarray of lists(of dictionaries)
#     """
#     return np.array(pdata).reshape(100, 100)


def spatialccdc(jdata: list, pdata: list) -> list:
    """
    Provide a unified CCDC model in a pseudo-spatial chip, as represented by a
    flattened list of lists.

    Args:
        jdata: initial JSON deserialization of change results for a chip
        pdata: pickle deserialization of classification results for a chip

    Returns:
        ndarray of lists(of CCDC namedtuples)
    """
    # cl = spatialcl(pdata).flatten()
    ccd = spatialccd(jdata)

    return [unify(c, cl1) for c, cl1 in zip(ccd, pdata)]


def validate(jpaths: list, ppaths: list) -> list:
    """

    """
    pass
