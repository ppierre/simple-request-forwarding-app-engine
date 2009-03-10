#!/usr/bin/env python
# encoding: utf-8
"""
urlforward.py

Created by pierre pracht on 2009-03-03.
Copyright (c) 2009 __pierreTM__. All rights reserved.
"""

import urllib
import base64

# TDOD: add test using urlforward

from google.appengine.api import urlfetch


def urlforward(url=None,
               param={},
               method="GET",
               headers={},
               follow_redirects=True,
               login=None,
               password=None):
    """Warper around urlfetch.fetch :
     - Add HTTP Basic authentication
         both login and password must be set
     - Unify GET an POST handling
         take a param mapping who is used accordingly of HTTP method
     - Only return status_code

    Args:
        url: http or https URL
        param:
        method: HTTP method "GET" by default
        headers: mapping of HTTP headers {'name': "value"}
        follow_redirects: Allow follow of HTTP redirect, default to True
        login: name used for HTTP Basic authentication
        password: password used for HTTP Basic authentication

    Returns:
     status_code of forwarded request
    """
    fetch_param = {'url': url,
                   'method': method,
                   'headers': headers,
                   'follow_redirects': follow_redirects}
    if param:
        payload = urllib.urlencode(param)
        if method in ['POST', 'PUT']:
            fetch_param['payload'] = payload
        else:
            fetch_param['url'] = url + '?' + payload

    if login and password:
        fetch_param['headers']['Authorization'] = 'Basic ' + \
            base64.encodestring('%s:%s' % (login, password))

    # TODO: need to return more than status code ?
    result = urlfetch.fetch(**fetch_param)
    return result.status_code
