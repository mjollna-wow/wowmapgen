""" If you get an error at script launch, run this before the script in terminal -> export ETS_TOOLKIT=qt4
    The script runs fine in python 2.7
    
    The whole WowMapGen code is released under https://www.gnu.org/licenses/gpl-3.0.txt
    PIL licence : http://www.pythonware.com/products/pil/license.htm
"""

from PIL import Image

import os
import sys
import re
import textures
import struct
import random

''' ////////////////////////////////////////////// UTILITIES '''

struct_mhdr = struct.Struct("<16I")
size_mhdr = struct.calcsize("<16I")

struct_mcnk_header = struct.Struct("<15I2H4I6I3f3I")

struct_mddf = struct.Struct("<2I6f2H")
size_mddf = struct.calcsize("<2I6f2H")

struct_modf = struct.Struct("<2I12f4H")
size_modf = struct.calcsize("<2I12f4H")

struct_c = struct.Struct("<c")
struct_I = struct.Struct("<I")

adt_tilesize = 533.333333333

def build_offsets(stringlist, offsetslist):
    offset = 0
    for i in range (len(stringlist)):
        offsetslist.append(offset)
        offset = len(stringlist[i]) + 1

def stringlist_to_char(stringlist):
    list_encoded = []
    for i in range (len(stringlist)):
        temp = list(stringlist[i])
        for j in range (len(temp)):
            list_encoded.append(temp[j])
        list_encoded.append(b"\x00")
    return list_encoded

'''
Imported textures are rotated and rescaled to fit terrain.
1024 side : 724.08 for other sides
724.08*2 = 1448.16 (resize post-rotation)

'''

def image_to_grid(filename):
    img_mcal = Image.open(filename)
    img_mcal = img_mcal.rotate( 45, expand=0)
    img_mcal = img_mcal.resize( (1448, 1448), Image.ANTIALIAS)
    img_mcal = img_mcal.crop((212, 212, 1236, 1236))

    alpha_square_imgs = []

    # Image is cropped into 16*16 squares of dimensions 64*64 (4096) to fit mcal size
    x = 0
    for i in range(16):
      for j in range(16):
        x = x + 1
        area = (j * 64, i * 64, 64 + j * 64, 64 + i * 64)
        cropped_img = img_mcal.crop(area)
        alpha_square_imgs.append(cropped_img)
    return alpha_square_imgs

# https://en.wikipedia.org/wiki/Normalization_%28image_processing%29
def normalize_to(max_range, char_array):
    min_value = 0.0 
    max_value = 255.0
    temp_array = []
    for i in range(len(char_array)):
      temp_array.append( int( (char_array[i] - min_value) * max_range / max_value ) )
    return temp_array

''' ////////////////////////////////////////////// GET STUFF USEFUL FOR ALL FILES '''

# Checking paths

current_path = os.getcwd()
input_path = current_path + os.sep + "input" + os.sep
output_path = current_path + os.sep + "output" + os.sep

if not os.path.isdir(input_path):
    print("There's no input folder to get images and models from. Please create one !")
    sys.exit(0)

if not os.path.isdir(output_path):
    print("Creating 'output' folder for the generated ADT where the script is.")
    os.mkdir(output_path)

input_path_content = os.listdir(input_path)

# Checking that the image files are indeed here with the right name
# Also getting M2 and WMO names in the order they're listed.
# At last, getting textures names and order, and big_alpha option in textures.txt

terrain_pattern = re.compile('(terrain.)(jpg|png)', re.IGNORECASE)
layer1_pattern = re.compile('(layer1.)(jpg|png)', re.IGNORECASE)
layer2_pattern = re.compile('(layer2.)(jpg|png)', re.IGNORECASE)
layer3_pattern = re.compile('(layer3.)(jpg|png)', re.IGNORECASE)

