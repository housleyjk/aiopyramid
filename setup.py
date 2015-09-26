import os
import sys
from setuptools import setup, find_packages

py_version = sys.version_info[:2]
if py_version < (3, 3):
    raise Exception("aiopyramid requires Python >= 3.3.")

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst')) as readme:
    README = readme.read()
with open(os.path.join(here, 'CHANGES.rst')) as changes:
    CHANGES = changes.read()


requires = [
    'pyramid',
    'greenlet',
]

if py_version < (3, 4):
    requires.append('asyncio')

setup(
    name='aiopyramid',
    version='0.3.2',
    description='Tools for running pyramid using asyncio.',
    long_description=README + '\n\n\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Intended Audience :: Developers",
        "License :: Repoze Public License",
    ],
    author='Jason Housley',
    author_email='housleyjk@gmail.com',
    url='https://github.com/housleyjk/aiopyramid',
    keywords='pyramid asyncio greenlet wsgi',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    extras_require={
        'gunicorn': ['gunicorn>=19.1.1', 'aiohttp', 'websockets'],
    },
    license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
    entry_points="""\
    [pyramid.scaffold]
    aio_starter=aiopyramid.scaffolds:AioStarterTemplate
    aio_websocket=aiopyramid.scaffolds:AioWebsocketTemplate
    """
)
