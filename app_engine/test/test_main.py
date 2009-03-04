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
    self.assert_a_hooks_ok(response)
  
  def assert_transform(self, req={}, fwd={}):
    self.mock_a_hooks(200, param=fwd)
    self.assert_a_hooks_get_ok(params=req)
  
  def get_config_mixin(self, mixin):
    config = TestMixin.config_mixin.copy()
    config["/request_url"]["forwards"][0].update(mixin)
    return config


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
    self.assert_transform(req={"foo":"bar"}, fwd=CONTAINS("foo"))
  
  def test_value_of_post_parameter(self):
    """Check value of post request parameter"""
    self.mock_a_hooks(200, param={"foo":"bar"})
    self.assert_a_hooks_ok(self.app.post('/request_url', params={"foo":"bar"}))
  
  def test_value_of_get_parameter(self):
    """Check value of get request parameter"""
    self.assert_transform(req={"foo":"bar"}, fwd={"foo":"bar"})


class SimpleTestPOST(TestHelper, SimpleTestMixin):
  """Basic test HTTP method POST"""
  
  def get_config(self):
    return self.get_config_mixin({'method': 'POST'})
  
  def test_forward_http_method_post(self):
    """Check use of HTTP POST method"""
    self.mock_a_hooks(200, method='POST')
    self.assert_a_hooks_get_ok()


class SimpleTestGET(TestHelper, SimpleTestMixin):
  """Basic test HTTP method GET"""
  
  def get_config(self):
    return self.get_config_mixin({'method': 'GET'})
  
  def test_forward_http_method_get(self):
    """Check use of HTTP GET method"""
    self.mock_a_hooks(200,  method='GET')
    self.assert_a_hooks_get_ok()


class SimpleTestRemoveParam(TestHelper, TestMixin):
  """Test of removing request parameter"""
  
  def get_config(self):
    return self.get_config_mixin({'remove': ['sup1','sup2','sup3']})
  
  def test_forward_existing_param(self):
    """Check that existing param are forwarded if not in remove list"""
    self.assert_transform(req={"pass1":"val_pass1"}, fwd={"pass1":"val_pass1"})
  
  def test_suppress_existing_param(self):
    """Check that param are suppressed if in remove list"""
    self.assert_transform(req={"sup1":"val_sup1"}, fwd={})
  
  def test_suppress_and_forward_existing_param(self):
    """Check that existing param are forwarded if not in remove list
    And Check that param are suppressed if in remove list
    """
    self.assert_transform(req={"pass1":"val_pass1", 
                               "sup1":"val_sup1"}, 
                          fwd={"pass1":"val_pass1"})
  
  def test_suppress_and_forward_existing_param_multi(self):
    """Check that existing param are forwarded if not in remove list
    And Check that param are suppressed if in remove list
    With multiple keys
    """
    self.assert_transform(req={"pass1":"val_pass1", 
                               "pass2":"val_pass2", 
                               "sup1":"val_sup1", 
                               "sup3":"val_sup3"}, 
                          fwd={"pass1":"val_pass1", 
                               "pass2":"val_pass2"})


class SimpleTestOnlyParam(TestHelper, TestMixin):
  """Test of filtering request parameter"""
  
  def get_config(self):
    return self.get_config_mixin({'only': ['only1','only2','only3']})
  
  def test_suppress_existing_param(self):
    """Check that existing param are suppressed if not in only list"""
    self.assert_transform(req={"pass1":"val_pass1"}, fwd={})
  
  def test_forward_existing_param(self):
    """Check that param are forwarded if in only list"""
    self.assert_transform(req={"only1":"val_only1"}, fwd={"only1":"val_only1"})
  
  def test_suppress_and_forward_existing_param(self):
    """Check that existing param are suppressed if not in only list
    And Check that param are forwarded if in only list
    """
    self.assert_transform(req={"pass1":"val_pass1", 
                               "only1":"val_only1"}, 
                          fwd={"only1":"val_only1"})
  
  def test_suppress_and_forward_existing_param_multi(self):
    """Check that existing param are suppressed if not in only list
    And Check that param are forwarded if in only list
    With multiple keys
    """
    self.assert_transform(req={"pass1":"val_pass1", 
                               "only2":"val_only2", 
                               "only1":"val_only1", 
                               "pass3":"val_pass3"}, 
                          fwd={"only1":"val_only1", 
                               "only2":"val_only2"})


