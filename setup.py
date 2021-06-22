#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('./docs/overview.rst') as readme_file:
    readme = readme_file.read()

requirements = []

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', ]


setup(
    author="Lyle Barner",
    author_email='lyle.barner@jpl.nasa.gov',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
    ],
    entry_points={
        'console_scripts': [
            'scrub=scrub.scrub_cli:main',
        ],
    },
    description="SCRUB is an orchestration and aggregation tool for static code analysis tools.",
    install_requires=requirements,
    long_description=readme,
    include_package_data=True,
    keywords='scrub',
    name='scrub',
    packages=find_packages(include=['scrub', 'scrub.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/nasa/scrub',
    version='2.4.0',
    zip_safe=False,
)
