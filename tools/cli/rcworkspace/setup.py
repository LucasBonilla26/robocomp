from setuptools import setup, find_packages

setup(
    name='rcworkspace',
    version='0.0.1',
    include_package_data=True,
    packages=find_packages(),
    url='https://github.com/robocomp/robocomp/tree/development/tools/robocompdsl',
    license='GPL V3',
    author='Esteban Martinena',
    author_email='emartinena@unex.es',
    description='rcworkspace command line',
    entry_points={'console_scripts': ['rcworkspace = rcworkspace.main:app']}
)
