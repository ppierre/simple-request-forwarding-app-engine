import unittest
import logging

import utils.urlforward

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
              'method': "GET",
              'remove': [],
              'default': {},
              'set': {"truc":"Houps"},
            },
          ]
        }
      })
    self.application = WSGIAppHandler(config)
    
    mocker = Mocker()
    mock_fetch = mocker.mock()
    self.old_fetch = utils.urlforward.urlforward
    utils.urlforward.urlforward = mock_fetch
    
    # mock result fetch ok
    mock_fetch(KWARGS, url=CONTAINS("http://exemple.com/a_hooks.php"))
    mocker.result(200)
    
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
    utils.urlforward.urlforward = self.old_fetch

