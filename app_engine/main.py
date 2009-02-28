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

# ==============================================
# = Check local SDK or production environement =
# ==============================================

if os.environ.get('SERVER_SOFTWARE','').startswith('Devel'):
    HOST='local'
    logging.info('SDK environement, will reload config.yaml at each request')
elif os.environ.get('SERVER_SOFTWARE','').startswith('Goog'):
    HOST='google'
else:
    logging.error('Unknown server. Production/development?')


# ====================
# = Load config.yaml =
# ====================

def getConfig():
  config_dict = getConfigForFile('config.yaml')
  # merge test configuration when in SDK (local)
  if HOST == 'local':
    config_dict.update(getConfigForFile('config-test-local.yaml'))
  return config_dict

def getConfigForFile(config_file):
  config_path = os.path.join(os.path.dirname(__file__), config_file)
  config_list = yaml.safe_load(file(config_path))
  config_dict = {}
  # organise configuration by requested url
  for item in config_list:
    config_dict[item['url']] = item
  return config_dict

# Global variable for configuration parameters
global CONFIG
CONFIG = getConfig()

# ========================
# = Config default value =
# ========================

# Use config-default.yaml as template to fill option with default value
CONFIG_DEFAULT = getConfigForFile('config-default.yaml')['::dummy::']
logging.info(CONFIG_DEFAULT)

# ==========================================
# = MainHandler : match url against CONFIG =
# ==========================================

class MainHandler(webapp.RequestHandler):
  
  # Handel all request methods
  def do_request(self, request_url, request_method):
    
    # lookup config for url
    config_request = CONFIG.get(request_url)
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
    response_txt = ''
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
        response_txt += "Send at %s\n" % url
      else:
        # HTTP Error code :(
        response_txt += "Houps: %d for %s\n" % (status_code,url)
        # forward (last) error code to sender
        response_code = status_code
        logging.error(response_txt)
    
    # End of all forwarding
    
    # Send reponse to original request
    self.response.set_status(response_code)
    self.response.out.write(response_txt)
  
  # Redirect all resquest to the same handler
  # TODO: Maybe a way to take request before HTTP method dispatching
  
  def get(self, request_url):
    self.do_request(request_url, 'GET')
  
  def post(self, request_url):
    self.do_request(request_url, 'POST')
  
  def put(self, request_url):
    self.do_request(request_url, 'PUT')
  
  def delete(self, request_url):
    self.do_request(request_url, 'DELETE')

# Sub-Class of MainHandler, reload CONFIG at each request
# Used in local (SDK) environement

class LocalMainHandler(MainHandler):
  
  def do_request(self, request_url, request_method):
    # reload config at each request in SDK environement
    global CONFIG
    CONFIG = getConfig()
    MainHandler.do_request(self, request_url, request_method)


# ======================
# = Launch application =
# ======================

def main():
  
  # Test if in SDK (local) or is deployed (google)
  if HOST == 'local':
    Handler = LocalMainHandler
    debug = True
  elif HOST == 'google':
    Handler = MainHandler
    debug = False
  
  # launch Handler
  application = webapp.WSGIApplication([(r'(/.*)', Handler)], debug=debug)
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
