from setuptools import setup, find_packages

setup(name='micropyGPS',
      version='1.0',
      description='GPS NMEA sentence parser',
      author='Calvin McCoy',
      author_email='calvin.mccoy@protonmail.com',
      url='https://github.com/inmcm/micropyGPS',
      py_modules=['micropyGPS'],
      include_package_data=True,
      test_suite="test_micropyGPS.py",
      )
