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
README = open(path.join(here, 'README.md')).read()

setup(
    name='silverstrike',
    version=version,
    description='Django webapp to manage personal finances',
    long_description=README,
    long_description_content_type="text/markdown",
    author='Simon Hanna',
    url='https://github.com/agstrike/silverstrike',
    license='MIT',
    packages=['silverstrike'],
    include_package_data=True,
    install_requires=[
        'django>=2.0,<3.0',
        'djangorestframework<3.8',
        'django-widgets-improved',
        'django-allauth',
        'python-dateutil',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
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

