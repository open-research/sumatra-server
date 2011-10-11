=========================
Welcome to Sumatra Server
=========================

Sumatra Server is a Django_ app that implements an HTTP-based store for
records of computational experiments (e.g. simulations, scripted analyses), with
the goal of supporting `reproducible research`_.

In particular, it implements the server-side counterpart to the
``HttpRecordStore`` client in Sumatra_.

It is based on the Piston_ framework.


Getting started
---------------

The following assumes that you already have a Django project to which you wish
to add a record store for computational experiments. If you don't, you can
download an `example project here`_.

You will need to have installed Sumatra Server, Sumatra, Piston and
django-tagging_. Add the following lines to the ``INSTALLED_APPS`` tuple in your
settings.py::

    'sumatra_server',
    'sumatra.web',
    'sumatra.recordstore.django_store',
    'tagging',
    
Your ``INSTALLED_APPS`` should also contain ``'django.contrib.auth'`` and
``'django.contrib.contenttypes'``.

Now decide where in your URL structure the record store will live and edit your
urls.py accordingly, e.g.::

    urlpatterns = patterns('',
        # other url mappings
        (r'^records/', include('sumatra_server.urls')),
    )

Now update your database by running syncdb::

    $ python manage.py syncdb
    Creating tables ...
    Creating table sumatra_server_projectpermission
    Creating table django_store_project
    Creating table django_store_executable
    Creating table django_store_dependency
    Creating table django_store_repository
    Creating table django_store_parameterset
    Creating table django_store_launchmode
    Creating table django_store_datastore
    Creating table django_store_platforminformation
    Creating table django_store_record_platforms
    Creating table django_store_record_dependencies
    Creating table django_store_record
    Creating table tagging_tag
    Creating table tagging_taggeditem

If you would like to load some test data to try it out, run::

    $ python manage.py loaddata haggling permissions
    
This will populate the record store with some simulation records, owned by a
user "testuser" with password "abc123".


API
---

Sumatra server implements a RESTful_ API, which returns either HTML or JSON,
depending on the Accept header in the HTTP request. Normally, if you access the
page through a web browser you should get the HTML version, while Sumatra or
compatible tools will receive the JSON version. You can also override the Accept
header by explicitly adding ``?format=html`` or ``?format=json`` to the end of
the URL.

.. list-table:: *Table showing the operations that can be performed on the record store*.
   :header-rows: 1
   
   * - URL
     - GET
     - POST
     - PUT
     - DELETE
   * - /
     - Return a list of projects
     - .
     - .
     - .
   * - /<project_name>/
     - Return a list of records for the given project. May add a querystring ``?tags=tag1,tag2`` to show only records that have one of the supplied tags
     - .
     - Create a new project and give the current user permission to access the project
     - .
   * - /<project_name>/permissions/
     - Return a list of users who can access this project
     - Give a user permission to access this project
     - .
     - .
   * - /<project_name>/<record_label>/
     - Return the record with the given label
     - .
     - Create or update a record with the given label
     - Delete the record with the given label
   * - /<project_name>/tagged/<tag>/
     - Return a list of records with the given tag (*not yet implemented*)
     - .
     - .
     - Delete all records having the given tag (*not yet implemented*)

JSON format
-----------

Here is an example of a simulation record encoded using JSON. This is the
format that must be used to PUT a new record into the store::

    {
        "user": "testuser",
        "project_id": "TestProject",
        "label": "20100709-154255", 
        "reason": "Simulation to test the HttpRecordStore with Sumatra Server",
        "outcome": "Eureka! Nobel prize here we come.", 
        "executable": {
            "path": "/usr/local/bin/python", 
            "version": "2.5.2", 
            "name": "Python", 
            "options": ""
        }, 
        "repository": {
            "url": "/Users/andrew/tmp/SumatraTest", 
            "type": "MercurialRepository"
        },
        "version": "396c2020ca50",
        "diff": "", 
        "main_file": "main.py", 
        "parameters": {
            "content": "seed = 65785 # seed for random number generator\ndistr = \"uniform\" # statistical distribution to draw values from \nn = 100 # number of values to draw", 
            "type": "SimpleParameterSet"
        }, 
        "launch_mode": {
            "type": "SerialLaunchMode", 
            "parameters": "{}"
        }, 
        "timestamp": "2010-07-09 15:42:55", 
        "duration": 0.58756184577941895, 
        "datastore": {
            "type": "FileSystemDataStore", 
            "parameters": "{'root': '/Users/andrew/tmp/SumatraTest/Data'}"
        }, 
        "output_data": [
            {
                "path": "output.dat",
                "digest": 'a39100d5130f613b96c9fcf605b68d53d60f6fdb',
                "metadata": "",
            } for key in record.output_data],
        "input_datastore": {
            "type": "FileSystemDataStore", ,
            "parameters": "{'root': '/'}",
        },
        "input_data": [],
        "dependencies": [
            {
                "path": "/Library/Frameworks/Python.framework/Versions/4.0.30002/lib/python2.5/site-packages/matplotlib-0.98.3.0001-py2.5-macosx-10.3-fat.egg/matplotlib", 
                "version": "0.98.3", 
                "name": "matplotlib", 
                "module": "python", 
                "diff": ""
            }, 
            {
                "path": "/Library/Frameworks/Python.framework/Versions/4.0.30002/lib/python2.5/site-packages/numpy-1.1.1.0001-py2.5-macosx-10.3-fat.egg/numpy", 
                "version": "1.1.1", 
                "name": "numpy", 
                "module": "python", 
                "diff": ""
            }, 
        ],
        "platforms": [
            {
                "system_name": "Darwin", 
                "ip_addr": "127.0.0.1", 
                "architecture_bits": "32bit", 
                "machine": "i386", 
                "architecture_linkage": "", 
                "version": "Darwin Kernel Version 9.8.0: Wed Jul 15 16:55:01 PDT 2009; root:xnu-1228.15.4~1/RELEASE_I386", 
                "release": "9.8.0", 
                "network_name": "localhost", 
                "processor": "i386"
            }
        ],
        "tags": ""
    }

Most of these fields are write-once, i.e. if you PUT another record to the same
URL, only changes in "reason", "outcome" and "tags" will be taken into account.


Authentication
--------------

Sumatra Server uses HTTP Basic authentication, and validates against the user
database of your Django project.


.. _Django: http://www.djangoproject.com
.. _Sumatra: http://neuralensemble.org/sumatra
.. _`reproducible research`: http://reproducibleresearch.net/
.. _Piston: https://bitbucket.org/jespern/django-piston/
.. _`example project here`: https://bitbucket.org/apdavison/sumatra_server_example
.. _`django-tagging`: http://code.google.com/p/django-tagging/
.. _`RESTful`: http://en.wikipedia.org/wiki/Representational_State_Transfer