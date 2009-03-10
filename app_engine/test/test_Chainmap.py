from utils.Chainmap import Chainmap
import unittest
import logging


class ChainmapTests(unittest.TestCase):

    def setUp(self):
        logging.info('In setUp()')
        self.d1 = {'a': 1, 'b': 2}
        self.d2 = {'a': 3, 'd': 4}
        self.cm = Chainmap(self.d1, self.d2)

    def testFound(self):
        """Test element lookup"""
        logging.info('Running testFound()')
        self.assert_('a' in self.cm)
        self.assert_('d' in self.cm)
        self.assert_('d' in self.cm)
        self.assert_('c' not in self.cm)

    def testFoundFirst(self):
        """take value in first dict"""
        self.assertEqual(self.cm['a'], self.d1['a'])
        self.assertEqual(self.cm['b'], self.d1['b'])

    def testFoundSecond(self):
        """if not in first, take in second"""
        self.assertEqual(self.cm['d'], self.d2['d'])

    def testMissKey(self):
        """raise KeyError if not found in any dict"""
        self.assertRaises(KeyError, Chainmap.__getitem__, self.cm, 'c')
