Request forwarding on Google App Engine
=======================================

A simple application for forwarding request :

* Change HTTP method
* Set default parameters
* Filter request parameters
* Hide your secret :
  * Cloak forwarding URL
  * Choose request URL (long and/or cryptic)
  * Add HTTP basic authentication
  * Add additional parameters

__Disclaimer :__ Not really tested, __nor finished__ :(. I wrote this for a simple need : bypass a missing User-Agent and hide some password.

Installation
------------

You need [Google App Engine SDK](http://code.google.com/intl/fr/appengine/downloads.html)
* And read [documentation](http://code.google.com/intl/fr/appengine/docs/)

* Clone this repository
* copy `app_engine/app-sample.yaml` to `app_engine/app.yaml`
  * edit `app_engine/app.yaml` and change application id
* copy `app_engine/config-sample.yaml` to `app_engine/config.yaml`
  * edit `app_engine/config.yaml` (see Configuration)

Configuration
-------------

see `app_engine/config-sample.yaml`

_Need some documentation_

Usage
-----

### Test

    # Go to application directory and launch it with :
    dev_appserver.py app_engine

### Deployment

    # After testing it, deploy on Google App Engine
    appcfg.py update app_engine

See : [Uploading Your Application](http://code.google.com/intl/fr/appengine/docs/python/gettingstarted/uploading.html)

Far future :
------------

* Documentation
* Unit test
* Parameters transformation
  * XSLT ?
  * JSONT ?
  * other ...