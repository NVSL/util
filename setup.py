from setuptools import setup, find_packages
import os
import sys
from codecs import open

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open(os.path.join(here, 'VERSION.txt'), encoding='utf-8') as f:
    version = f.read()

setup(name="gtron_util",
      version=version,
      long_description=long_description,
      author="NVSL, University of California San Diego",
      install_requires=["bs4", 'lxml==3.6.2', 'numpy', 'svgwrite'],
      packages = find_packages()
)