wmo_pattern = re.compile('([a-z_0-9])*(\.)(wmo)', re.IGNORECASE)
wmo_group_pattern = re.compile('([a-z_0-9])*(_[0-9]{3}\.wmo)', re.IGNORECASE)
m2_pattern = re.compile('([a-z_0-9])*(\.)(m2)', re.IGNORECASE)
blp_pattern = re.compile('([a-z_0-9])*(\.)(blp)', re.IGNORECASE)
big_alpha_pattern = re.compile('(big_alpha = )(true|false)', re.IGNORECASE) # for big_alpha option
vertex_painting_pattern = re.compile('(vertex_painting.)(jpg|png)', re.IGNORECASE)
vertex_lighting_pattern = re.compile('(vertex_lighting.)(jpg|png)', re.IGNORECASE)

objects_ok = False
textures_ok = False
img_vertex_painting = ""
img_vertex_lighting = ""
img_terrain = "" 
img_layer_1 = "" 
img_layer_2 = ""
img_layer_3 = ""
wmo_names = [] 
m2_names = []
wmo_root_files = []
textures_names = []
big_alpha = True

for filename in input_path_content:
    if filename == "objects.txt":
        objects_ok = True
    if filename == "textures.txt":
        textures_ok = True        
    if vertex_painting_pattern.match(filename):
        img_vertex_painting = filename
    if vertex_lighting_pattern.match(filename):
        img_vertex_lighting = filename
    if terrain_pattern.match(filename):
        img_terrain = filename
    if layer1_pattern.match(filename):
        img_layer_1 = filename
    if layer2_pattern.match(filename):
        img_layer_2 = filename
    if layer3_pattern.match(filename):
        img_layer_3 = filename
    if wmo_pattern.match(filename):
        if not wmo_group_pattern.match(filename):
            wmo_root_files.append(filename) # TODO : use the files to get bounding boxes in wmos

if objects_ok == False:
    print("There's no objects.txt in the input folder. Your objects choices cannot be found, so please add this file and fill it with M2 and WMO full paths ! Objects will be used to populate the ADT in the same order they are in the file.")
    sys.exit(0)    

if textures_ok == False:
    print("There's no textures.txt in the input folder. Your tilesets choices cannot be added, so please add this file and fill it with 4 textures full paths ! Textures will be added in the same order they are in the file.")
    sys.exit(0)

if img_vertex_painting == "":
    print("There's no vertex_painting (jpg or png) image in your input folder. Please add one ! By default, #7F7F7F filled image will be neutral.")
    sys.exit(0)

if img_vertex_lighting == "":
    print("There's no vertex_lighting (jpg or png) image in your input folder. Please add one ! By default, #7F7F7F filled image will be neutral.")
    sys.exit(0)

for line in open(input_path + 'objects.txt', 'r'):
    if re.search(wmo_pattern, line):
        wmo_names.append(line[:-1])
    if re.search(m2_pattern, line):
        m2_names.append(line[:-1])

for line in open(input_path + 'textures.txt', 'r'):
    if re.search(blp_pattern, line):
        textures_names.append(line[:-1])
    if re.search(big_alpha_pattern, line):
        if line.split(" ")[-1][:-1].lower() == "false":
            big_alpha = False

if img_terrain == "" or img_layer_1 == "" or img_layer_2 == "" or img_layer_3 == "":
    print("There's a missing image file in your input folder. ADT cannot be generated.")
    sys.exit(0)

# Having a default name for the generated ADT in case there's no argument given, and replace it only if argument pattern is ok

adt_name = "dalaranprison_30_30.adt"
adt_pattern = re.compile('([a-z_0-9])*(_[0-9]{1,2}_[0-9]{1,2}.adt)', re.IGNORECASE)

if len(sys.argv) > 1:
    if adt_pattern.match(sys.argv[1]):
        adt_name = sys.argv[1]

adt_name_no_ext = adt_name.split('.')[0]
adt_x = int(adt_name_no_ext.rsplit('_', 2)[-2])
adt_y = int(adt_name_no_ext.rsplit('_', 2)[-1])

''' ////////////////////////////////////////////// WRITE TERRAIN ADT (in an ugly way) '''

