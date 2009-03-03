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
    self.app = TestApp(WSGIAppHandler(self.get_config()))
    
    self.mocker = Mocker()
    self.mock_fetch = self.mocker.mock()
    self.old_fetch = main.urlforward
    logging.info(self.old_fetch)
    main.urlforward = self.mock_fetch
  
  def tearDown(self):
    main.urlforward = self.old_fetch


class SimpleTestMixin:
  """Basic test Mixin to use with POST or GET"""

  config_mixin = DummyYamlOptions({
      "/request_url": {
        'url': "/request_url",
        'methods': ["GET", "POST"],
        'forwards': [
          { 'url': "http://example.com/a_hooks.php",
            'method': "GET",
            'remove': [],
            'default': {},
            'set': {},
          },
        ]
      }
    })
  
  def mock_a_hooks(self, status_code, **args):
    """set expected values for urlforward mock
    to http://example.com/a_hooks.php
    """
    self.mock_forward(status_code, url="http://example.com/a_hooks.php", 
                                   **args)
  
  def assert_a_hooks_ok(self, response):
    self.assertEqual('200 OK', response.status)
    self.assertTrue('Send at http://example.com/a_hooks.php' in response)
  
  def test_ok_redirect(self):
    """Check forwarding of request"""
    self.mock_a_hooks(200)
    self.assert_a_hooks_ok(self.app.get('/request_url'))
  
  def test_fail_redirect(self):
    """Check non forwarding of not configured URL"""
    self.mock_not_forward()
    response = self.app.get('/request_not_define_url', expect_errors=True)
    self.assertEqual('403 Forbidden', response.status)
  
  def test_absent_redirect(self):
    """Check forwarding of request to absent destination"""
    self.mock_a_hooks(404)
    response = self.app.get('/request_url', expect_errors=True)
    self.assertEqual('404 Not Found', response.status)
    self.assertTrue('Houps: 404 for http://example.com/a_hooks.php' in response)
  
  def test_unhallowed_method(self):
    """Check unhallowed request method"""
    self.mock_a_hooks(200)
    response = self.app.put('/request_url', expect_errors=True)
    self.assertEqual('405 Method Not Allowed', response.status)
  
  def test_passing_of_post_parameter(self):
    """Check forwarding of post request parameter"""
    self.mock_a_hooks(200, param=CONTAINS("foo"))
    self.assert_a_hooks_ok(self.app.post('/request_url', params={"foo":"bar"}))
  
  def test_passing_of_get_parameter(self):
    """Check forwarding of get request parameter"""
    self.mock_a_hooks(200, param=CONTAINS("foo"))
    self.assert_a_hooks_ok(self.app.get('/request_url', params={"foo":"bar"}))
  
  def test_value_of_post_parameter(self):
    """Check value of post request parameter"""
    self.mock_a_hooks(200, param={"foo":"bar"})
    self.assert_a_hooks_ok(self.app.post('/request_url', params={"foo":"bar"}))
  
  def test_value_of_get_parameter(self):
    """Check value of get request parameter"""
    self.mock_a_hooks(200, param={"foo":"bar"})
    self.assert_a_hooks_ok(self.app.get('/request_url', params={"foo":"bar"}))


class SimpleTestPOST(TestHelper, SimpleTestMixin):
  """Basic test HTTP method POST"""
  
  def get_config(self):
    config = SimpleTestMixin.config_mixin.copy()
    config["/request_url"]["forwards"][0]['method'] = 'POST'
    return config
  
  def test_forward_http_method_post(self):
    """Check use of HTTP POST method"""
    self.mock_a_hooks(200, method='POST')
    self.assert_a_hooks_ok(self.app.get('/request_url'))


class SimpleTestGET(TestHelper, SimpleTestMixin):
  """Basic test HTTP method GET"""
  
  def get_config(self):
    config = SimpleTestMixin.config_mixin.copy()
    config["/request_url"]["forwards"][0]['method'] = 'GET'
    return config
  
  def test_forward_http_method_get(self):
    """Check use of HTTP GET method"""
    self.mock_a_hooks(200,  method='GET')
    self.assert_a_hooks_ok(self.app.get('/request_url'))

  