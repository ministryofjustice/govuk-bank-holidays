# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import importlib
import os
import sys

from setuptools import setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

package_info = importlib.import_module('govuk_bank_holidays')
with open('README.rst') as readme:
    README = readme.read()

install_requires = ['requests', 'six']
tests_require = ['flake8', 'responses']
if sys.version_info[0:2] < (3, 4):
    tests_require.append('mock')

setup(
    name='govuk-bank-holidays',
    version=package_info.__version__,
    author=package_info.__author__,
    url='https://github.com/ministryofjustice/govuk-bank-holidays',
    packages=['govuk_bank_holidays'],
    include_package_data=True,
    license='MIT',
    description='Tool to load UK bank holidays from GOV.UK',
    long_description=README,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=install_requires,
    tests_require=tests_require,
    test_suite='tests',
)
