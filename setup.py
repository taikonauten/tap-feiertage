#!/usr/bin/env python

from setuptools import setup

setup(name='tap-feiertage',
      version="2.0.7",
      description='Singer.io tap for extracting data from the feiertage api',
      author='Taikonauten GmbH & Co. KG',
      url='http://singer.io',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      py_modules=['tap_feiertage'],
      install_requires=[
          'singer-python==5.9.0',
          'requests==2.31.0',
          'pendulum==1.2.0',
          'backoff==1.8.0'
      ],
      entry_points='''
          [console_scripts]
          tap-feiertage=tap_feiertage:main
      ''',
      packages=['tap_feiertage'],
      package_data = {
          'tap_feiertage/schemas': [
              "holidays.json"
          ],
      },
      include_package_data=True,
)
