#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(name='silverstrike',
	  version='0.1',
	  description='Python Accounting Webapp',
	  author='Simon Hanna',
	  url='https://github.com/agstrike/silverstrike',
	  packages=['silverstrike'],
	  include_package_data=True,
	  install_requires=[
          'django',
	  'django-widget-tweaks',
          'django-allauth',
          'python-dateutil',
    ])
