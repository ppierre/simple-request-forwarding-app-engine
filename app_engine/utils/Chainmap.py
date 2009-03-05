#!/usr/bin/env python
# encoding: utf-8
"""
Chainmap.py

From : http://code.activestate.com/recipes/305268/
"""

import UserDict


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
