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

import unittest
from datetime import datetime

import logging
import secrets

from geopathfinder.eodatareaders import eoDRFilename, create_eodr_filename

logging.basicConfig(level=logging.INFO)


class TestSgrtFilename(unittest.TestCase):

    def setUp(self):
        self.id_1 = "123456"  # secrets.token_hex(nbytes=6)
        self.id_2 = "654321"  # secrets.token_hex(nbytes=6)
        self.dt_1 = datetime(2008, 1, 1, 12, 23, 33)
        self.dt_2 = datetime(2009, 2, 2, 22, 1, 1)

        fields_1 = {'id': self.id_1, 'dt_1': self.dt_1, 'band': 'B1'}

        self.eodr_fn_1 = eoDRFilename(fields_1)

        fields_2 = {'id': self.id_2, 'dt_1':  self.dt_1, 'dt_2': self.dt_2, 'band': 'B12', 'd1': '45'}

        self.eodr_fn_2 = eoDRFilename(fields_2)

    def test_build_eodr_filename(self):
        """
        Test building SGRT file name.

        """
        fn = ('123456_20080101T122333_---------------_B1.vrt')

        self.assertEqual(str(self.eodr_fn_1), fn)

    def test_get_n_set_date(self):
        """
        Test set and get start and end date.

        """
        self.assertEqual(self.eodr_fn_2['dt_1'].date(), self.dt_1.date())
        self.assertEqual(self.eodr_fn_2['dt_2'].date(), self.dt_2.date())

        new_start_time = datetime(2009, 1, 1, 12, 23, 33)
        self.eodr_fn_2['dt_1'] = new_start_time

        self.assertEqual(self.eodr_fn_2['dt_1'].date(), new_start_time.date())

    def test_create_eodr_filename(self):
        """
        Tests the creation of a SmartFilename from a given string filename.

        """

        # testing for single datetime
        fn = '123456_20181220T232333_---------------_B5_34_aug.vrt'
        should = create_eodr_filename(fn)

        self.assertEqual(should.get_field('id'), '123456')
        self.assertEqual(should.get_field('dt_1'), datetime(2018, 12, 20, 23, 23, 33))
        self.assertEqual(should.get_field('dt_2'), '')
        self.assertEqual(should.get_field('band'), 'B5')
        self.assertEqual(should.get_field('d1'), '34')
        self.assertEqual(should.get_field('d2'), 'aug')
        self.assertEqual(should.ext, '.vrt')


if __name__ == "__main__":
    unittest.main()
