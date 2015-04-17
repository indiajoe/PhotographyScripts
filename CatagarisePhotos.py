#!/usr/bin/env python
""" This script is to catagarise the list of input photos. 
Hashtag catagories are inputed by user when each photo is displayed one after other.
Usage: ./CatagarisePhotos.py PhotosList.txt PhotosWithHashtag.txt
where, PhotosList.txt : Text file with list of photos to catagarise.
       PhotosWithHashtag.txt: Space seperated OUTPUT text file with associated hashtags with image names """

IMGVIEWER = 'gpicview'  #Set your favorite imageviewer here

import os
import sys
import subprocess
try:
    import readline
except ImportError:
    print('Install python readline module for better input entry experience. \n sudo pip install readline ')


if len(sys.argv) < 3 :
    print('-'*10)
    print("""Usage: {0} PhotosList.txt PhotosWithHashtag.txt
where,
    PhotosList.txt : Text file with list of photos to catagarise.
    PhotosWithHashtag.txt: Space seperated OUTPUT text file with associated hashtags with image names """.format(sys.argv[0]))
    print('-'*10)
    sys.exit(1)

try : 
    imgfilelist = open(sys.argv[1],'r')
except IOError :
    print ("Error: Cannot open the file "+sys.argv[1]+". \n Create the Image file list before running this script. \n Eg: \n  find . -iname '*.jpg' | sort  > PhotosList.txt")
    sys.exit(1)

OutputFileName = sys.argv[2]
HashTagsList = []

print('Instruction: Enter the tags for each image in space seperated format. You could reuse previously entered tags by entering their serial number from printed list. All new tags should contain atleast one nondigit character, and no spaces allowed in a tag.')

def is_number(s):   # A function to check whether string s is a number or not.
    try:
        int(s)
        return True
    except ValueError:
        return False


for img in imgfilelist:
    img = img.rstrip()
    pid = subprocess.Popen([IMGVIEWER, img]).pid  #Open image
    Menu = ''
    for i,tags in enumerate(HashTagsList):
        Menu += '{0}:{1}  | '.format(i,tags)
    print('-'*10)
    print(Menu)
    UserInput = raw_input('Tags for {0}:'.format(img))
    CurrentTagsList=[]
    for tag in UserInput.split():
        if is_number(tag): #User entered serial number of tag from Menu
            try:
                CurrentTagsList.append(HashTagsList[int(tag)])
            except IndexError:
                print('Serial number {0} not in printed taglist'.format(tag))
        else:
            CurrentTagsList.append(tag)
            if tag not in HashTagsList: #Updating the Tags list for menu
                HashTagsList.append(tag)
    #Append the tages to image name in output file
    with open(OutputFileName,'a') as outputfile:
        outputfile.write(' '.join([img]+CurrentTagsList)+'\n')

    os.kill(pid,15) # Close the open image window