img_vertex_painting_file = Image.open(input_path + img_vertex_painting)
pix_vertex_painting = list(img_vertex_painting_file.getdata())
vertex_painting = []

img_vertex_lighting_file = Image.open(input_path + img_vertex_lighting)
pix_vertex_lighting = list(img_vertex_lighting_file.getdata())
vertex_lighting = []

img = Image.open(input_path + img_terrain)
pix = list(img.getdata())
chunk_heights = []

inner = 0
outer = 0
lol = 0

# TODO : Last line and column values should match the next ADT corresponding values, which is not the case here. Smoothing should be better than dividing values per 2. And actually, that whole rotation idea should probably be avoided at all.

for l in range (16): # chunk row
    for k in range (16): # chunk col
        for j in range (9):
            for i in range (9):
                if k == 15 and i == 8:
                    lol = 0
                elif l == 15 and j == 8:
                    lol = 0
                else:
                    outer = (127+i-(l*8)+(k*8)-j)+((i+j+(l*8)+(k*8))*255)
                chunk_heights.append(pix[outer] / 2) # values / 2 make terrain smoother
                vertex_painting.append(pix_vertex_painting[outer])
                vertex_lighting.append(pix_vertex_lighting[outer])
            for i in range (8):
                if j < 8:
                    if k == 15 and i == 7:
                        lol = 0
                    elif l == 15 and j == 7:
                        lol = 0
                    else:
                        inner = (127+i-(l*8)+(k*8)-j+255)+((i+j+(l*8)+(k*8))*255)
                    chunk_heights.append(pix[inner] / 2)
                    vertex_painting.append(pix_vertex_painting[inner])
                    vertex_lighting.append(pix_vertex_lighting[inner])

terrainfile = open(output_path + adt_name, 'wb')

terrainfile.write("MVER"[::-1].encode())
terrainfile.write(struct_I.pack(4))
terrainfile.write(struct_I.pack(0x12))

terrainfile.write("MHDR"[::-1].encode())
terrainfile.write(struct_I.pack(size_mhdr))
terrainfile.write(struct_mhdr.pack(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)) # TODO : if (len(water) > 0): chunk_header[40] = b"\x40"

if big_alpha == True:
    mcnk_flags = 0x40 + 0x8000 # (40 80 00 00) do not fix alpha map for big alpha
else:
    mcnk_flags = 0x40 # has MCCV

mcnk_area_id = 0

