#!/usr/bin/env python

from os.path import dirname, abspath
import sys
sys.path.insert(0, dirname(dirname(abspath(__file__))))
import settings
from django.core.management import setup_environ
setup_environ(settings)

import unittest
from datetime import datetime
from decimal import Decimal
import django.contrib.auth.models as a_models
import membership.models as m_models

class TestQuarterFunctions(unittest.TestCase):

  def get_member(self):
    for member in m_models.Member.objects.filter(date_departed__isnull = True):
      if not member.is_on_loa:
        return member


  def setUp(self):
    self.m = self.get_member()

  def test_quarter_diff(self):
    self.assertEqual(self.m.quarter_diff(datetime(2012,1,1), datetime(2012,1,1)), 0)
    self.assertEqual(self.m.quarter_diff(datetime(2012,1,1), datetime(2012,4,1)), 1)
    self.assertEqual(self.m.quarter_diff(datetime(2012,1,1), datetime(2012,7,1)), 2)
    self.assertEqual(self.m.quarter_diff(datetime(2012,1,1), datetime(2012,10,1)), 3)
    self.assertEqual(self.m.quarter_diff(datetime(2012,1,1), datetime(2013,1,1)), 4)
    self.assertEqual(self.m.quarter_diff(datetime(2012,1,1), datetime(2013,4,1)), 5)
    self.assertEqual(self.m.quarter_diff(datetime(2012,1,1), datetime(2013,7,1)), 6)
    self.assertEqual(self.m.quarter_diff(datetime(2012,1,1), datetime(2013,10,1)), 7)
    self.assertEqual(self.m.quarter_diff(datetime(2012,1,1), datetime(2014,1,1)), 8)
    self.assertEqual(self.m.quarter_diff(datetime(2012,1,1), datetime(2013,10,2)), -1)
    self.assertEqual(self.m.quarter_diff(datetime(2012,1,1), datetime(2013,10,2)), -1)
    self.assertEqual(self.m.quarter_diff(datetime(2012,1,1), datetime(2013,9,1)), -1)

  def test_round_to_quarter(self):
    self.assertEqual(self.m.round_to_quarter(datetime(2012,1,1)), datetime(2012,1,1))
    self.assertEqual(self.m.round_to_quarter(datetime(2012,2,1)), datetime(2012,1,1))
    self.assertEqual(self.m.round_to_quarter(datetime(2012,3,1)), datetime(2012,4,1))
    self.assertEqual(self.m.round_to_quarter(datetime(2012,4,1)), datetime(2012,4,1))
    self.assertEqual(self.m.round_to_quarter(datetime(2012,5,1)), datetime(2012,4,1))
    self.assertEqual(self.m.round_to_quarter(datetime(2012,6,1)), datetime(2012,7,1))
    self.assertEqual(self.m.round_to_quarter(datetime(2012,7,1)), datetime(2012,7,1))
    self.assertEqual(self.m.round_to_quarter(datetime(2012,8,1)), datetime(2012,7,1))
    self.assertEqual(self.m.round_to_quarter(datetime(2012,9,1)), datetime(2012,10,1))
    self.assertEqual(self.m.round_to_quarter(datetime(2012,10,1)), datetime(2012,10,1))
    self.assertEqual(self.m.round_to_quarter(datetime(2012,11,1)), datetime(2012,10,1))
    self.assertEqual(self.m.round_to_quarter(datetime(2012,12,1)), datetime(2013,1,1))


  def test_calc_real_equity_increment(self):
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(0), Decimal(200), datetime(2013,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(10), Decimal(200), datetime(2013,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(20), Decimal(200), datetime(2013,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(30), Decimal(200), datetime(2013,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(40), Decimal(200), datetime(2013,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(50), Decimal(200), datetime(2013,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(60), Decimal(200), datetime(2013,1,1)), Decimal(15))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(70), Decimal(200), datetime(2013,1,1)), Decimal(5))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(80), Decimal(200), datetime(2013,1,1)), Decimal(0))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(90), Decimal(200), datetime(2013,1,1)), Decimal(0))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(100), Decimal(200), datetime(2013,1,1)), Decimal(0))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(0), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(10), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(20), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(30), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(40), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(50), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(60), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(70), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(80), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(90), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(100), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(110), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(120), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(130), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(140), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(150), Decimal(200), datetime(2012,1,1)), Decimal(25))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(160), Decimal(200), datetime(2012,1,1)), Decimal(15))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(170), Decimal(200), datetime(2012,1,1)), Decimal(5))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(180), Decimal(200), datetime(2012,1,1)), Decimal(0))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(190), Decimal(200), datetime(2012,1,1)), Decimal(0))
    self.assertEqual(self.m.calc_real_equity_increment(Decimal(25.0),Decimal(200), Decimal(200), datetime(2012,1,1)), Decimal(0))

  def test_potential_new_equity_due(self):
    m = self.get_member()
    m.equity_held = Decimal(0)
    m.date_departed = False
    m.date_joined = datetime(2012,1,1)

    self.assertEqual(m.potential_new_equity_due(), Decimal(25))

    m.equity_held = Decimal(25)
    self.assertEqual(m.potential_new_equity_due(), Decimal(25))
    
    m.equity_held = Decimal(50)
    self.assertEqual(m.potential_new_equity_due(), Decimal(25))
    
    m.equity_held = Decimal(75)
    self.assertEqual(m.potential_new_equity_due(), Decimal(25))
    
    m.equity_held = Decimal(100)
    self.assertEqual(m.potential_new_equity_due(), Decimal(25))
    
    m.equity_held = Decimal(125)
    self.assertEqual(m.potential_new_equity_due(), Decimal(25))

    m.equity_held = Decimal(150)
    self.assertEqual(m.potential_new_equity_due(), Decimal(25))

    m.equity_held = Decimal(160)
    self.assertEqual(m.potential_new_equity_due(), Decimal(15))

    m.equity_held = Decimal(165)
    self.assertEqual(m.potential_new_equity_due(), Decimal(10))

    m.equity_held = Decimal(166)
    self.assertEqual(m.potential_new_equity_due(), Decimal(9))

    m.equity_held = Decimal(175)
    self.assertEqual(m.potential_new_equity_due(), Decimal(0))

    m.equity_held = Decimal(200)
    self.assertEqual(m.potential_new_equity_due(), Decimal(0))

if __name__ == '__main__':
  unittest.main

