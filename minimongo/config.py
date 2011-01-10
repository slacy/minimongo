from socket import gethostname
from mvp.ec2 import machine_roles

localhost = 'localhost'
port = 27017

hostname = gethostname()
if hostname == 'slacy-sunfire' or hostname == 'whisper':
    host = localhost
else:
    host = machine_roles('mongodb')[0].private_dns_name