class SimpleTestDefaultParam(TestHelper, TestMixin):
  """Test of setting default value for request parameter"""
  
  def get_config(self):
    return self.get_config_mixin({'default': {"def1":"val_def1", 
                                              "def2":"val_def2"}})
  
  def test_default_param(self):
    """Check that default param are present even if not in request"""
    self.assert_transform(req={}, fwd={"def1":"val_def1", 
                                       "def2":"val_def2"})
  
  def test_forward_existing_param_and_default(self):
    """Check that param are forwarded even if not existing in default"""
    self.assert_transform(req={"pass1":"val_pass1"},
                          fwd={"pass1":"val_pass1", 
                               "def1":"val_def1", 
                               "def2":"val_def2"})
  
  def test_request_over_default(self):
    """Check that request param take over default value"""
    self.assert_transform(req={"def1":"new_val_def1"}, 
                          fwd={"def1":"new_val_def1", 
                               "def2":"val_def2"})
  
  def test_forward_and_over_default(self):
    """Check that request param take over default value
    And that param are forwarded even if not existing in default
    """
    self.assert_transform(req={"pass1":"val_pass1", 
                               "def1":"new_val_def1"}, 
                          fwd={"pass1":"val_pass1", 
                               "def1":"new_val_def1", 
                               "def2":"val_def2"})


class SimpleTestSetParam(TestHelper, TestMixin):
  """Test of forced value for request parameter"""
  
  def get_config(self):
    return self.get_config_mixin({'set': {"set1":"val_set1", 
                                          "set2":"val_set2"}})
  
  def test_default_param(self):
    """Check that fixed param are present even if not in request"""
    self.assert_transform(req={}, fwd={"set1":"val_set1", 
                                       "set2":"val_set2"})
  
  def test_forward_existing_param_and_set(self):
    """Check that param are forwarded even if not fixed"""
    self.assert_transform(req={"pass1":"val_pass1"}, 
                          fwd={"pass1":"val_pass1", 
                               "set1":"val_set1", 
                               "set2":"val_set2"})
  
  def test_set_over_request(self):
    """Check that request param don't take over fixed value"""
    self.assert_transform(req={"set1":"new_val_set1"}, 
                          fwd={"set1":"val_set1", 
                               "set2":"val_set2"})
  
  def test_forward_and_set_over_request(self):
    """Check that request param don't take over fixed value
    And that param are forwarded even if not fixed
    """
    self.assert_transform(req={"pass1":"val_pass1", 
                               "set1":"new_val_set1"}, 
                          fwd={"pass1":"val_pass1", 
                               "set1":"val_set1", 
                               "set2":"val_set2"})


class OrderTestRemoveOnlyParam(TestHelper, TestMixin):
  """Test order of remove / only"""
  
  def get_config(self):
    return self.get_config_mixin({'remove': ['only_sup1','sup2','sup3'],
                                  'only': ['only_sup1','only2','only3']})
  
  def test_forward_existing_param(self):
    """Check that existing param are forwarded if not in remove list
    and if present in only list
    """
    self.assert_transform(req={"only2":"val_only2"}, fwd={"only2":"val_only2"})
  
  def test_suppress_existing_param_remove(self):
    """Check that param are suppressed if in remove list
    even if present in remove list
    """
    self.assert_transform(req={"only_sup1":"val_only_sup1"}, fwd={})
  
  def test_suppress_existing_param_only(self):
    """Check that existing param are suppressed if not in only list
    even if not in remove list
    """
    self.assert_transform(req={"pass1":"val_pass1"}, fwd={})
  


class OrderTestDefaultRemoveOnlyParam(TestHelper, TestMixin):
  """Test of setting default value for request parameter
   - not in remove list
   - present in only list
   
   TODO: split test in get and post method
  """
  
  def get_config(self):
    return self.get_config_mixin({'default': {"def_remove1":"val_def_remove1", 
                                              "def_only2":"val_def_only2", 
                                              "def_remove_only3":"val_def_remove_only3"}, 
                                  'remove': ['def_remove1','sup2','def_remove_only3'],
                                  'only': ['only1','def_only2','def_remove_only3']})
  
  def test_default_param_and_filter(self):
    """Check that default param are present even if not in request
    But they are in only list and not in remove list
    """
    self.assert_transform(req={}, fwd={"def_only2":"val_def_only2"})
  
  def test_forward_existing_param_and_default_and_filter(self):
    """Check that param are forwarded even if not existing in default
    If they are in only list and not in remove list
    """
    self.assert_transform(req={"only1":"val_only1"},
                          fwd={"only1":"val_only1", 
                               "def_only2":"val_def_only2"})
  
  def test_request_over_default_and_filter(self):
    """Check that request param take over default value
    If they are in only list and not in remove list
    """
    self.assert_transform(req={"def_only2":"new_val_only2"}, 
                          fwd={"def_only2":"new_val_only2"})
  
  def test_forward_and_over_default_and_filter(self):
    """Check that request param take over default value
    And that param are forwarded even if not existing in default
    If they are in only list and not in remove list
    """
    self.assert_transform(req={"only1":"val_only1", 
                               "def_only2":"new_val_only2"}, 
                          fwd={"only1":"val_only1", 
                               "def_only2":"new_val_only2"})
  

