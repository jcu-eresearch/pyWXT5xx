#!/usr/bin/env python
# pyWXT5xx parses and creates messages for the Vaisala WXT5xx series Weather Station.
# Copyright (C) 2016  NigelB
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from setuptools import setup, find_packages

setup(name='pyWXT5xx',
      version='0.0.1',
      description='pyWXT5xx parses and creates messages for the Vaisala WXT5xx series Weather Station.',
      author='NigelB',
      author_email='nigel.blair@gmail.com',
      packages=find_packages(),
      zip_safe=False,
      install_requires=["pyserial"],
      entry_points={
            "console_scripts": [
                  "wxt5 = wxt5xx.cli:main",
            ]
      }
      )