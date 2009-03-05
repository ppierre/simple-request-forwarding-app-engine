#!/usr/bin/env python
# encoding: utf-8
"""
yamloptions.py

Created by pierre pracht on 2009-03-01.
Copyright (c) 2009 __pierreTM__. All rights reserved.
"""

import os
import UserDict
import unittest
import yaml

from Chainmap import Chainmap

# ====================
# = Load config file =
# ====================

def get_config_from(config_file, base_dir):
  """Read yaml file relative to script path
  
  Args:
    config_file: filename of yaml file
    base_dir: directory location
  
  Returns:
    a dict of config item indexed by URL
  """
  options_list = yaml.safe_load(file(os.path.join(base_dir,config_file)))
  options_dict = {}
  # organise configuration by requested url
  for item in options_list:
    options_dict[item['url']] = item
  return options_dict


# ===============
# = YamlOptions =
# ===============

class YamlOptions(UserDict.IterableUserDict):
  """
  TODO: add test with read YamlOptions
  """
  
  def __init__(self, yaml_list, yaml_default, base_dir):
    self._yaml_list = yaml_list
    self._yaml_default = yaml_default
    self._base_dir = base_dir
    
    # do initial loading
    self.reload()
  
  
  def reload(self):
    options = {}
    for config_file in reversed(self._yaml_list):
      options.update(get_config_from(config_file, self._base_dir))
    
    # default value for each key (URL)
    config_default = get_config_from(self._yaml_default, self._base_dir)['::dummy::']
    config_forward_default = config_default['forwards'][0]
    for (url_request,config_request) in options.items():
      config_request['forwards'] = [Chainmap(config_forward, config_forward_default)
                                    for config_forward in config_request['forwards']]
      options[url_request] = Chainmap(config_request,config_default)
    
    self.data = options


class YamlOptionsTests(unittest.TestCase):
  def setUp(self):
    pass


if __name__ == '__main__':
  unittest.main()