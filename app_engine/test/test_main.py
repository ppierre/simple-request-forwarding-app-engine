import unittest
import logging

import google.appengine.api.urlfetch

from utils.webtest import TestApp
from utils.mocker import *

from main import WSGIAppHandler

class DummyYamlOptions(dict):
  def reload(self):
    pass

class IndexTest(unittest.TestCase):

  def setUp(self):
    config = DummyYamlOptions({
        "/request_url": {
          'url': "/request_url",
          'methods': ["GET", "POST"],
          'forwards': [
            { 'url': "http://exemple.com/a_hooks.php",
              'method': "POST",
              'remove': [],
              'default': {},
              'set': {},
            },
          ]
        }
      })
    self.application = WSGIAppHandler(config)
    
    mocker = Mocker()
    mock_fetch = mocker.mock()
    self.old_fetch = google.appengine.api.urlfetch.fetch
    google.appengine.api.urlfetch.fetch = mock_fetch
    
    # mock result fetch ok
    result_fetch_ok = mocker.mock()
    result_fetch_ok.status_code
    mocker.result(200)
    mock_fetch(KWARGS, url="http://exemple.com/a_hooks.php")
    mocker.result(result_fetch_ok)
    
    mocker.replay()
  
  def test_ok_redirect(self):
    app = TestApp(self.application)
    response = app.get('/request_url')
    self.assertEqual('200 OK', response.status)
    self.assertTrue('Send at http://exemple.com/a_hooks.php' in response)
  
  def test_faill_redirect(self):
    app = TestApp(self.application)
    response = app.get('/request_not_define_url', status="403", expect_errors=True)
    self.assertEqual('403 Forbidden', response.status)
  
  def tearDown(self):
    google.appengine.api.urlfetch.fetch = self.old_fetch

