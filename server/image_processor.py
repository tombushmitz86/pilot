import cv2
from PIL import Image, ImageDraw
import base64
from dbHandler import DBHandler
import ConfigParser

dbHandler = DBHandler()


class ImageProccessor:
    # Parser function for config file:
    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        print('black box is ready')

    def ConfigSectionMap(self, section):
        configs = {}
        options = self.config.options(section)
        for option in options:
            configs[option] = self.config.get(section, option)
            if configs[option] == -1:
                print("skip: %s" % option)
        return configs

    def recsDraw(self, pic_name, cor, votes_color):
        j = 0
        im = Image.open(pic_name)
        for i in range(0, 5):
            cord = (cor[i][0], cor[i][1], cor[i][2], cor[i][3])
            draw = ImageDraw.Draw(im)
            draw.rectangle(cord, outline=500)
            width = 10
            for k in range(width):
                draw.rectangle(cord, outline=votes_color[j])
                cord = (cord[0] + 1, cord[1] + 1, cord[2] + 1, cord[3] + 1)
            j += 1
        return im

    def decision(self, case, free_count, center):
        # Deciosion according to best of 5:
        if case == 'Majority':
            if free_count > 2:
                return 1
            else:
                return 0
        # Deciosion according to at least 2 recs FREE:
        if case == '2 ROIs Free':
            if free_count > 1:
                return 1
            else:
                return 0
        # Deciosion according to at least 2 recs TAKEN:
        if case == '2 ROIs Taken':
            if free_count > 0 & free_count < 4:
                return 0
            else:
                return 1
        # Deciosion according to the CENTER rec:
        if case == 'Center based':
            return center

        return -1

    def Process(self, id, image, coordination, vote, rule):
        # Reading config file to parse
        # Config = ConfigParser.ConfigParser()
        self.config.read("config.txt")

        case = [-1 for i in range(2)]  # case = ['Voting algo', 'Decision rule']
        case[0] = vote   # vote
        case[1] = rule   # decision
        size = 640, 960

        # Get parameters from config file:
        recs = [i for i in range(6)]
        thresh_vers1 = [[] for i in range(2)]  # vals for vers1 thresholds
        thresh_vers2 = [
            int(self.ConfigSectionMap("thresh_vers2")['free_bottom']),
            int(self.ConfigSectionMap("thresh_vers2")['taken_top']),
        ]
        thresh_vers3 = [
            int(self.ConfigSectionMap("thresh_vers3")['free_bottom']),
            int(self.ConfigSectionMap("thresh_vers3")['free_top']),
        ]
        global_thresh = int(self.ConfigSectionMap("global_threshold")['global'])

        val1 = int(self.ConfigSectionMap("free")['rec1'])
        val2 = int(self.ConfigSectionMap("free")['rec2'])
        val3 = int(self.ConfigSectionMap("free")['rec3'])
        val4 = int(self.ConfigSectionMap("free")['rec4'])
        val5 = int(self.ConfigSectionMap("free")['rec5'])

        free_vals = (val1, val2, val3, val4, val5)

        val1 = int(self.ConfigSectionMap("taken")['rec1'])
        val2 = int(self.ConfigSectionMap("taken")['rec2'])
        val3 = int(self.ConfigSectionMap("taken")['rec3'])
        val4 = int(self.ConfigSectionMap("taken")['rec4'])
        val5 = int(self.ConfigSectionMap("taken")['rec5'])
        taken_vals = (val1, val2, val3, val4, val5)
        thresh_vers1[0] = free_vals
        thresh_vers1[1] = taken_vals

        # Decode string to image:
        fh = open("imageToSave.png", "wb")
        fh.write(image.decode('base64'))
        fh.close()

        picture = cv2.imread('imageToSave.png')
        # Crop ROIs:
        recs = coordination

        # TODO: maybe need to change indexs to start with 0 instead of 1
        # NOTE: its img[y: y + h, x: x + w]
        rec1 = picture[recs[0][1]:recs[0][3], recs[0][0]:recs[0][2]]
        rec2 = picture[recs[1][1]:recs[1][3], recs[1][0]:recs[1][2]]
        rec3 = picture[recs[2][1]:recs[2][3], recs[2][0]:recs[2][2]]
        rec4 = picture[recs[3][1]:recs[3][3], recs[3][0]:recs[3][2]]
        rec5 = picture[recs[4][1]:recs[4][3], recs[4][0]:recs[4][2]]

        # Build statistics (var, std, mean):
        recs = [rec1.var(), rec2.var(), rec3.var(), rec4.var(), rec5.var()]
        recs = map(float, recs)
        recs = map(round, recs)

        # VERSION 1
        if case[0] == 'Vote1':
            votes = [0, 0, 0, 0, 0]
            votes_color = ["red", "red", "red", "red", "red"]
            sum_of_votes = 0

            # Extract status relative to MEAN of EACH square (Free: 407,363,411,326,340. Taken: 1580,2475,3670,1600,2463) + Global threshold of 800:
            if abs(recs[0]-thresh_vers1[0][0]) < abs(recs[0]-thresh_vers1[1][0]):
                votes[0] = 1
                votes_color[0] = "green"
            if abs(recs[1]-thresh_vers1[0][1]) < abs(recs[1]-thresh_vers1[1][1]):
                votes[1] = 1
                votes_color[1] = "green"
            if abs(recs[2]-thresh_vers1[0][2]) < abs(recs[2]-thresh_vers1[1][2]):
                votes[2] = 1
                votes_color[2] = "green"
            if abs(recs[3]-thresh_vers1[0][3]) < abs(recs[3]-thresh_vers1[1][3]):
                votes[3] = 1
                votes_color[3] = "green"
            if abs(recs[4]-thresh_vers1[0][4]) < abs(recs[4]-thresh_vers1[1][4]):
                votes[4] = 1
                votes_color[4] = "green"

            # Add global threshold exception:
            for i in range(5):
                if recs[i] > global_thresh:
                    votes[i] = 0
                    votes_color[i] = "red"

            # Saving ROIs image to DB:
            im = self.recsDraw('imageToSave.png', coordination, votes_color)

            # Count the votes:
            for i in range(5):
                sum_of_votes += votes[i]
            status = self.decision(case[1], sum_of_votes, votes[2])

        # Version 2
        if case[0] == 'Vote2':
            votes = [0, 0, 0, 0, 0]
            votes_color = ["red", "red", "red", "red", "red"]
            sum_of_votes = 0
            # Extract status relative to Mean of TOP 3 Largest/Smallest
            #  (Taken: 6699. Free: 200) of a row:
            for i in range(5):
                if abs(recs[i]-thresh_vers2[0]) < abs(recs[i]-thresh_vers2[1]):
                    votes[i] = 1
                    votes_color[i] = "green"

            # Save ROIs image to DB:
            im = self.recsDraw('imageToSave.png', coordination, votes_color)

            # Count the votes:
            for i in range(5):
                sum_of_votes += votes[i]
            status = self.decision(case[1], sum_of_votes, votes[2])

        # Version 3
        if case[0] == 'Vote3':
            votes = [0, 0, 0, 0, 0]
            votes_color = ["red", "red", "red", "red", "red"]
            sum_of_votes = 0
            # Extract status relative to Mean of Bottom/TOP 3 of Free
            # (Top: 712. Bottom: 200) of a row:
            for i in range(5):
                if abs(recs[i]-thresh_vers3[0]) < abs(recs[i]-thresh_vers3[1]):
                    votes[i] = 1
                    votes_color[i] = "green"

            # Save ROIs image to DB:
            im = self.recsDraw('imageToSave.png', coordination, votes_color)

            # Count the votes:
            for i in range(5):
                sum_of_votes += votes[i]
            status = self.decision(case[1], sum_of_votes, votes[2])

        # Version 4
        if case[0] == 'Vote4':
            votes = [0, 0, 0, 0, 0]
            votes_color = ["red", "red", "red", "red", "red"]
            sum_of_votes = 0

            for i in range(5):
                if recs[i] > global_thresh:
                    votes[i] = 0
                else:
                    votes[i] = 1
                    votes_color[i] = "green"

            im = self.recsDraw('imageToSave.png', coordination, votes_color)

            for i in range(5):
                sum_of_votes += votes[i]
            status = self.decision(case[1], sum_of_votes, votes[2])

        # Version 5
        if case[0] == 'Vote5':
            votes = [0, 0, 0, 0, 0]
            votes_color = ["red", "red", "red", "red", "red"]
            sum_of_votes = 0

            # Extract status relative to MEAN of EACH square
            # (Free: 407,363,411,326,340. Taken: 1580,2475,3670,1600,2463):
            if abs(recs[0]-thresh_vers1[0][0]) < abs(recs[0]-thresh_vers1[1][0]):
                votes[0] = 1
                votes_color[0] = "green"
            if abs(recs[1]-thresh_vers1[0][1]) < abs(recs[1]-thresh_vers1[1][1]):
                votes[1] = 1
                votes_color[1] = "green"
            if abs(recs[2]-thresh_vers1[0][2]) < abs(recs[2]-thresh_vers1[1][2]):
                votes[2] = 1
                votes_color[2] = "green"
            if abs(recs[3]-thresh_vers1[0][3]) < abs(recs[3]-thresh_vers1[1][3]):
                votes[3] = 1
                votes_color[3] = "green"
            if abs(recs[4]-thresh_vers1[0][4]) < abs(recs[4]-thresh_vers1[1][4]):
                votes[4] = 1
                votes_color[4] = "green"

            im = self.recsDraw('imageToSave.png', coordination, votes_color)

            for i in range(5):
                sum_of_votes += votes[i]
            status = self.decision(case[1], sum_of_votes, votes[2])

        #
        votes_color = ["white", "white", "white", "white", "white"]
        im_white = self.recsDraw('imageToSave.png', coordination, votes_color)
        im_white.thumbnail(size, Image.ANTIALIAS)
        im_white.save('imageToSave_white.png')
        im.thumbnail(size, Image.ANTIALIAS)
        im.save('imageToSave_colored.png')

        with open('imageToSave_white.png', "rb") as image_file:
            str_white = base64.b64encode(image_file.read())

        with open('imageToSave_colored.png', "rb") as image_file:
            str_colored = base64.b64encode(image_file.read())

        dbHandler.savePicture(id, image, str_white, str_colored, status)