for i in range (256):
    mcnk_indexX = i / 16
    mcnk_indexY = i % 16
    mcnk_posY = ( ( ( (533.33333 / 16) * mcnk_indexY ) + (533.33333 * adt_x) ) - (533.33333 * 32) ) * -1;
    mcnk_posX = ( ( ( (533.33333 / 16) * mcnk_indexX ) + (533.33333 * adt_y) ) - (533.33333 * 32) ) * -1;
    mcnk_header = struct_mcnk_header.pack( mcnk_flags, mcnk_indexX, mcnk_indexY, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, mcnk_area_id, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, mcnk_posX, mcnk_posY, -80.0, 0, 0, 0 )
    
    terrainfile.write("MCNK"[::-1].encode())
    terrainfile.write(struct_I.pack(2356)) # TODO : calculate that properly
    terrainfile.write(mcnk_header)
    
    vertices = []
    for j in range (145):
        vertices.append(chunk_heights[i*145+j])
    terrainfile.write("MCVT"[::-1].encode())
    terrainfile.write(struct_I.pack(len(vertices) * 4))
    terrainfile.write( struct.pack('f' * len(vertices), *vertices) )

    colors = []    
    for j in range (145):
        colors.append(chr(vertex_painting[j+145*i][2]))
        colors.append(chr(vertex_painting[j+145*i][1])) 
        colors.append(chr(vertex_painting[j+145*i][0]))
        colors.append(b"\x7F")
    terrainfile.write("MCCV"[::-1].encode())   
    terrainfile.write(struct_I.pack(len(colors)))
    terrainfile.write( struct.pack('c' * len(colors), *colors) )

    lights = []
    for j in range (145):
        lights.append(chr(vertex_lighting[j+145*i][2]))
        lights.append(chr(vertex_lighting[j+145*i][1])) 
        lights.append(chr(vertex_lighting[j+145*i][0]))
        lights.append(b"\xFF")
    terrainfile.write("MCLV"[::-1].encode())
    terrainfile.write(struct_I.pack(len(lights)))
    terrainfile.write( struct.pack('c' * len(lights), *lights) )

    normals = []
    for j in range (145): # TODO : one day, maybe, calculate normals. 
        normals.append(b"\x00")
        normals.append(b"\x00") 
        normals.append(b"\x7F")
    normals.append(b"\x00")  # 70 F5 12 00 08 00 00 00 54 F5 12 00
    normals.append(b"\x70")
    normals.append(b"\xF5")
    normals.append(b"\x12")
    normals.append(b"\x00")
    normals.append(b"\x08")
    normals.append(b"\x00")
    normals.append(b"\x00")
    normals.append(b"\x00")
    normals.append(b"\x54")
    normals.append(b"\xF5")
    normals.append(b"\x12")
    normals.append(b"\x00")
    terrainfile.write("MCNR"[::-1].encode())
    terrainfile.write(struct_I.pack(len(normals)))
    terrainfile.write( struct.pack('c' * len(normals), *normals) )
    
    terrainfile.write("MCSE"[::-1].encode())
    terrainfile.write(struct_I.pack(0))

terrainfile.close()

''' ////////////////////////////////////////////// WRITE TEXTURE ADT (in an ugly way) '''

alpha1_square_imgs = image_to_grid(input_path + img_layer_1)
alpha2_square_imgs = image_to_grid(input_path + img_layer_2)
alpha3_square_imgs = image_to_grid(input_path + img_layer_3)

# 4096 * 3 (must be 4096 per texture per chunk in the end)
all_mcal = []

if big_alpha == True:
    # Append image data to 256 mcal alpha chunks
    for i in range(16):
      for j in range(16):
        current_mcal = []
        current_mcal += textures.img_to_char_list(alpha1_square_imgs[j+i*16])
        current_mcal += textures.img_to_char_list(alpha2_square_imgs[j+i*16])
        current_mcal += textures.img_to_char_list(alpha3_square_imgs[j+i*16])
        all_mcal.append(current_mcal)
else:
    # Append image data to 256 mcal alpha chunks
    for i in range(16):
      for j in range(16):
        current_mcal = []
        current_mcal += textures.img_to_int_list(alpha1_square_imgs[j+i*16])
        current_mcal += textures.img_to_int_list(alpha2_square_imgs[j+i*16])
        current_mcal += textures.img_to_int_list(alpha3_square_imgs[j+i*16])
        all_mcal.append(current_mcal)

    # Normalization for 2048 uncompressed map in range (0, 15)
    normalized_mcal = []
    for i in range(len(all_mcal)):
        normalized_mcal.append(normalize_to(15.0, all_mcal[i]))

    shrinked_mcal = []
    first_char = 0
    second_char = 0
    for i in range (len(normalized_mcal)): # 256 chunks
        current_mcal = []
        for j in range(0, len(normalized_mcal[i]), 2):
            full_char = (normalized_mcal[i][j]) << 4 | (normalized_mcal[i][j + 1] & 0x0F) # does that really change anything to invert j and j+1 ?
            current_mcal.append(chr(full_char))
        shrinked_mcal.append(current_mcal)

#print(str(bin(10)) + " " + str(10))
#print(str(bin(13)) + " " + str(13))
#print( str( bin( (10 << 4) | ( 13 & 0x0F) ) ) )

# I already have the textures names from the textures.txt file

textures_layers = []
mcnk_size = 0

if big_alpha == True:
    layer_size = 4096
    mcal_size = 12288
