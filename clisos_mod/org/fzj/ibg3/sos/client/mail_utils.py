'''
Created on Apr 3, 2018

@author: sorg
'''

import getpass
import smtplib
from email.mime.text import MIMEText

MSG="""The user %s has downloaded data from %s with following parameters:
Begin:            %s
End:              %s
Offering:         %s
Station(s):       %s
Phenomenon(s):    %s
Sample filter:    -
"""


def sendNotificationMail(fromTs, toTs, offering, stations, observedPRoperties):
    userName=getpass.getuser()
    
    msg = MIMEText(MSG%(userName, fromTs, toTs, offering, stations, observedPRoperties))
    sender="ibg3.webmaster@fz-juelich.de"
    recipients=["j.sorg@fz-juelich.de"]
    
    msg['Subject'] = 'TERENO data was downloaded'
    msg['From'] = sender
    msg['To'] = ",".join(recipients)
    
    s = smtplib.SMTP('webmail.fz-juelich.de')
    s.sendmail(sender, recipients, msg.as_string())
    s.quit()
