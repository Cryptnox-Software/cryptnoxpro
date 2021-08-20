"""
Configuration for setting up CryptnoxCard CLI application
"""
import sys
from setuptools import setup

from cryptnoxcard.version import __version__

PYSCARD = "pyscard"
if sys.platform.startswith("win"):
    PYSCARD += "==2.0.1"

dependencies = [
    "aiohttp",
    "argparse",
    "appdirs",
    "base58",
    "ecdsa",
    "colander",
    "cryptnoxpy",
    "cryptography",
    "lazy-import",
    "pytz",
    PYSCARD,
    "requests",
    "tabulate",
    "stdiomask",
    "web3"
]

if sys.platform.startswith("win"):
    dependencies.append("winrt")

setup(name='cryptnoxcard',
      version=__version__,
      platforms=['any'],
      python_requires=">=3.6,<3.10",
      install_requires=dependencies,
      entry_points={
          'console_scripts': ['cryptnoxcard=cryptnoxcard.main:main'],
      }
      )
