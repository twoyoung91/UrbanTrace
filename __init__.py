# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 20:19:57 2024

@author: Yang Yang
"""

def classFactory(iface):
  from .mainPlugin import urbanTrace
  return urbanTrace(iface)