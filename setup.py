#!/usr/bin/env python
import importlib
import os
import sys
import warnings

from setuptools import setup

if sys.version_info[0:2] < (3, 7):
    warnings.warn('This package is only tested on Python version 3.7+')

root_path = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(root_path, 'README.rst')) as readme:
    README = readme.read()

package_info = importlib.import_module('govuk_bank_holidays')
setup_extensions = importlib.import_module('govuk_bank_holidays.setup_extensions')

setup(
    name='govuk-bank-holidays',
    version=package_info.__version__,
    author=package_info.__author__,
    author_email='dev@digital.justice.gov.uk',
    url='https://github.com/ministryofjustice/govuk-bank-holidays',
    packages=[
        'govuk_bank_holidays',
        'govuk_bank_holidays.locale.cy.LC_MESSAGES',
        'govuk_bank_holidays.locale.en.LC_MESSAGES',
    ],
    include_package_data=True,
    license='MIT',
    description='Tool to load UK bank holidays from GOV.UK',
    long_description=README,
    keywords='bank holidays govuk uk',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    cmdclass=setup_extensions.command_classes,
    python_requires='>=3.6',  # looser requirement than what's tested
    install_requires=['requests'],
    tests_require=['responses'],
    test_suite='tests',
)
