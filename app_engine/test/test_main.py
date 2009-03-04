import unittest

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
    main.urlforward = self.mock_fetch
  
  def tearDown(self):
    main.urlforward = self.old_fetch


class TestMixin:

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
  
  def assert_a_hooks_get_ok(self, **args):
    response = self.app.get('/request_url', **args)
    self.assertEqual('200 OK', response.status)
    self.assertTrue('Send at http://example.com/a_hooks.php' in response)


class SimpleTestMixin(TestMixin):
  """Basic test Mixin to use with POST or GET"""

  def test_ok_redirect(self):
    """Check forwarding of request"""
    self.mock_a_hooks(200)
    self.assert_a_hooks_get_ok()
  
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
    self.assert_a_hooks_get_ok(params={"foo":"bar"})
  
  def test_value_of_post_parameter(self):
    """Check value of post request parameter"""
    self.mock_a_hooks(200, param={"foo":"bar"})
    self.assert_a_hooks_ok(self.app.post('/request_url', params={"foo":"bar"}))
  
  def test_value_of_get_parameter(self):
    """Check value of get request parameter"""
    self.mock_a_hooks(200, param={"foo":"bar"})
    self.assert_a_hooks_get_ok(params={"foo":"bar"})


class SimpleTestPOST(TestHelper, SimpleTestMixin):
  """Basic test HTTP method POST"""
  
  def get_config(self):
    config = TestMixin.config_mixin.copy()
    config["/request_url"]["forwards"][0]['method'] = 'POST'
    return config
  
  def test_forward_http_method_post(self):
    """Check use of HTTP POST method"""
    self.mock_a_hooks(200, method='POST')
    self.assert_a_hooks_get_ok()


class SimpleTestGET(TestHelper, SimpleTestMixin):
  """Basic test HTTP method GET"""
  
  def get_config(self):
    config = TestMixin.config_mixin.copy()
    config["/request_url"]["forwards"][0]['method'] = 'GET'
    return config
  
  def test_forward_http_method_get(self):
    """Check use of HTTP GET method"""
    self.mock_a_hooks(200,  method='GET')
    self.assert_a_hooks_get_ok()


class SimpleTestRemoveParam(TestHelper, TestMixin):
  """Test of removing request parameter"""
  
  def get_config(self):
    config = TestMixin.config_mixin.copy()
    config["/request_url"]["forwards"][0]['remove'] = ['sup1','sup2','sup3']
    return config
  
  def test_forward_existing_param(self):
    """Check that existing param are forwarded if not in remove list"""
    self.mock_a_hooks(200,  param={"pass1":"val_pass1"})
    self.assert_a_hooks_get_ok(params={"pass1":"val_pass1"})
  
  def test_suppress_existing_param(self):
    """Check that param are suppressed if in remove list"""
    self.mock_a_hooks(200,  param={})
    self.assert_a_hooks_get_ok(params={"sup1":"val_sup1"})
  
  def test_suppress_and_forward_existing_param(self):
    """Check that existing param are forwarded if not in remove list
    And Check that param are suppressed if in remove list
    """
    self.mock_a_hooks(200, param={"pass1":"val_pass1"})
    self.assert_a_hooks_get_ok(params={"pass1":"val_pass1", 
                                       "sup1":"val_sup1"})
  
  def test_suppress_and_forward_existing_param_multi(self):
    """Check that existing param are forwarded if not in remove list
    And Check that param are suppressed if in remove list
    With multiple keys
    """
    self.mock_a_hooks(200, param={"pass1":"val_pass1", 
                                  "pass2":"val_pass2"})
    self.assert_a_hooks_get_ok(params={"pass1":"val_pass1", 
                                       "pass2":"val_pass2", 
                                       "sup1":"val_sup1", 
                                       "sup3":"val_sup3"})


