#!/usr/bin/env python

import logging
import urllib
import base64
import wsgiref.handlers
import yaml
import os
import sys

from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from utils.Chainmap import Chainmap
from utils import server

# ====================
# = Load config file =
# ====================

def get_config_from(config_file):
  """Read yaml file relative to script path
  
  Args:
    config_file: filename of yaml file
  
  Returns:
    a dict of config item indexed by URL
  """
  config_path = os.path.join(os.path.dirname(__file__), config_file)
  config_list = yaml.safe_load(file(config_path))
  config_dict = {}
  # organise configuration by requested url
  for item in config_list:
    config_dict[item['url']] = item
  return config_dict


# ========================
# = Config default value =
# ========================

# Use config-default.yaml as template to fill option with default value
CONFIG_DEFAULT = get_config_from('config-default.yaml')['::dummy::']
logging.info(CONFIG_DEFAULT)


# ==================
# = WSGIAppHandler =
# ==================

class WSGIAppHandler(object):
  """Run directly as a WSGI-compatible application.
  
  Take a list of yaml file name for configuration option
  """
  
  def __init__(self, yaml_list, debug=False):
    """Initializes with option from yaml files
    
    Args:
      yaml_list: list of configuration file first taking over last one
      debug: if true send stack trace to browser 
             and reload configuration a each request
    """
    self.__debug = debug
    self.__yaml_list = yaml_list
    self._init_config()
    
  def _init_config(self):
    """Load configuration from list of yaml files"""
    
    self.__config = {}
    for config_file in reversed(self.__yaml_list):
      self.__config.update(get_config_from(config_file))
    
  
  def __call__(self, environ, start_response):
    """Called by WSGI when a request comes in."""
    self.request = webapp.Request(environ)
    self.response = webapp.Response()
    
    try:
      self.do_request()
    except Exception, e:
      self.handle_exception(e, self.__debug)
    
    self.response.wsgi_write(start_response)
    return ['']
    
  # Handel all request methods
  def do_request(self):
    
    request_url = self.request.path
    request_method = self.request.method
    
    # lookup config for url
    config_request = self.__config.get(request_url)
    if not(config_request):
      # TODO: error message page not found
      self.response.set_status(403)
      return # exit : no config for this URL
    
    # Set defaults values
    logging.info(sys.path)
    config_request = Chainmap(config_request,CONFIG_DEFAULT)
    
    #validate request method
    logging.info(config_request['methods'])
    if request_method not in config_request['methods']:
      # TODO: error message 405
      self.response.set_status(405)
      return # exit : not allowed request methode
    
    # TODO filter on Request::remote_addr
    
    # TODO add HTTP basic authentification for incoming request
    
    # variable to collect response
    response_code = 200
    
    # Make all forwarding
    for config in config_request['forwards']:
      
      # Set default value
      config = Chainmap(config,CONFIG_DEFAULT['forwards'][0])
      logging.info(CONFIG_DEFAULT['forwards'][0])
      
      # get and filter param
      param = config['default']
      keys = set(self.request.arguments()) - set(config['remove'])
      if 'only' in config:
        keys = keys & set(config['only'])
      for key in keys:
        # TODO Request::get(key) / Request::get_all(key) ?
        param[key] = self.request.get(key)
      param.update(config['set'])
    
      # build forwarded request
      url = config['url']
      payload = urllib.urlencode(param)
      method = config['method']
    
      # handle payload (POST,PUT) or query parameters
      if method in ['POST', 'PUT']:
        fetch_param = {
          'url'     : url,
          'payload' : payload,
        }
      else:
        # TODO: A better way to build request param ?
        fetch_param = {
          'url'     : url + '?' + payload,
        }
      fetch_param['method'] = method
      
      # add Basic HTTP authentification if needed
      if 'user' in config and 'pass' in config:
        auth_string = 'Basic ' + \
          base64.encodestring(config['user']+':'+config['pass'])
        fetch_param['headers'] = { 'Authorization' : auth_string }

      # fetch forwarded request
      result = urlfetch.fetch(**fetch_param)
      status_code = result.status_code
      
      # TODO better message formating (or more usefull)
      if status_code == 200:
        # HTTP OK result :)
        self.response.out.write("Send at %s\n" % url)
      else:
        # HTTP Error code :(
        self.response.out.write("Houps: %d for %s\n" % (status_code, url))
        # forward (last) error code to sender
        response_code = status_code
        # TODO: factor login with response
        # logging.error(response_txt)
    
    # End of all forwarding
    
    # Send reponse to original request
    self.response.set_status(response_code)

# =======================
# = WSGIAppHandlerDebug =
# =======================

class WSGIAppHandlerDebug(WSGIAppHandler):
  """Used when running in SDK for reloading config at each request"""
  
  def __call__(self, environ, start_response):
    """Called by WSGI when a request comes in.
    Will reload config and call parent
    """
    self._init_config()
    WSGIAppHandler.__call__(self, environ, start_response)
  
# ======================
# = Launch application =
# ======================

# main WSGI application (WSGIAppHandler)
global application

def setup():
  """build and cache in global 'application' main WSGI application"""
  
  global application
  
  config_yaml = 'config.yaml'
  config_local_yaml = 'config-test-local.yaml'
  
  # Test if in SDK (local)
  if server.platform() == 'local':
    application = \
      WSGIAppHandlerDebug([config_local_yaml, config_yaml], debug=True)
  else:
    application = WSGIAppHandler([config_yaml])
  
def main():
  """launch main WSGI application"""
  
  global application
  run_wsgi_app(application)


if __name__ == '__main__':
  # buiild and cache
  setup()
  # launch
  main()
