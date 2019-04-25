#!/usr/bin/env python
"""
Install wagtailvideos using setuptools
"""
from setuptools import find_packages, setup

with open('README.rst', 'r') as f:
    readme = f.read()

setup(
    name='wagtail-videos',
    version='2.1.0',
    description="A wagtail module for uploading and displaying videos in various codecs.",
    long_description=readme,
    author='Takeflight',
    author_email='developers@takeflight.com.au',
    url='https://github.com/flytrap/wagtailvideos',

    install_requires=[
        'wagtail>=2.0',
        'Django>=1.11',
        'django-enumchoicefield==1.0.0',
    ],
    extras_require={
        'testing': [
            'mock==2.0.0'
        ]
    },
    zip_safe=False,
    license='BSD License',

    packages=find_packages(),

    include_package_data=True,
    package_data={},

    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
    ],
)