class SimpleTestOnlyParam(TestHelper, TestMixin):
  """Test of filtering request parameter"""
  
  def get_config(self):
    config = TestMixin.config_mixin.copy()
    config["/request_url"]["forwards"][0]['only'] = ['only1','only2','only3']
    return config
  
  def test_forward_existing_param(self):
    """Check that existing param are suppressed if not in only list"""
    self.mock_a_hooks(200, param={})
    self.assert_a_hooks_get_ok(params={"pass1":"val_pass1"})
  
  def test_suppress_existing_param(self):
    """Check that param are forwarded if in only list"""
    self.mock_a_hooks(200, param={"only1":"val_only1"})
    self.assert_a_hooks_get_ok(params={"only1":"val_only1"})
  
  def test_suppress_and_forward_existing_param(self):
    """Check that existing param are suppressed if not in only list
    And Check that param are forwarded if in only list
    """
    self.mock_a_hooks(200, param={"only1":"val_only1"})
    self.assert_a_hooks_get_ok(params={"pass1":"val_pass1", 
                                       "only1":"val_only1"})
  
  def test_suppress_and_forward_existing_param_multi(self):
    """Check that existing param are suppressed if not in only list
    And Check that param are forwarded if in only list
    With multiple keys
    """
    self.mock_a_hooks(200, param={"only1":"val_only1", 
                                  "only2":"val_only2"})
    self.assert_a_hooks_get_ok(params={"pass1":"val_pass1", 
                                       "only2":"val_only2", 
                                       "only1":"val_only1", 
                                       "pass3":"val_pass3"})


class SimpleTestDefaultParam(TestHelper, TestMixin):
  """Test of setting default value for request parameter"""
  
  def get_config(self):
    config = TestMixin.config_mixin.copy()
    config["/request_url"]["forwards"][0]['default'] = {"def1":"val_def1", 
                                                        "def2":"val_def2"}
    return config
  
  def test_default_param(self):
    """Check that default param are present even if not in request"""
    self.mock_a_hooks(200, param={"def1":"val_def1", 
                                  "def2":"val_def2"})
    self.assert_a_hooks_get_ok(params={})
  
  def test_forward_existing_param_and_default(self):
    """Check that param are forwarded even if not existing in default"""
    self.mock_a_hooks(200, param={"pass1":"val_pass1", 
                                  "def1":"val_def1", 
                                  "def2":"val_def2"})
    self.assert_a_hooks_get_ok(params={"pass1":"val_pass1"})
  
  def test_request_over_default(self):
    """Check that request param take over default value"""
    self.mock_a_hooks(200, param={"def1":"new_val_def1", 
                                  "def2":"val_def2"})
    self.assert_a_hooks_get_ok(params={"def1":"new_val_def1"})
  
  def test_forward_and_over_default(self):
    """Check that request param take over default value
    And that param are forwarded even if not existing in default
    """
    self.mock_a_hooks(200, param={"pass1":"val_pass1", 
                                  "def1":"new_val_def1", 
                                  "def2":"val_def2"})
    self.assert_a_hooks_get_ok(params={"pass1":"val_pass1", 
                                       "def1":"new_val_def1"})


class SimpleTestSetParam(TestHelper, TestMixin):
  """Test of forced value for request parameter"""
  
  def get_config(self):
    config = TestMixin.config_mixin.copy()
    config["/request_url"]["forwards"][0]['set'] = {"set1":"val_set1", 
                                                    "set2":"val_set2"}
    return config
  
  def test_default_param(self):
    """Check that fixed param are present even if not in request"""
    self.mock_a_hooks(200, param={"set1":"val_set1", 
                                  "set2":"val_set2"})
    self.assert_a_hooks_get_ok(params={})
  
  def test_forward_existing_param_and_default(self):
    """Check that param are forwarded even if not fixed"""
    self.mock_a_hooks(200, param={"pass1":"val_pass1", 
                                  "set1":"val_set1", 
                                  "set2":"val_set2"})
    self.assert_a_hooks_get_ok(params={"pass1":"val_pass1"})
  
  def test_request_over_default(self):
    """Check that request param don't take over fixed value"""
    self.mock_a_hooks(200, param={"set1":"val_set1", 
                                  "set2":"val_set2"})
    self.assert_a_hooks_get_ok(params={"set1":"new_val_set1"})
  
  def test_forward_and_over_default(self):
    """Check that request param don't take over fixed value
    And that param are forwarded even if not fixed
    """
    self.mock_a_hooks(200, param={"pass1":"val_pass1", 
                                  "set1":"val_set1", 
                                  "set2":"val_set2"})
    self.assert_a_hooks_get_ok(params={"pass1":"val_pass1", 
                                       "set1":"new_val_set1"})


