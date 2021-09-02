'''
Created on Mar 17, 2017

@author: sorg
'''

import unittest
from clisos_mod.org.fzj.ibg3.sos.client import sos_result_data_format, om_parser

class TestFormatting(unittest.TestCase):
    
#     def test(self):
#         d=["hallo","lovis","menja","padme","rudy"]
#         print d[0,2,4]
#     
    def testGetObservation(self):
        f=open("/home/sorg/development/fzj/tests/clisos/horst/test.out")
        data=om_parser.OmParsedData(("SoilWeightAvg1minLysimeterSensor11018"))
        converter=om_parser.OmConverter(data)
        om_parser.OmParser(f.read(), data)
        
        #csv=sos_result_data_format.getFormatter(f.read(), "csv")
        #print csv.formatData()