"""
Configuration for setting up Cryptnox CLI application
"""
import pathlib

from setuptools import setup


def read(file):
    return (pathlib.Path(__file__).parent / file).read_text("utf-8").strip()


setup(
    long_description="\n\n".join((read("README.md"), read("CHANGELOG.rst"))),
)
