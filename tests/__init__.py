import os
import unittest

current_dir = os.path.dirname(__file__)
test_all = unittest.TestLoader().discover(current_dir)
