from PIL import Image

import os
import sys
import re

def crop_and_turn(filename):
    img_to_crop = Image.open(filename)
    transp_mask = Image.open("mask261no_alpha_invert.png")

    # Image is cropped into 255*255 rotated squares
    x = 0
    for i in range(3):
      for j in range(3):
        x = x + 1
        area = (j * 180, i * 180, 180 + j * 180, 180 + i * 180)
        cropped_img = img_to_crop.crop(area)
        cropped_img = cropped_img.rotate( -45, expand=1)
        
        bg_img = cropped_img.resize( (261, 261), Image.NEAREST)
        #bg_img = Image.new( 'L', (259, 259), 255 )
        
        cropped_img = cropped_img.resize( (255, 255), Image.NEAREST)
        
        wrapper = Image.new( 'L', (261, 261) )
        wrapper.paste(cropped_img, (3, 3))
        
        bg_img = Image.composite(bg_img, wrapper, transp_mask)
        
        bg_img = bg_img.crop( (3, 3, 258, 258) )
        
        bg_img.save( str(x) + filename )

crop_and_turn("layer3.png")

'''
def crop_and_turn(filename):
    img_to_crop = Image.open(filename)

    # Image is cropped into 255*255 rotated squares
    x = 0
    for i in range(3):
      for j in range(3):
        x = x + 1
        area = (j * 182, i * 182, 182 + j * 182, 182 + i * 182)

        cropped_img = img_to_crop.crop(area)
        cropped_img = cropped_img.rotate( -45, expand=1)        
        cropped_img = cropped_img.resize( (255, 255), Image.NEAREST)
        
        cropped_img.save( str(x) + filename )

crop_and_turn("terrain_test.png")
'''
