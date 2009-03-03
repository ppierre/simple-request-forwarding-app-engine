import unittest
import logging

from utils.webtest import TestApp
from utils.mocker import *

import main
from main import WSGIAppHandler

class DummyYamlOptions(dict):
  def reload(self):
    pass

class TestHelper(unittest.TestCase):
  """Setup a test application and mock forwarded request
  
  Subclass must provide config property
  """

  def mock_forward(self, status_code, **args):
    """set expected values for urlforward mock"""
    self.mock_fetch(KWARGS, **args)
    self.mocker.result(status_code)
    self.mocker.replay()
  
  def mock_not_forward(self):
    """disallow use of urlforward"""
    self.mock_fetch(KWARGS)
    self.mocker.throw("unhallowed call of urlforward")
    self.mocker.replay()
  
  def setUp(self):
    self.app = TestApp(WSGIAppHandler(self.config))
    
    self.mocker = Mocker()
    self.mock_fetch = self.mocker.mock()
    self.old_fetch = main.urlforward
    logging.info(self.old_fetch)
    main.urlforward = self.mock_fetch
  
  def tearDown(self):
    main.urlforward = self.old_fetch


class SimpleTest(TestHelper):
  """Basic test"""

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
  
  def test_ok_redirect(self):
    """Check forwarding of request"""
    self.mock_forward(200, url=CONTAINS("http://example.com/a_hooks.php"))
    response = self.app.get('/request_url')
    self.assertEqual('200 OK', response.status)
    self.assertTrue('Send at http://example.com/a_hooks.php' in response)
  
  def test_faill_redirect(self):
    """Check non forwarding of not configured URL"""
    self.mock_not_forward()
    response = self.app.get('/request_not_define_url', expect_errors=True)
    self.assertEqual('403 Forbidden', response.status)
