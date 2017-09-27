# -*- coding: utf-8 -*-

__version__ = '1.3.1'
# $Source$

#Some commentary


from .mod1 import *
#import mod2
from . import mod3, mod4


def init_test():
    '''
    Only working when in WinPython root directory.

    Returns:
    maske, data0, data1, no_motion, motion
    '''
    maske = read_mask('./MRR/Testdaten/55_mask.bmp')
    display(maske)
    data0 = read_dicom_set('./MRR/Testdaten/188_13-12-10_56_1',
                               unwrap=True, mask=maske, verbose=False)
    data1 = read_dicom_set('./MRR/Testdaten/188_13-12-10_54_1',
                               unwrap=True, mask=maske, verbose=False)
    no_motion = mean(data0, axis=0)
    motion = mean(data1, axis=0)
    return maske , data0, data1, no_motion, motion