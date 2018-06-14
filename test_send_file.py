import requests
import json
import base64
import random
from threading import Timer
import time
import logging
import hashlib

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def send_file():

    with open("test_free2.jpg","rb") as f:
        picture = base64.b64encode(f.read())
    logging.debug('<Sending picture>')
    request  = {'photo_name' : 'picture.jpg',
                'photo_data' : picture
                }
    response = requests.post("http://0.0.0.0:5000/store/14",json=request)
    if response.status_code == 200:
        logging.debug('<Upload Success>')
    else:
        logging.debug('<Upload Failed>')


def test_register():
    password = hashlib.md5("password1")

    user = {
        'username': 'Avshalom',
        'password' : password.hexdigest(),
        'email':'tombush@post.bgu.ac.il',
        'mode': 'public'}
    response = requests.post("http://132.73.203.234:5000/register",json=user)
    if response.status_code == 200:
        logging.debug("registration completed")
    else:
        logging.debug("registration failed")

def test_addUnit():
    unit = {'username' : 'Avshi',
            'id': 9852,
            'location_lat': '32.085105',
            'location_long': '34.787178'}
    response = requests.post("http://0.0.0.0:5000/addUnit",json=unit)
    if response.status_code == 200:
        logging.debug("unit add completed")
    else:
        logging.debug("unit add failed")
def test_change_mode():
    change = {'mode': 'private'}
    response = requests.post('http://0.0.0.0:5000/changemode/tom',json=change)
    if response.status_code == 200:
        logging.debug("user mode change  completed")
    else:
        logging.debug("user mode change failed")


def test_getlocations():
    response = requests.get("http://0.0.0.0:5000/getLocations/sam")
    if response.status_code == 200:
        logging.debug("location fetch  completed")
    else:
        logging.debug("location fetch failed")

def get_unit_status():
    response = requests.get("http://0.0.0.0:5000/getStatus/1124")
    if response.status_code == 200:
        logging.debug("status fetch  completed")
    else:
        logging.debug("status fetch failed")


def test_delete():
    response = requests.get("http://0.0.0.0:5000/deleteUnit/9852")
    if response.status_code == 200:
        logging.debug("unit delete   completed")
    else:
        logging.debug("unit delete failed")

pi_id = random.randint(1,10) #randomise pi ID
print "Pi id is {}".format(pi_id)
# get_unit_status()
# test_getlocations()
# test_delete()
# send_file()
# test_register()
# test_change_mode()
# test_addUnit()
# test()
#while(1):
send_file()
  #  time.sleep(5)




# machine address : 46.101.229.180
