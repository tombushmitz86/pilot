from flask import jsonify
from base64 import decodestring
from flask import request
import logging
import json
from dbHandler import DBHandler
from image_processor import ImageProccessor


app = Flask(__name__)
dbHandler = DBHandler()
image_processor = ImageProccessor()


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# DEFINES THE ImageProcessor VOTING \ RULING ALGO ##############
vote_algo = 'Vote1'
rule = 'Majority'
image_processor_debug_mode = 'Debug'
#############################################################


# stores a photo that is uploaded from camera unit
@app.route('/store/<id>', methods=['GET', 'POST'])
def store_photo(id):
    logging.debug('<Photo POST recieved>')
    photo = request.get_json()['photo_data']
    roi = dbHandler.getROIcoord(id)

    image_processor.Process(int(id), photo, roi, vote_algo, rule)

    # need to fetch ROI coordinates from the DB
    # need to supply ROI coordiantes of the format : [(x,y,h,w),......]
    # black_box_val =  image_processor(photo,id)
    # print black_box_val
    # dbHandler.savePicture(id, photo, black_box_val)
##########
##########
##########
    return 'ok'


# Get last picture of unit <id>
@app.route('/getpic/<id>')
def send_pic(id):
    logging.debug("server: returning pi#{} photo".format(id))
    photo = dbHandler.getPicture(id)
    returned_photo = {'photo': photo}

    return jsonify(**returned_photo)


# Get status of unit <id>
@app.route('/getStatus/<id>')
def get_status(id):
    status = dbHandler.get_status(id)
    logging.debug("status i s{}".format(status))
    return status


# register a new user.
@app.route('/register', methods=['GET', 'POST'])
def register_user():
    _id = dbHandler.register_user(request.get_json())
    if _id:
        response = {'status': 'ok'}
    else:
        response = {'status': 'failed'}
    return jsonify(**response)


# Add a new unit
@app.route("/addUnit", methods=['GET', 'POST'])
def add_unit():
    unit_details = request.get_json()
    logging.debug("updating {} units".format(unit_details['username']))
    val = dbHandler.add_unit(
        unit_details['username'],
        unit_details['id'],
        unit_details['location_lat'],
        unit_details['location_long'],
    )

    if val:
        return 'ok'
    else:
        return 'faild'


# Status check
@app.route('/')
def health():
     return 'Hi! I am RUNNING'


# change operation mode for a user
@app.route('/changemode/<username>',methods=['GET', 'POST'])
def change_mode(username):
    dbHandler.update_mode(
        username,request.get_json()['mode'],
    )
    return 'ok'

# get all locations , will retrun ALL locations if the user is public or HIS if the user is private
@app.route('/getLocations/<username>')
def return_locations(username):
    Locations = dbHandler.getLocations(username)
    logging.debug("posting back locations to user")
    return json.dumps(Locations)


#delete a camera unit
@app.route('/deleteUnit/<id>')
def deleteUnit(id):
    dbHandler.deleteUnit(id)
    return 'ok'


@app.route('/getDecisionPhoto/<id>')
def getDecisionPhoto(id):
    photo = dbHandler.getDecisionPhoto(id)
    return photo


@app.route('/checkUserDetails',methods=['GET', 'POST'])
def checkUserDetails():
    response ={'status': None}
    status = dbHandler.checkUserCred(request.get_json())
    if status == 'ok':
        details = dbHandler.getUserDetails(request.get_json()['username'])
        del details['_id']
        response['status'] = 'ok'
        response.update(details)
    if status == 'Wrong password':
        response['status'] = 'Wrong password'
    if status == 'No such username exists':
        response['status'] = 'No such username exists'
    logging.debug("finished searching for details")
    return jsonify(**response)


@app.route('/getCamerasStatus')
def getCameraStatus():
    cameras = dbHandler.getCameraStatus()
    return json.dumps(cameras)


@app.route('/test')
def test():
    photo = dbHandler.getColoredImage(14)
    with open("test.png", "wb") as f:
        f.write(decodestring(photo))
    return 'ok'


@app.route('/getROIpicture/<id>')
def getROIpicture(id):
    id = int(id)
    ROI_image = dbHandler.getROIpicture(id)
    return ROI_image

def vacant(image, roi_array, thresh_array):
    #1 - cropping
    #NOTE: ROI is built: BL[X, Y, W, H], BR[X, Y, W, H] ...
    bl = roi_array[0]
    br = roi_array[1]
    c = roi_array[2]
    fl = roi_array[3]
    fr = roi_array[4]

    # NOTE: its img[y: y + h, x: x + w]
    #Back left
    Back_left = image[bl[1]:bl[1]+bl[3], bl[0]:bl[0]+bl[2]]
    #Back right
    Back_right = image[br[1]:br[1]+br[3], br[0]:br[0]+br[2]]
    #Center
    Center = image[c[1]:c[1]+c[3], c[0]:c[0]+c[2]]
    #Front left
    Front_left = image[fl[1]:fl[1]+fl[3], fl[0]:fl[0]+fl[2]]
    #Front right
    Front_right = image[fr[1]:fr[1]+fr[3], fr[0]:fr[0]+fr[2]]

    #2 - taking var
    var_BL = Back_left.var()
    var_BR = Back_right.var()
    var_C = Center.var()
    var_FL = Front_left.var()
    var_FR = Front_right.var()
    var_array = var_BL, var_BR, var_C, var_FL, var_FR

    #3 - detecting if the spot is vacant:
    vacant = 0
    for index in range(0, 4):
        if var_array[index] < thresh_array[index]:
            vacant += 1
    if vacant > 2:
        return True
    return False


if __name__ == '__main__':
    app.run(host='0.0.0.0')
