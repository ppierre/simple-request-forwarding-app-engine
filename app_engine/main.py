#!/usr/bin/env python

import logging
import urllib
import base64
import wsgiref.handlers
import os
import sys
import cgi
import traceback

import webob

from google.appengine.ext.webapp.util import run_wsgi_app

from utils.Chainmap import Chainmap
from utils.yamloptions import YamlOptions
from utils.urlforward import urlforward
from utils import server


# ==================
# = WSGIAppHandler =
# ==================

class WSGIAppHandler(object):
  """Run directly as a WSGI-compatible application.
  
  Take a config object for configuration option
  """
  
  def __init__(self, config, debug=False):
    """Initializes with option from yaml files loaded in a YamlOptions object
    
    Args:
      config: YamlOptions instance
      debug: if true send stack trace to browser 
             and reload configuration a each request
    """
    self.__debug = debug
    self._config = config
    
  
  def __call__(self, environ, start_response):
    """Called by WSGI when a request comes in."""
    self.request = webob.Request(environ)
    self.response = webob.Response()
        
    # put request config option in request Ad-Hoc Attributes
    self.request.config = self._config
    
    try:
      self.do_request()
    except Exception, e:
      self.handle_exception(e, self.__debug)
    
    return self.response(environ, start_response)
    
  # Handel all request methods
  def do_request(self):
    
    request_url = self.request.path
    request_method = self.request.method
    
    if request_url not in self.request.config:
      # TODO: error message page not found
      self.response.status = 403
      return # exit : no config for this URL
    
    # lookup config for url
    config_request = self.request.config[request_url]
    
    #validate request method
    if request_method not in config_request['methods']:
      # TODO: error message 405
      self.response.status = 405
      return # exit : not allowed request methode
    
    # TODO filter on Request::remote_addr
    
    # TODO add HTTP basic authentification for incoming request
    
    # variable to collect response
    response_code = 200
    
    # Make all forwarding
    for config in config_request['forwards']:
      
      # get and filter param
      param = config['default']
      keys = set(self.request.params.keys()) - set(config['remove'])
      if 'only' in config:
        keys = keys & set(config['only'])
      for key in keys:
        # TODO Request::get(key) / Request::get_all(key) ?
        param[key] = self.request.params.get(key)
      param.update(config['set'])
      
      # build forwarded request
      fetch_opt = ["url", 
                   "method", 
                   "headers", 
                   "follow_redirects", 
                   "login", 
                   "password"]
      
      fetch_param = dict([(k,config[k]) for k in fetch_opt if k in config])
      
      status_code = urlforward(param=param, **fetch_param)
      
      # TODO better message formating (or more usefull)
      if status_code == 200:
        # HTTP OK result :)
        self.response.body += "Send at %s\n" % config["url"]
      else:
        # HTTP Error code :(
        self.response.body  += "Houps: %d for %s\n" % \
                                  (status_code, config["url"])
        # forward (last) error code to sender
        response_code = status_code
        # TODO: factor login with response
        # logging.error(response_txt)
    
    # End of all forwarding
    
    # Send reponse to original request
    self.response.status = response_code
  
  def handle_exception(self, exception, debug_mode):
    """Called if this handler throws an exception during execution.

    The default behavior is to call self.error(500) and print a stack trace
    if debug_mode is True.

    Args:
      exception: the exception that was thrown
      debug_mode: True if the web application is running in debug mode
    """
    self.response.status = 500
    logging.exception(exception)
    if debug_mode:
      lines = ''.join(traceback.format_exception(*sys.exc_info()))
      self.response.body = '<pre>%s</pre>' % (cgi.escape(lines, quote=True))

# =======================
# = WSGIAppHandlerDebug =
# =======================

class WSGIAppHandlerDebug(WSGIAppHandler):
  """Used when running in SDK for reloading config at each request"""
  
  def __call__(self, environ, start_response):
    """Called by WSGI when a request comes in.
    Will reload config and call parent
    """
    self._config.reload()
    return WSGIAppHandler.__call__(self, environ, start_response)
  
# ======================
# = Launch application =
# ======================

# main WSGI application (WSGIAppHandler)
global application

def setup():
  """build and cache in global 'application' main WSGI application"""
  
  yaml_list = ['config.yaml']
  if server.platform() == 'local': 
    yaml_list.insert(0, 'config-test-local.yaml')
  
  yaml_default = 'config-default.yaml'
  
  basedir = os.path.dirname(__file__)
  config = YamlOptions(yaml_list, yaml_default, basedir)
  
  global application
  
  # Test if in SDK (local)
  if server.platform() == 'local':
    application = WSGIAppHandlerDebug(config, debug=True)
  else:
    application = WSGIAppHandler(config)
  
  

def main():
  """launch main WSGI application"""
  
  global application
  run_wsgi_app(application)


if __name__ == '__main__':
  # buiild and cache
  setup()
  # launch
  main()
