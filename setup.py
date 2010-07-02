# -*- coding: utf-8 -*-
# Copyright (c) 2009 by Yaco Sistemas S.L.
# Contact info: Fidel Ramos Sañudo <framos@yaco.es>
#
# This file is part of boletin
#
# boletin is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# boletin is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with boletin.  If not, see <http://www.gnu.org/licenses/>.

import os
from setuptools import setup

from boletin import version


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name="boletin",
    version=version,
    author="Fidel Ramos Sañudo",
    author_email="framos@yaco.es",
    description="Newsletter generation and sending application for Django",
    long_description=(read('README')+'\n\n'+read('CHANGES')),
    license="LGPL v3",
    keywords="django newsletter",
    packages=['boletin'],
    url='https://tracpub.yaco.es/djangoapps/wiki/Boletin',
    zip_safe=False,
)
