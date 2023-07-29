#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=8.1.6', 'click_log>=0.4.0', 'pycryptodome>=3.18.0', 'requests>=2.25.1', 'zeroconf>=0.71.4']
setup_requirements = []
test_requirements = ['pytest', 'tox', 'python-coveralls', 'flask', 'flake8']

PROJECT_URLS = {
    "Bug Reports": "https://github.com/sarusani/pysonofflan/issues/",
    "Itead Dev Docs": "https://github.com/itead/Sonoff_Devices_DIY_Tools/tree/master/other/"
}

setup(
    author="Sarusani",
    author_email='sarusani@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Home Automation'
    ],
    description="Interface for Sonoff devices running v3+ Itead "
                "firmware.",
    entry_points={
        'console_scripts': [
            'pysonofflanr3=pysonofflanr3.cli:cli',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='pysonofflanr3, homeassistant',
    name='pysonofflanr3',
    packages=find_packages(include=['pysonofflanr3']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/sarusani/pysonofflan',
    project_urls=PROJECT_URLS,
    version='1.1.5',
    zip_safe=False,
)
