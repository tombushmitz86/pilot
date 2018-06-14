import requests
import base64
import sys

unit_id = sys.argv[1]
pic_name = sys.argv[2]

with open('/home/pi/camera/{}.jpg'.format(pic_name), 'rb') as image_file:
    image = base64.b64encode(image_file.read())

url = 'http://46.101.229.180:5000/store/{}'.format(unit_id)
query = {'photo_data': image}
res = requests.post(url, json=query)
print(res.text)
