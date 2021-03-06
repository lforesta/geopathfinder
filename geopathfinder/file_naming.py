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

import os
import copy
from collections import OrderedDict


class SmartFilenamePart(object):
    """ Represents a part of filename. """

    def __init__(self, arg, start=0, length=None, delimiter="_", pad="-", decoder=None, encoder=None):
        """
        Constructor of SmartFilenamePart class.

        Parameters
        ----------
        arg: object
            Input argument, which can be a string or the decoded part of the filename.
        start: int, optional
            Start index of filename part (default is 0).
        length: int, optional
            Length of filename part.
        delimiter : str, optional
            Delimiter (default: '_')
        pad : str, optional
            Padding symbol (default: '-').
        decoder: function, optional
            Decodes a certain value (str -> object).
        encoder: function, optional
            Encodes a certain value (object -> str).
        """

        self.arg = arg
        self.start = start
        self.delimiter = delimiter
        self.pad = pad
        self.decoder = (lambda x: x) if decoder is None else decoder
        self.encoder = (lambda x: x) if encoder is None else encoder
        self.length = length if length is not None else len(self.encoded)

        # check validity
        if not self.is_valid():
            err_msg = "Length does not comply with definition: {:} > {:}".format(len(self), self.length)
            raise ValueError(err_msg)

    def is_valid(self):
        """
        Checks if a SmartFilenamePart instance is valid.
        It is valid if the specified length is equal to the length of the SmartFilenamePart.

        Returns
        -------
        bool
            True if SmartFilenamePart instance is valid, else False.
        """

        return self.length == len(self)

    @property
    def encoded(self):
        """
        Converts filename part to an encoded (string) representation.

        Returns
        -------
        str
            Encoded (string) representation of a filename part.
        """

        return self.encoder(self.arg)

    @property
    def decoded(self):
        """
        Converts filename part to a decoded (object) representation.

        Returns
        -------
        object
            Decoded (object) representation of a filename part.
        """

        enc_wo_pad = self.encoded.strip(self.pad)
        if enc_wo_pad != '':
            return self.decoder(enc_wo_pad)
        else:
            return None

    def __repr__(self):
        """
        Returns the string representation of the class.

        Returns
        -------
        str
            String representation of the class.
        """

        return self.encoded.ljust(self.length, self.pad)

    def __len__(self):
        """
        Returns length of the filename part.

        Returns
        -------
        int
            Length of the filename part.
        """

        return len(str(self))

    def __add__(self, other):
        """
        Defines summation rule for two SmartFilenamePart/str instances.

        Parameters
        ----------
        other: SmartFilenamePart, str
            Second summand.

        Returns
        -------
        str
            Concatenated strings separated by a delimiter.
        """

        return str(self) + self.delimiter + str(other)


