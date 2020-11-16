from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='tom-ephemeris',
    version='0.1.0',
    description='Tom Toolkit module to observe moving objects with custom, user-provided ephemerides.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/fraserw/tom_ephemeris',
    author='Wes Fraser',
    author_email='westhefras@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Physics'
    ],
    keywords=['tomtoolkit', 'astronomy', 'planetary-science', 'moving-object-data-analysis', 'observatory'],
    packages=find_packages(),
    install_requires=[
        'tomtoolkit',
        'tom_nonsidereal_airmass',
        'pyephem'
    ],
    include_package_data=True,
)
