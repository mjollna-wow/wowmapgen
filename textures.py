#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Module: textures.py

from PIL import Image

def layer_options(layers_list, layer_number, flags, offset, doodads):
    """ texture number
        flags (256 = use alpha map ; 768 = use alpha map and compressed map)
        offset in MCAL
        ground doodads ID in DBC (ex : 11768 or 30590) """
    layers_list.append(layer_number)
    layers_list.append(flags)
    layers_list.append(offset)
    layers_list.append(doodads)
    return layers_list

def img_to_char_list(image):
    charlist = []
    pix = list(image.getdata())
    for p in range (len(pix)):
        charlist.append(chr(pix[p]))
    return charlist 

def img_to_int_list(image):
    intlist = []
    pix = list(image.getdata())
    for p in range (len(pix)):
        intlist.append(pix[p])
    return intlist 

""" Below : having fun with MCAL, functions per 64x64 alphamap chunk """

def add_opacity(charlist):
    for k in range (4096):
        charlist.append(b"\xFF")
    return charlist

def add_transparency(charlist):
    for k in range (4096):
        charlist.append(b"\x00")
    return charlist

def checkers_opacity(charlist):
    for k in range (64):
        for j in range (64):
            if k < 32 and j < 32:
                charlist.append(b"\xFF")
            elif k >= 32 and j >= 32:
                charlist.append(b"\xFF")
            else:
                charlist.append(b"\x00")
    return charlist

def checkers_first_opacity(charlist):
    for k in range (64):
        for j in range (64):
            if k < 32 and j >= 32:
                charlist.append(b"\xFF")
            else:
                charlist.append(b"\x00")
    return charlist

def image_opacity(charlist, imagepath):
    image = Image.open(imagepath)
    pix = list(image.getdata())
    for k in range (64):
        for j in range (64):
            charlist.append(chr(pix[j+k*64]))
    return charlist 

def adt_stripes(charlist):
    """ To mix all 3 layers of a chunk into horizontal stripes """
    for i in range (1024):
        charlist.append(b"\xFF")
    for i in range (3072):
        charlist.append(b"\x00")

    for i in range (2048):
        charlist.append(b"\x00")
    for i in range (1024):
        charlist.append(b"\xFF")
    for i in range (1024):
        charlist.append(b"\x00")

    for i in range (3072):
        charlist.append(b"\x00")
    for i in range (1024):
        charlist.append(b"\xFF")    
