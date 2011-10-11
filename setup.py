import os
from distutils.core import setup

setup(
    name = "sumatra-server",
    version = "0.1.0",
    url = 'http://bitbucket.org/apdavison/sumatra_server/',
    download_url = 'https://bitbucket.org/apdavison/sumatra_server/downloads',
    license = "CeCILL v2 http://www.cecill.info",
    description = "Sumatra Server is a Django app that implements an HTTP-based store for records of computational experiments.",
    long_description = open("README.rst").read(),
    author = 'Andrew Davison',
    author_email = 'andrew.davison@unic.cnrs-gif.fr',
    packages = ['sumatra_server', 'sumatra_server.templatetags'],
    package_data = {'sumatra_server': ["templates/*.html", "fixtures/*.json"]},
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Science/Research',
        'License :: Other/Proprietary License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
