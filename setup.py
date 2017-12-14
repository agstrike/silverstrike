from os import path
import re
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

def get_version():
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(path.join(here, 'silverstrike', '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)

version = get_version()
long_description = """SilverStrike is a Django based webapp to help you
manage your personal finances.
"""

setup(
    name='silverstrike',
    version=version,
    description='Django webapp to manage personal finances',
    long_description=long_description,
    author='Simon Hanna',
    url='https://github.com/agstrike/silverstrike',
    license='MIT',
    packages=['silverstrike'],
    include_package_data=True,
    install_requires=[
        'django>=1.10,<2',
        'djangorestframework',
        'django-widget-tweaks',
        'django-allauth',
        'python-dateutil',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='finance django money money-manager',
    python_requires='>=3.4',
)

