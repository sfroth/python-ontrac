#!/usr/bin/env python
from distutils.core import setup
import ontrac

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules'
]

KEYWORDS = 'ontrac api wrapper'

setup(name='ontrac',
      version=ontrac.VERSION,
      description='OnTrac Web Services API wrapper.',
      url='https://github.com/SideStudios/python-ontrac',
      packages=['ontrac'],
      package_dir={'ontrac': 'ontrac'},
      platforms=['Platform Independent'],
      license='BSD',
      classifiers=CLASSIFIERS,
      keywords=KEYWORDS,
      requires=['lxml'],
      install_requires=['lxml>=3.4.1'],
)
