import unittest
import logging

from utils.webtest import TestApp
from utils.mocker import *

import main
from main import WSGIAppHandler

class DummyYamlOptions(dict):
  def reload(self):
    pass

class IndexTest(unittest.TestCase):

  def mock_forward(self, status_code, **args):
    """set expected values for urlforward mock"""
    self.mock_fetch(KWARGS, **args)
    self.mocker.result(status_code)
    self.mocker.replay()
  
  def setUp(self):
    config = DummyYamlOptions({
        "/request_url": {
          'url': "/request_url",
          'methods': ["GET", "POST"],
          'forwards': [
            { 'url': "http://example.com/a_hooks.php",
              'method': "GET",
              'remove': [],
              'default': {},
              'set': {"truc":"Houps"},
            },
          ]
        }
      })
    self.application = WSGIAppHandler(config)
    
    self.mocker = Mocker()
    self.mock_fetch = self.mocker.mock()
    self.old_fetch = main.urlforward
    logging.info(self.old_fetch)
    main.urlforward = self.mock_fetch
  
  def test_ok_redirect(self):
    app = TestApp(self.application)
    self.mock_forward(200, url=CONTAINS("http://example.com/a_hooks.php"))
    response = app.get('/request_url')
    self.assertEqual('200 OK', response.status)
    self.assertTrue('Send at http://example.com/a_hooks.php' in response)
  
  def test_faill_redirect(self):
    app = TestApp(self.application)
    response = app.get('/request_not_define_url', status="403", expect_errors=True)
    self.assertEqual('403 Forbidden', response.status)
  
  def tearDown(self):
    main.urlforward = self.old_fetch

