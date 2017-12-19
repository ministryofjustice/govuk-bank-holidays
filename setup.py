# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import importlib
import os
import sys

from setuptools import setup

package_info = importlib.import_module('govuk_bank_holidays')
with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

install_requires = ['requests', 'six']
tests_require = ['flake8>=3.5,<4', 'responses']

if sys.version_info[0:2] < (3, 4):
    tests_require.append('mock')

setup_extensions = importlib.import_module('govuk_bank_holidays.setup_extensions')

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
    cmdclass=setup_extensions.command_classes,
    install_requires=install_requires,
    tests_require=tests_require,
    test_suite='tests',
)
