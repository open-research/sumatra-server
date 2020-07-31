import os
from distutils.core import setup

setup(
    name="sumatra-server",
    version="0.3.0",
    url="https://github.com/open-research/sumatra-server",
    download_url="https://pypi.org/project/sumatra-server/",
    license="BSD 2-clause",
    description="Sumatra Server is a Django app that implements an HTTP-based store for records of computational experiments.",
    long_description=open("README.rst").read(),
    author="Andrew Davison",
    author_email="andrew.davison@cnrs.fr",
    packages=["sumatra_server", "sumatra_server.templatetags", "sumatra_server.migrations"],
    package_data={"sumatra_server": ["templates/*.html", "fixtures/*.json"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
