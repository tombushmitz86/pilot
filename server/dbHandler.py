from bson import ObjectId
from pymongo import MongoClient
import logging
import time
import hashlib


class DBHandler:

    def __init__(self):
        self.client = MongoClient()  # creating a mongod instance
        self.db = self.client.Pilot  # camera units database
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.debug('<connected to database>')


    def getPicture(self, id): # get last picture from pi<id>
        # quary = self.db.saved_pics.find_one({'unit_id' : id})
        quary = self.db.saved_pics.find({'unit_id':id}).sort( '_id', -1).limit(1)
        for doc in quary:
            q = doc['photo']
        return q

    def updateStatus(self, id, status):
        logging.debug("udpating pi#{} photo to {}".format(id,status))
        self.db.saved_pics.update({'id': id},
                                  {'status': status})

    def get_status(self, id):
        quary = self.db.units.find_one({'id': id})
        logging.debug("returning  pi#{} status {}".format(id,quary['status']))
        return quary['status']

    def add_unit(self, username, id, location_lat, location_long): #adding a new pi unit to user's database
        _id = self.db.units.insert({ #adding to unit collection
            'id' : id,
            'location_lat': location_lat,
            'location_long' : location_long,
            'picture_taken' : 0,
            'username' : username
        })
        self.db.users.update({'username' : username} ,{'$set': {'units' : []}})
        self.db.users.update({'username' : username} ,{'$push':{'units' : id}}) #adding to user's unit reference
        if _id :
            logging.debug("finished update units")
            return True
        else:
            return False


# def update_mode(self, username, mode):
#     quary = self.db.users.update({'username': username},{'mode' : mode}, upsert=True)
#     return quary

    def update_mode(self, username, mode):
        self.db.users.update_one({'username': username},{'$set':
                                                                     {'mode' : mode}})

    def register_user(self,new_user_details):
        if self.db.users.find_one({'username' : new_user_details['username']}):
            return 'user already exists'
        _id = self.db.users.insert(new_user_details)
        return _id

        logging.debug('finished registering user')
        return id

    def getLocations(self, username):

        q = self.db.users.find_one({'username' : username}) #get users operation mode
        mode = q['mode']
        Locations = []
        #get only user's own units location
        quarry = self.db.users.find_one({'username' : username})
        arr = quarry['units']
        for unit in arr :
            camera  =self.db.units.find_one({'id' : unit})
            # my_locations.append({camera['username'], camera['location_lat'], camera['location_long'],camera['status'],camera['id']})
            del camera['thresholds']
            del camera['ROI']
            del camera['_id']
            last_picture  = self.getPicture(unit)
            camera['last_picture'] = last_picture
            Locations.append(camera)


        if mode == 'Public':
            cursor = self.db.units.find()
            for doc in cursor :
                if doc['id'] not in quarry['units'] :
                    del doc['_id']
                    if 'ROI' in doc:
                        del doc['ROI']
                    if 'thresholds' in doc:
                        del doc['thresholds']
                    last_picture = self.getPicture(doc['id'])
                    doc['last_picture'] = last_picture
                    Locations.append(doc)

        return Locations

    def deleteUnit(self, id):
        q= self.db.units.find_one({'id' : id})
        username = q['username']
        _id = q['_id']
        self.db.units.remove({'id' : id})
        'removed  from unit collections'
        self.db.users.update({'username': username}, {'$pull': {'units': ObjectId(_id)}})
        logging.debug('removed from user''s list of units')

    def checkUserCred(self, creds):
        user = self.db.users.find_one({'username': creds['username']})
        password = hashlib.md5(creds['password'])

        if(not user):
            return 'No such username exists'
        else:
            if user['password'] != password.hexdigest():
                return 'Wrong password'
        return 'ok'


    def getDecisionPhoto(self, id):
        unit = self.db.units.find_one({'id'})
        return unit['decision_photo']

    def getROIpicture(self, id):
        q = self.db.units.find_one({'id': id})
        return q['ROI_image']

    def getUserDetails(self,username):
        return self.db.users.find_one({'username': username})

    def getCameraStatus(self):
        cameras = []
        cursor = self.db.units.find()

        for item in cursor :
            camera = {}
            camera['id'] = item['id']
            camera['status'] = item['status']
            cameras.append(camera)
        return cameras





    def getVarAndCoordinates(self, id):
        q = self.db.units.find_one({'id': id})
        return (q['ROI'],q['thresholds'])

    def updateRoi(self, id, roi):
        self.db.units.update_one({'id' : id}, {'$set': {'ROI': roi}})
        return

    def updateThresh(self, id, thresh):
        self.db.units.update_one({'id' : id}, {'$set': {'thresholds': thresh}})
        return

    ##########******* FOR BLACK BOX ROUTIN ******##########
    def getROIcoord(self, id):

        q = self.db.units.find_one({'id': int(id)})
        return q['ROI']

    def getColoredImage(self, id):
        q = self.db.units.find_one({'id': id})
        return q['ROI_image_colored']

    def savePicture(self, id, pictureTosave, pictureTosave_roi, pictureTosave_colored, status): # update last picture on pi<id>
        logging.debug("saving photo from pi id {}".format(id))
        # self.db.saved_pics.create_index('createdAt',expireAfterSeconds = 43200) #delete photos after 12hours

        toinsert = {'unit_id' : id,
                    'photo': pictureTosave,
                    'hour': time.strftime("%I:%M:%S"),
                    'date': time.strftime("%d/%m/%Y"),
                    }
        _id = self.db.saved_pics.insert(toinsert)
        # self.db.saved_pics.update_one({'_id': ObjectId(_id)},{"$set" :{'createdAt': datetime.datetime.utcnow()}},upsert = True)

        self.db.units.update_one({'id': id},{'$set' : {'status':status, 'ROI_image':pictureTosave_roi,'ROI_image_colored':pictureTosave_colored}})
        #TODO: need to add here the update of ROI_image in the UNIT document