class SmartFilename(object):

    """
    SmartFilename class handles file names with pre-defined field names
    and field length.
    """

    def __init__(self, fields, fields_def, ext=None, pad='-', delimiter='_', convert=False):
        """
        Define name of fields, length, pad and delimiter symbol.

        Parameters
        ----------
        fields : dict
            Name of fields (keys) and (values).
        fields_def : OrderedDict
            Name of fields (keys) in right order and length (values). It must contain:
                - "len": int
                    Length of filename part (must be given).
                - "start": int, optional
                    Start index of filename part (default is 0).
                - "delim": str, optional
                    Delimiter between this and the following filename part (default is the one from the parent class).
                - "pad": str,
                    Padding for filename part (default is the one from the parent class).
        ext : str, optional
            File name extension (default: None).
        pad : str, optional
            Padding symbol (default: '-').
        delimiter : str, optional
            Delimiter (default: '_')
        convert: bool, optional
            If true, decoding is applied to parts of the filename, where such an operation is available (default is False).
        """
        self.ext = ext
        self.delimiter = delimiter
        self.pad = pad
        self.convert = convert
        self._fn_map = self.__build_map(fields, fields_def)
        self.obj = self.__init_filename_obj()

    @classmethod
    def from_filename(cls, filename_str, fields_def, pad="-", delimiter="_", convert=False):
        """
        Converts a filename given as a string into a SmartFilename class object.

        Parameters
        ----------
        filename_str : str
            Filename without any paths (e.g., "M20170725_test.tif").
        fields_def : OrderedDict
            Name of fields (keys) in right order and length (values). It must contain:
                - "len": int
                    Length of filename part (must be given).
                - "start": int, optional
                    Start index of filename part (default is 0).
                - "delim": str, optional
                    Delimiter between this and the following filename part (default is the one from the parent class).
                - "pad": str,
                    Padding for filename part (default is the one from the parent class).
        pad : str, optional
            Padding symbol (default: '-').
        delimiter : str, optional
            Delimiter (default: '_')
        convert: bool, optional
            If true, decoding is applied to parts of the filename, where such an operation is available (default is False).

        Returns
        -------
        SmartFilename
            Class representing a filename.
        """

        # get extensions from filename
        ext = os.path.splitext(filename_str)[1]

        fields = dict()
        start = 0
        for name, value in fields_def.items():
            # parse part of filename via start and end position
            if 'start' in value.keys() and 'len' in value.keys():
                start = value['start']
                length = value['len']
                fields[name] = filename_str[start:(start + length)]
            elif 'len' in value.keys():
                length = value['len']
                fields[name] = filename_str[start:(start + length)]
            else:
                length = 0

            start += length

            if 'delim' in value.keys():
                start += len(value['delim'])
            else:
                start += len(delimiter)

        if cls.__name__ == "SmartFilename":
            return cls(fields, fields_def, ext=ext, convert=convert, pad=pad, delimiter=delimiter)
        else:
            return cls(fields, ext=ext, convert=convert)

    def __init_filename_obj(self):
        """
        Initialises the class 'FilenameObj' to set all filename attributes as class variables.
        This enables an easier access to filename properties.

        Returns
        -------
        FilenameObj

        """

        class FilenameObj(object):
            def __init__(self):
                pass

        filename_obj = FilenameObj()
        for name, fn_part in self._fn_map.items():
            if self.convert:
                setattr(filename_obj, name, fn_part.decoded)
            else:
                setattr(filename_obj, name, fn_part.encoded)

        return filename_obj

    def __build_map(self, fields, fields_def):
        """
        Creates a dictionary/map between filename part names and SmartFilenamePart instances.

        Paramaters
        ----------
        fields : dict
            Name of fields (keys) and (values).
        fields_def : OrderedDict
            Name of fields (keys) in right order and length (values). It must contain:
                - "len": int
                    Length of filename part (must be given).
                - "start": int, optional
                    Start index of filename part (default is 0).
                - "delim": str, optional
                    Delimiter between this and the following filename part (default is the one from the parent class).
                - "pad": str,
                    Padding for filename part (default is the one from the parent class).

        Returns
        -------
        dict
            Contains SmartFilenamePart instances representing each part of the filename.
        """

        # check fields consistency
        for key in fields.keys():
            if key not in fields_def.keys():
                raise KeyError("Field name undefined: {:}".format(key))

        fn_map = OrderedDict()
        for name, keys in fields_def.items():
            if name not in fields:
                elem = ""
            else:
                elem = fields[name]

            if 'delim' not in keys:
                keys['delimiter'] = self.delimiter
            else:
                keys['delimiter'] = keys['delim']
                del keys['delim']
            if 'pad' not in keys:
                keys['pad'] = self.pad
            if 'len' in keys:
                keys['length'] = keys['len']
                del keys['len']
            smart_fn_part = SmartFilenamePart(elem, **keys)
            fn_map[name] = smart_fn_part

        return fn_map

    def _build_fn(self):
        """
        Build file name based on fields, padding and length.

        Returns
        -------
        filename : str
            Filled file name.

        """
        fn_parts = list(self._fn_map.values())
        filename = str(fn_parts[0])
        for i in range(1, len(fn_parts)):
            filename = filename[:-len(fn_parts[i-1])] + (fn_parts[i-1] + fn_parts[i])

        if self.ext is not None:
            filename += self.ext

        return filename

    def _get_field(self, name):
        """
        Returns the value of the field with a given key.

        Parameters
        ----------
        name : str
            Name of the field.

        Returns
        -------
        str, object
            Part of the filename associated with given key. Depending on the chosen flag 'convert', it is either a str
            (convert=False) or an object.
        """

        # check and reset the attribute of the object variable
        field_from_obj = self._fn_map[name].encoder(getattr(self.obj, name))
        if field_from_obj and (field_from_obj != self._fn_map[name].encoded):
            fn_part = copy.deepcopy(self._fn_map[name])
            fn_part.arg = field_from_obj
            if fn_part.is_valid():
                self._fn_map[name] = fn_part

        if self.convert:
            return self._fn_map[name].decoded
        else:
            return self._fn_map[name].encoded.strip(self._fn_map[name].pad)

    def __getitem__(self, name):
        """
        Returns the value of the field with a given key.

        Parameters
        ----------
        name : str
            Name of the field.

        Returns
        -------
        str, object
            Part of the filename associated with given key. Depending on the chosen flag 'convert', it is either a str
            (convert=False) or an object. If the key can't be found in the fields definition, the method tries to return
            a property of an inherited class.
        """

        if name in self._fn_map:
            return self._get_field(name)
        elif hasattr(self, name):
            return getattr(self, name)
        else:
            raise KeyError('"{}" is neither a class variable nor a file attribute.'.format(name))

    def __setitem__(self, name, value):
        """
        Sets the value of a filename field corresponding to the given key.

        Parameters
        ----------
        name : str
            Name of the field.
        value: object
            Value of the field.

        """

        if name in self._fn_map:
            fn_part = copy.deepcopy(self._fn_map[name])
            fn_part.arg = value
            if not fn_part.is_valid():
                err_msg = "Length does not comply with definition: {:} > {:}".format(len(fn_part.encoded),
                                                                                     fn_part.length)
                raise ValueError(err_msg)
            else:
                self._fn_map[name] = fn_part
                value = fn_part.encoded.replace(self.pad, '')
                if self.convert:
                    setattr(self.obj, name, fn_part.decoded)
                else:
                    setattr(self.obj, name, value)
        else:
            raise KeyError("Field name undefined: {:}".format(name))

    def __repr__(self):
        """
        Returns the string representation of the class.

        Returns
        -------
        str
            String representation of the class.
        """

        return self._build_fn()