else:
    layer_size = 2048
    mcal_size = 6144

# MCLY for all chunks identical : append to layers the 3 layers with options
textures.layer_options(textures_layers, 0, 0, 0, 382) # TODO : ground doodads value is hardcoded (382), that should go into textures.txt file.
textures.layer_options(textures_layers, 1, 256, 0, 382)
textures.layer_options(textures_layers, 2, 256, layer_size, 382)
textures.layer_options(textures_layers, 3, 256, layer_size * 2, 382)

mcnk_size += len(textures_layers) * 4 + 8 # int size + MCLY name and size
mcnk_size += mcal_size + 8 # char size + MCAL name and size

texturefile = open(output_path + adt_name_no_ext + '_tex0.adt', 'wb')

texturefile.write("MVER"[::-1].encode())
texturefile.write(struct_I.pack(4))
texturefile.write(struct_I.pack(0x12))

# Mamp required for Adspartan's multiconverter (might not be still the case in more recent versions)
texturefile.write("MAMP"[::-1].encode())
texturefile.write(struct_I.pack(4))
texturefile.write(struct_I.pack(0))

mtex = stringlist_to_char(textures_names)

texturefile.write("MTEX"[::-1].encode())
texturefile.write( struct_I.pack( len(mtex)) )
texturefile.write( struct.pack('c' * len(mtex), *mtex) )

for i in range (256):
    texturefile.write("MCNK"[::-1].encode())
    texturefile.write(struct_I.pack(mcnk_size))
    
    texturefile.write("MCLY"[::-1].encode())
    texturefile.write(struct_I.pack(len(textures_layers) * 4))
    texturefile.write( struct.pack('I' * len(textures_layers), *textures_layers) )
    
    if big_alpha == True:
        texturefile.write("MCAL"[::-1].encode())
        texturefile.write( struct_I.pack( len(all_mcal[i])) )
        texturefile.write( struct.pack('c' * len(all_mcal[i]), *all_mcal[i]) )
    else:
        texturefile.write("MCAL"[::-1].encode())
        texturefile.write( struct_I.pack( len(shrinked_mcal[i])) )
        texturefile.write( struct.pack('c' * len(shrinked_mcal[i]), *shrinked_mcal[i]) )

texturefile.close()

''' ////////////////////////////////////////////// WRITE OBJECTS ADT (in an ugly way) '''

# I already have the names and full paths from the input folder + listfile

m2_ids = []
wmo_ids = []

build_offsets(m2_names, m2_ids)
build_offsets(wmo_names, wmo_ids)

mddf = []
modf = []

img_test_objects = Image.open(input_path + "test_objects.png") # this grayscale image HAS an alpha channel, and has to be 1024x1024.
img_test_objects = img_test_objects.rotate( 45, expand=0)
img_test_objects = img_test_objects.resize( (1448, 1448), Image.NEAREST)
img_test_objects = img_test_objects.crop((212, 212, 1236, 1236))

pix_test_objects = list(img_test_objects.getdata())

for i in range(len(pix_test_objects)):
    if pix_test_objects[i][0] == 0:
        mddf_entry = 0
        mddf_unique_id = 579742 + i # TODO this better
        mddf_x = adt_x * adt_tilesize + ( (i % 1024) * adt_tilesize / 1024 )
        mddf_y = 0.0 # this is the height
        mddf_z = adt_y * adt_tilesize + ( (i / 1024) * adt_tilesize / 1024 )
        mddf_rx = random.randint(-360, 360)
        mddf_ry = 0
        mddf_rz = random.randint(-360, 360)
        mddf_scale = 1.5 * 1024
        mddf_flags = 0
        mddf.append( struct_mddf.pack( mddf_entry, mddf_unique_id, mddf_x, mddf_y, mddf_z, mddf_rx, mddf_ry, mddf_rz, mddf_scale, mddf_flags ) )

# adt_x * adt_tilesize + relative coord from top left corner
# ADT to chunk indexX : floor((32 - (adt_x / adt_tilesize)))
# ADT to chunk indexY : floor((32 - (adt_y / adt_tilesize)))

