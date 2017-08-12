#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(name='PyAccountant',
	  version='0.1',
	  description='Python Accounting Webapp',
	  author='Simon Hanna',
	  url='https://github.com/PyAccountant/PyAccountant',
	  packages=['pyaccountant',],
	  include_package_data=True,
	  install_requires=[
	  	'Django',
	  	'django-widget-tweaks',
        'django-allauth',
        'python-dateutil',
        ])
