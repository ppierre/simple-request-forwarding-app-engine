#!/usr/bin/env python
"""
server.py

Created by pierre pracht on 2009-03-01.
"""

import os

# ==============================================
# = Check local SDK or production environement =
# ==============================================

def platform():
    """Return where program is executed :
     - App engine SDK                   : 'local'
     - App deployed on Google : 'google'
     - Other                                    : 'unknown'
    """
    if os.environ.get('SERVER_SOFTWARE', '').startswith('Devel'):
            return 'local'
    elif os.environ.get('SERVER_SOFTWARE', '').startswith('Goog'):
            return 'google'
    else:
            return 'unknown'


def main():
    print("Launched on %s" % platform())


if __name__ == '__main__':
    main()
