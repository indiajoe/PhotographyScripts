#!/usr/bin/env python
""" This script is to group a long list of images into sets of simillar photographs.
The purpose is to identify images which can be stiched to form panorama,
or on a higher level which looks simillar 
                                                 indiajoe@gmail.com """

import numpy as np
#import matplotlib.pyplot as plt
from skimage import io, transform
from skimage.color import rgb2gray, convert_colorspace
from skimage.feature import ORB, match_descriptors, plot_matches
from skimage.transform import ProjectiveTransform
from skimage.measure import ransac


import sys
import time
import logging
LOG_FILENAME = 'ImageGroupingScript.log'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    )
logger = logging.getLogger(__name__)


class GroupChecker(object):
    """ This is a general base class for Group Checker 
    which identifies which group the image belongs to"""
    def __init__(self, name, startGID = 0):
        self.name = name
        self.CurrentGroupID = startGID  # Initial starting value of Group ID

    def getGID(self,image):
        """ Returns the Group ID for the input image """
        self.CurrentGroupID = self.NextGID(image)
        return self.CurrentGroupID

    def NextGID(self,image):
        """ Calculates the next Group ID for the input image """
        pass  # Overrided in Children

    def LoadImage(self,image,Greyscale=False,scale=1):
        """ Loads the raw image file 
        Greyscale = True to load image in greyscale
        scale= 0.25 to reduce the scale of image to 25% """
        try:
            img = io.imread(image,as_grey=Greyscale)
        except IOError:
            print ("Error: Cannot open the image file {0} \n Please verify the path and filename of the image in the input list is correct.".format(image))
            logger.error("Cannot open the image {0}".format(image))
            raise

        logger.debug('Image {0} loaded..'.format(image))
        return transform.rescale(img, scale)


class PanormaGroup(GroupChecker):
    """ This is to check wheter the new image can be 
    considered to be part of a panorama of previous image 
    Based on: http://nbviewer.ipython.org/github/scikit-image/skimage-demos/blob/master/pano/pano.ipynb?raw=true """

    def __init__(self, name, startGID = 0):
        super(PanormaGroup,self).__init__(name, startGID = startGID)
        # "Oriented FAST and rotated BRIEF" feature detector
        self.orb = ORB(n_keypoints=4000, fast_threshold=0.05)
#        self.ImagesWithOverlap = []  # List to store images which has overlap
        self.ImagesKeypointsDescriptors = []  # List of tuples storing ORB (keypoints, descrioptors)
        # Minus one to compensate for the increment which will happen for the first image
        self.CurrentGroupID -= 1
        
    def NextGID(self,image):
        """ Calculates the next Group ID for the input image """
        NewImg = self.LoadImage(image,Greyscale=True,scale=0.25)
        self.orb.detect_and_extract(NewImg)
        NewImgKeyDescr = (self.orb.keypoints, self.orb.descriptors)

        for PreImgKeyDescr in reversed(self.ImagesKeypointsDescriptors):
            # Check for overlap
            matcheOfDesc = match_descriptors(PreImgKeyDescr[1], NewImgKeyDescr[1], cross_check=True)

            # Select keypoints from the source (image to be registered)
            # and target (reference image)
            src = NewImgKeyDescr[0][matcheOfDesc[:, 1]][:, ::-1]
            dst = PreImgKeyDescr[0][matcheOfDesc[:, 0]][:, ::-1]

            model_robust, inliers = ransac((src, dst), ProjectiveTransform,
                                           min_samples=4, residual_threshold=1, max_trials=300)                
                
            NumberOfTrueMatches = np.sum(inliers)  #len(inliers[inliers])

            if NumberOfTrueMatches > 100 :
                # Image has overlap
                logger.debug('Image {0} found a match! (No: of Matches={1})'.format(image,NumberOfTrueMatches))
                break
            else :
                logger.debug('Image {0} not matching..(No: of Matches={1})'.format(image,NumberOfTrueMatches))
                continue

        else:
            # None of the images in the for loop has any overlap...So this is a new Group
            self.ImagesKeypointsDescriptors = [] # Erase all previous group items
            # self.ImagesWithOverlap = [] 

            # Increment Group ID
            self.CurrentGroupID += 1
            logger.debug('Starting a new Panorama group (GID={0})'.format(self.CurrentGroupID))

        # Append the latest image to the current group
        self.ImagesKeypointsDescriptors.append(NewImgKeyDescr) 
        # self.ImagesWithOverlap.append(NewImg)

        # Return the current  group ID
        return self.CurrentGroupID
            

