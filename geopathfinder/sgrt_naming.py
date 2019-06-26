# Copyright (c) 2018, Vienna University of Technology (TU Wien), Department
# of Geodesy and Geoinformation (GEO).
# All rights reserved.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL VIENNA UNIVERSITY OF TECHNOLOGY,
# DEPARTMENT OF GEODESY AND GEOINFORMATION BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
SGRT folder and file name definition.

"""

import os

from datetime import datetime
from collections import OrderedDict

from geopathfinder.folder_naming import SmartPath
from geopathfinder.file_naming import SmartFilename
from geopathfinder.folder_naming import build_smarttree
from geopathfinder.folder_naming import create_smartpath


# Please add here new sensors if they follow the SGRT naming convention.
allowed_sensor_dirs = ['Sentinel-1_CSAR',
                       'SCATSAR',
                       'METOP_ASCAT',
                       'Envisat_ASAR']

# TODO: add more data type checks
class SgrtFilename(SmartFilename):

    """
    SGRT file name definition using SmartFilename class.
    """

    def __init__(self, fields):

        self.date_format = "%Y%m%d"
        self.time_format = "%H%M%S"
        self.fields = fields.copy()

        if 'dtime_2' not in self.fields.keys():
            self.single_date = True
            apply_dtime_2 = False
        else:
            self.single_date = False
            apply_dtime_2 = True
            # if only daytime and no date is given
            if self.fields['dtime_2'].endswith('--'):
                dtime_2 = datetime.strptime(self.fields['dtime_2'][:-2], self.time_format)
            else:
                dtime_2 = datetime.strptime(self.fields['dtime_2'], self.date_format)

            if dtime_2.year < 1950:
                self.single_date = True

        fields_def = OrderedDict([
                     ('pflag', {'len': 1, 'delim': False}),
                     ('dtime_1', {'len': 8, 'delim': False,
                                  'decoder': lambda x: self.decode_date(x),
                                  'encoder': lambda x: self.encode_date(x)}),
                     ('dtime_2', {'len': 8, 'delim': True,
                                  'decoder': lambda x: self.decode_time(x),
                                  'encoder': lambda x: self.encode_time(x)}),
                     ('time', None),
                     ('var_name', {'len': 9, 'delim': True}),
                     ('mission_id', {'len': 2, 'delim': True}),
                     ('spacecraft_id', {'len': 1, 'delim': False}),
                     ('mode_id', {'len': 2, 'delim': False}),
                     ('product_type', {'len': 3, 'delim': False}),
                     ('res_class', {'len': 1, 'delim': False}),
                     ('level', {'len': 1, 'delim': False}),
                     ('pol', {'len': 2, 'delim': False}),
                     ('orbit_direction', {'len': 1, 'delim': False}),
                     ('relative_orbit', {'len': 3, 'delim': True,
                                         'decoder': lambda x: self.decode_rel_orbit(x),
                                         'encoder': lambda x: self.encode_rel_orbit(x)}),
                     ('workflow_id', {'len': 5, 'delim': True}),
                     ('grid_name', {'len': 6, 'delim': True}),
                     ('tile_name', {'len': 10, 'delim': True})
                    ])

        if 'dtime_1' in self.fields.keys():
            if self.single_date:
                date = self.fields['dtime_1']
                if apply_dtime_2:
                    time = self.fields['dtime_2']
                else:
                    time = self.fields['dtime_1']
                self.fields['dtime_1'] = date
                self.fields['dtime_2'] = time

        super(SgrtFilename, self).__init__(self.fields, fields_def, pad='-', ext='.tif')

    @property
    def stime(self):
        """start time"""
        return datetime.combine(self["dtime_1"], self["dtime_2"]) if self.single_date else self["dtime_1"]

    @property
    def etime(self):
        """end time"""
        return datetime.combine(self["dtime_1"], self["dtime_2"]) if self.single_date else self["dtime_2"]


    @property
    def product_id(self):
        try:
            product_id = "".join([self["mission_id"], self["spacecraft_id"],self["mode_id"],self["product_type"], self["res_class"]])
        except:
            product_id = None

        return product_id

    @property
    def ftile(self):
        try:
            ftile = "_".join([self["grid_name"], self["tile_name"]])
        except:
            ftile = None
        return ftile

    def decode_date(self, string):
        return datetime.strptime(string, self.date_format)

    def decode_time(self, string):
        if self.single_date:
            time_obj = datetime.time(datetime.strptime(string, self.time_format))
        else:
            time_obj = datetime.strptime(string, self.date_format)

        return time_obj

    def decode_rel_orbit(self, string):
        return int(string)

    def encode_date(self, time_obj):
        return time_obj.strftime(self.date_format)

    def encode_time(self, time_obj):
        if self.single_date:
            string = time_obj.strftime(self.time_format)
        else:
            string = time_obj.strftime(self.date_format)

        return string

    def encode_rel_orbit(self, orbit_num):
        return "{:03d}".format(orbit_num)

    def __getitem__(self, key):

        if key == "time":
            if self.single_date:
                return self.stime
            else:
                return self.stime + (self.etime - self.stime)/2  # if start and end time are given, take the mean
        else:
            return super(SgrtFilename, self).__getitem__(key)


def create_sgrt_filename(filename_string):
    """
    Creates a SgrtFilename() object from a given string filename

    Parameters
    ----------
    filename_string : str
        filename following the SGRT filename convention.
        e.g. 'M20170725_165004--_SIG0-----_S1BIWGRDH1VVA_146_A0104_EU500M_E048N012T6.tif'

    Returns
    -------
    SgrtFilename

    """

    helper = SgrtFilename({})
    filename_string = filename_string.replace(helper.ext, '')
    parts = filename_string.split(helper.delimiter)

    if not [len(x) for x in parts] == [9, 8, 9, 13, 3, 5, 6, 10]:
        raise ValueError('Given filename_string "{}" does not comply with '
                         'SGRT naming convention!')

    dtime_2_format = "%Y%m%d"
    if parts[1].endswith('--'):
        dtime_2_format = "%H%M%S--"

    fields = {
              'pflag': parts[0][0],
              'dtime_1': parts[0][1:],
              'dtime_2': parts[1],
              'time': None,
              'var_name': parts[2],
              'mission_id': parts[3][0:2],
              'spacecraft_id': parts[3][2:3],
              'mode_id': parts[3][3:5],
              'product_type': parts[3][5:8],
              'res_class': parts[3][8:9],
              'level': parts[3][9:10],
              'pol': parts[3][10:12],
              'orbit_direction': parts[3][12:13],
              'relative_orbit': parts[4],
              'workflow_id': parts[5],
              'grid_name': parts[6],
              'tile_name': parts[7]
             }

    return SgrtFilename(fields)


def sgrt_path(root, mode=None, group=None, datalog=None,
              product=None, wflow=None, grid=None, tile=None, var=None,
              qlook=True, make_dir=False):
    '''
    Realisation of the full SGRT folder naming convention, yielding a single
    SmartPath.

    Parameters
    ----------
    root : str
        root directory of the path. must contain satellite sensor at toplevel.
        e.g. "R:\Datapool_processed\Sentinel-1_CSAR"
    mode : str
        e.g "IWGRDH"
    group : str, optional
        "preprocessed" or "parameters" or "products"
    datalog : str, optional
        must be "datasets" or "logfiles"
    product : str
        e.g. "ssm"
    wflow : str
        e.g. "C1003"
    grid : str
        e.g. "EQUI7_EU500M"
    tile : str
        e.g. "E048N012T6"
    var : str
        e.g. "ssm"
    qlook : bool
        if the quicklook subdir should be integrated
    make_dir : bool
        if the directory should be created on the filesystem

    Returns
    -------
    SmartPath
        Object for the path
    '''

    # check the sensor folder name
    if root.split(os.sep)[-1] not in allowed_sensor_dirs:
        raise ValueError('Wrong input for "root"!')

    # define the datalog folder name
    if datalog is None:
        if isinstance(wflow, str):
            datalog = 'datasets'
    elif datalog == 'logfiles':
        product = None
        wflow = None
        grid = None
        tile = None
        var = None
        qlook = False
    elif datalog == 'datasets':
        pass
    else:
        raise ValueError('Wrong input for "datalog" level!')


    # define the group folder name
    if group is None:
        if wflow.startswith('A'):
            group = 'preprocessed'
        elif wflow.startswith('B'):
            group = 'parameters'
        elif wflow.startswith('C'):
            group = 'products'
        else:
            raise ValueError('Wrong input for "wflow" level!')


    # defining the folder levels
    levels = [mode, group,
              datalog, product, wflow, grid,
              tile,  var, 'qlooks']

    # defining the hierarchy
    hierarchy = ['mode', 'group',
                 'datalog', 'product', 'wflow', 'grid',
                 'tile', 'var', 'qlook']

    if qlook is False:
        levels.remove('qlooks')
        hierarchy.remove('qlook')

    return create_smartpath(root, hierarchy=hierarchy, levels=levels,
                     make_dir=make_dir)


def sgrt_tree(root, target_level=None, register_file_pattern=None):

    '''
    Realisation of the full SGRT folder naming convention, yielding a
    SmartTree(), reflecting all subfolders as SmartPath()

    Parameters
    ----------
    root : str
        top level directory of the SGRT dataset, which is the sensor name in
        the SGRT naming convention.
        E.g.: "R:\Datapool_processed\Sentinel-1_CSAR"
    target_level : str, optional
        Can speed up things: Level name of target tree-depth.
        The SmartTree is only built from directories reaching this level,
        and only built down to this level. If not set, all directories are
        built down to deepest depth.
    register_file_pattern : str tuple, optional
        strings defining search pattern for file search for file_register
        e.g. ('C1003', 'E048N012T6').
        No asterisk is needed ('*')!
        Sequence of strings in given tuple is crucial!
        Be careful: If the tree is large, this can take a while!

    Returns
    -------
    SmartTree
        Object for the SGRT tree.
    '''

    # defining the hierarchy
    hierarchy = ['mode', 'group','datalog',
                 'product', 'wflow', 'grid',
                 'tile', 'var', 'qlook']

    # Check for allowed directory topnames for "root".
    if root.split(os.sep)[-1] in allowed_sensor_dirs:
        sgrt_tree = build_smarttree(root, hierarchy,
                                    target_level=target_level,
                                    register_file_pattern=register_file_pattern)
    else:
        raise ValueError('Root-directory "{}" does is '
                         'not a valid SGRT folder!'.format(root))

    return sgrt_tree



if __name__ == '__main__':
    pass
