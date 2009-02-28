#!/usr/bin/env python
# encoding: utf-8
"""
Chainmap.py

From : http://code.activestate.com/recipes/305268/
"""

import UserDict
import unittest


class Chainmap(UserDict.DictMixin):
    """Combine multiple mappings for sequential lookup.
    
    For example, to emulate Python's normal lookup sequence:
    
        import __builtin__
        pylookup = Chainmap(locals(), globals(), vars(__builtin__))        
    """
    
    def __init__(self, *maps):
        self._maps = maps
    
    def __getitem__(self, key):
        for mapping in self._maps:
            try:
                return mapping[key]
            except KeyError:
                pass
        raise KeyError(key)

class ChainmapTests(unittest.TestCase):
  
  def setUp(self):
    self.d1 = {'a':1, 'b':2}
    self.d2 = {'a':3, 'd':4}
    self.cm = Chainmap(self.d1, self.d2)
  
  def testFound(self):
    self.assert_('a' in self.cm)
    self.assert_('b' in self.cm)
    self.assert_('d' in self.cm)
    self.assert_('c' not in self.cm)
  
  def testFoundFirst(self):
    # take value in first dict
    self.assertEqual(self.cm['a'], self.d1['a'])
    self.assertEqual(self.cm['b'], self.d1['b'])
  
  def testFoundSecond(self):
    # if not in first, take in second
    self.assertEqual(self.cm['d'], self.d2['d'])
  
  def testMissKey(self):
    # raise KeyError if not found in any dict
    self.assertRaises(KeyError, Chainmap.__getitem__, self.cm ,'c')


if __name__ == '__main__':
  unittest.main()