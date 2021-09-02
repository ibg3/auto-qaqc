'''
Created on Aug 9, 2012

@author: sorg
'''

import unittest, datetime, subprocess, sys

#service location informations
HOST="ibg3wradar.ibg.kfa-juelich.de"
PORT=8080
URL="/rur_intern/sos"

#begin of timeinterval for which data will be downloaded
starttime=datetime.datetime(year=2012,month=4,day=16)
#using iso-date-format
DATETIME_FORMAT_STRING = "%Y-%m-%dT%H:%M:%S"
#path to script
path_to_script="clisos.py"
#execution of script
SOS_CLIENT="python %s "%(path_to_script,)

class TestCommandlineSosClient(unittest.TestCase):
    
    def testSzenarioWithoutInformationAboutServiceContent(self):
        print("""
        for a description of all available commanline options use --help option:
        
        """)
        cmd="%s --help"%(SOS_CLIENT,)
        print(cmd)
        print(subprocess.getoutput(cmd))
        #use -h,-p and -u commandline-options to set hostname, port and url  
        sos_client="%s -h %s -p %s -u %s "%(SOS_CLIENT,HOST,PORT,URL) 
        
        self.pause()
        print("""
        
        sos-data is organized in so called offerings. an offering consists of 
        parameters (in sos words phenomenon or observedProperties) and stations (procedures)
        therefore first step for a user, which want data from sos, is to query all
        available offerings from the service
        
        """)
        cmd="%s -O"%(sos_client,)
        print(cmd)
        print(subprocess.getoutput(cmd))
        print("\n")
        self.pause()
        #all available offerings will be printed to stdout. something like that:
        #Soil
        #Climate
        #RawData
        #Discharge
        print("""
        
        to getting all available stations within an offering use -o OFFERING -S options. 
        hereby OFFERING is the name of an offering (known from last request)
        
        """)
        cmd="%s -o %s -S"%(sos_client,"Climate")
        print(cmd)
        print(subprocess.getoutput(cmd))
        print("\n")
        self.pause()
        
        print("""
        
        you can get all measured parameters of an offering or of a station.
        first: all parameters of an offering
               use -o OFFERING -L option
               
        """)
        cmd="%s -o %s -L"%(sos_client,"Climate")
        print(cmd)
        print(subprocess.getoutput(cmd))
        print("\n")
        self.pause()
        
        print("""
        
        second: all parameters of a station
                use -s STATION -D option
                
        """)
        cmd="%s -s %s -D"%(sos_client,"RU_CR_004")
        print(cmd)
        print(subprocess.getoutput(cmd))
        print("\n")
        self.pause()
        
        print("""
        
        if you want a description of a station you can use -X option to print 
        a complete description in xml-format 
        
        """)
        cmd="%s -s %s -X"%(sos_client,"RU_CR_004")
        print(cmd)
        print(subprocess.getoutput(cmd))
        print("\n")
        self.pause()
        
        print("""
        
        now you should know what offering you want to use.
        Then you can create a configuration file with all necessary parameters to
        query data from the service. Option -f FILENAME -C and -o OFFERING do this
        
        """)
        
        cmd="%s -o %s -f climate.offering.cfg -C"%(sos_client,"Climate")
        print(cmd)
        print(subprocess.getoutput(cmd))
        print("\n")
        print("""
        
        above is the content of the created configuration template file. you can modify the content 
        with your needs
        
        """)
        print(open("climate.offering.cfg","r").read())
        self.pause()
        
        print("""
        
        with the configuration file you can download data from the service. use -f FILE option
        to determine the configuration file and -G option to query data.
        
        """)
        cmd="%s -f climate.offering.cfg -G"%(SOS_CLIENT,)
        print(cmd)
        print(subprocess.getoutput(cmd))
        print("\n")
        
    def pause(self):
        print("""
        
        press <return> to continue
        """)
        sys.stdin.readline()
        
if __name__ == '__main__':
    unittest.main()
    