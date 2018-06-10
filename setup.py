# -*- coding: utf-8 -*-
#

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='actronquepy',
    version='0.0.1',
    description='A method for interfacing with Actron Que Air Conditioning',
    long_description=readme,
    author='Gambellator',
    author_email='andrew@gambell.io',
    url='https://github.com/Gambellator/actronquepy',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