class HSVColorVectorGroup(GroupChecker):
    """ This is to check wheter the new image can be 
    considered to be part of previous image with same Color pattern in the image/ 
     """

    def __init__(self, name, startGID = 0):
        super(HSVColorVectorGroup,self).__init__(name, startGID = startGID)
#        self.ImagesofSimilColor = []  # List to store images which has similar color distribution
        self.ImagesColorVectorList = []  # List of vectors represting the position of image in HSV color space
        # Minus one to compensate for the increment which will happen for the first image
        self.CurrentGroupID -= 1
        
    def NextGID(self,image):
        """ Calculates the next Group ID for the input image """
        NewImg = self.LoadImage(image,Greyscale=False,scale=0.25)
        NewImg_HSV = convert_colorspace(NewImg, 'RGB', 'HSV')
        NewColorVector = self.MeasureColorVector(NewImg_HSV,(8,12,3))  #8 bins for Hue, 12 for saturation and 3 for value
        for PreImgCVector in reversed(self.ImagesColorVectorList):
            # Calculate chi sqr distance 
            pass
            
        # UNDER CONSTRUCTION #

    def MeasureColorVector(self,img,HistSizes):
        """ Returns a color vector obtained by histogram 
        of number of bins mentioned in HistSizes for each color layer """

        ImgX,ImgY,ImgZ = img.shape
        # First define masks for the partions in the image
        Mask0 = np.zeros(img.shape)
        Mask0[ImgX/3:2*ImgX/3,ImgY/3:2*ImgY/3,:] = 1   # Central 1/3 region rectangle
        Vector0 = np.histogramdd(img[Mask0], bins=HistSizes, normed=True)

        Mask1 = np.zeros(img.shape)
        Mask1[0:ImgX/2,0:ImgY/2,:] = 1   # 1st quadrent
        Mask1[0:ImgX/2,0:ImgY/2,:] -= Mask0[0:ImgX/2,0:ImgY/2,:] 
        Vector1 = np.histogramdd(img[Mask1], bins=HistSizes, normed=True)

        Mask2 = np.zeros(img.shape)
        Mask2[ImgX/2:,0:ImgY/2,:] = 1   # 2nd quadrent
        Mask2[ImgX/2:,0:ImgY/2,:] -= Mask0[ImgX/2:,0:ImgY/2,:] 
        Vector2 = np.histogramdd(img[Mask2], bins=HistSizes, normed=True)

        Mask3 = np.zeros(img.shape)
        Mask3[0:ImgX/2,ImgY/2:,:] = 1   # 3rd quadrent
        Mask3[0:ImgX/2,ImgY/2:,:] -= Mask0[0:ImgX/2,ImgY/2:,:] 
        Vector3 = np.histogramdd(img[Mask3], bins=HistSizes, normed=True)

        Mask4 = np.zeros(img.shape)
        Mask4[ImgX/2:,ImgY/2:,:] = 1   # 4th quadrent
        Mask4[ImgX/2:,ImgY/2:,:] -= Mask0[ImgX/2:,ImgY/2:,:] 
        Vector4 = np.histogramdd(img[Mask4], bins=HistSizes, normed=True)

        return np.concatenate((Vector0,Vector1,Vector2,Vector3,Vector4))




def main():

    if len(sys.argv) < 3 :
        print('-'*10)
        print("""Usage: {0} InputPhotoList.txt PhotosWithGroupIDs.txt
        where,
        PhotosList.txt : Text file with list of photos to Group.
        PhotosWithGroupIDs.txt: Space seperated OUTPUT table text file with associated grouptags with image names """.format(sys.argv[0]))
        print('-'*10)
        sys.exit(1)

    logger.info("""************************
    GroupImages script run started.
    Time: {0}
    ************************""".format(time.strftime("%c")))

    try : 
        imgfilelist = open(sys.argv[1],'r')
    except IOError :
        print ("Error: Cannot open the file "+sys.argv[1]+". \n Create the Image file list before running this script. \n Eg: \n  find . -iname '*.jpg' | sort  > InputPhotosList.txt")
        logger.error("Cannot open the file "+sys.argv[1])
        sys.exit(1)

    OUTPUTFile = sys.argv[2]


    # Define group colums
    OverlapPanoramaGroupist = PanormaGroup('OverlapGroup',startGID = 0)

    for img in imgfilelist:
        img = img.rstrip()
        Result = '{0}  {1}'.format(img,OverlapPanoramaGroupist.getGID(img)) 

        print(Result)
        with open(OUTPUTFile,'a') as outfile:
            outfile.write(Result+'\n')



if __name__ == "__main__":
    main()