modf_entry = 0
modf_unique_id = 579746
modf_x = adt_x * adt_tilesize + 503.0
modf_y = 100.3662  # this is the height
modf_z = adt_x * adt_tilesize + 73.0
modf_rx = 0
modf_ry = 0
modf_rz = 0
modf_lbx = 16000.0
modf_lby = 5.3662
modf_lbz = 16100.0
modf_ubx = 16600.0
modf_uby = 200.3662
modf_ubz = 16200.0
modf_flags = 0
modf_doodad_set = 0
modf_name_set = 0
modf_padding = 1024

mmdx = stringlist_to_char(m2_names)
mwmo = stringlist_to_char(wmo_names)

modf.append( struct_modf.pack( modf_entry, modf_unique_id, modf_x, modf_y, modf_z, modf_rx, modf_ry, modf_rz, modf_lbx, modf_lby, modf_lbz,modf_ubx, modf_uby, modf_ubz, modf_flags, modf_doodad_set, modf_name_set, modf_padding ) )

# TODO : 
# Append the right objects in MCRD and MCRW (indices from MDDF and MODF). 1 sub-[] per chunk
# for 256 chunk : for i in range len(mddf): get mddf[i][2], apply floor((32 - (adt_x / adt_tilesize))), et mddf[i][4], apply floor((32 - (adt_y / adt_tilesize))), multiply results, and if it's == chunk, then m2_refs.append(i)
# or better : get collision box from m2 and bounding box from wmo, (apply rotation and scale to be accurate), convert area in chunks affected and append that to the right chunks.

m2_refs = []

for i in range( len(mddf) ):
    m2_refs.append(i)

wmo_refs = [0]

objects_mcnk_size = 16 + len(m2_refs) * 4 + len(wmo_refs) * 4

objectsfile = open(output_path + adt_name_no_ext + '_obj0.adt', 'wb')

objectsfile.write("MVER"[::-1].encode())
objectsfile.write(struct_I.pack(4))
objectsfile.write(struct_I.pack(0x12))

objectsfile.write("MMDX"[::-1].encode())
objectsfile.write( struct_I.pack( len(mmdx)) )
objectsfile.write( struct.pack('c' * len(mmdx), *mmdx) )

objectsfile.write("MMID"[::-1].encode())
objectsfile.write(struct_I.pack(len(m2_ids) * 4))
objectsfile.write( struct.pack('I' * len(m2_ids), *m2_ids) )

objectsfile.write("MWMO"[::-1].encode())
objectsfile.write( struct_I.pack( len(mwmo)) )
objectsfile.write( struct.pack('c' * len(mwmo), *mwmo) )

objectsfile.write("MWID"[::-1].encode())
objectsfile.write(struct_I.pack(len(wmo_ids) * 4))
objectsfile.write( struct.pack('I' * len(wmo_ids), *wmo_ids) )

objectsfile.write("MDDF"[::-1].encode())
objectsfile.write(struct_I.pack(size_mddf * len(mddf) ))
for i in range( len(mddf) ):
    objectsfile.write( mddf[i] )

objectsfile.write("MODF"[::-1].encode())
objectsfile.write(struct_I.pack(size_modf))
for i in range( len(modf) ):
    objectsfile.write( modf[i] )

for i in range (256):
    objectsfile.write("MCNK"[::-1].encode())
    objectsfile.write(struct_I.pack(objects_mcnk_size))
    
    objectsfile.write("MCRD"[::-1].encode())
    objectsfile.write(struct_I.pack(len(m2_refs) * 4))
    objectsfile.write( struct.pack('I' * len(m2_refs), *m2_refs) )
    
    objectsfile.write("MCRW"[::-1].encode())
    objectsfile.write(struct_I.pack(len(wmo_refs) * 4))
    objectsfile.write( struct.pack('I' * len(wmo_refs), *wmo_refs) )

objectsfile.close()
