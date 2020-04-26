This repo has been migrated from Bitbucket and converted from Mercurial to git.

# Introduction to WowMapGen

This Python 2.x script is an attempt to generate 4.x Wow ADT. It takes a bunch of parameters to configure terrain, textures, vertex painting and lighting, and some objects placement.

Bear in mind that it is unfinished, it's closer to a working test than a full fledged program. I probably won't work on it again, but feel free to edit it, it's licenced under GPL v3. 

A little more work could make it really usable and nice. For example, there should be uniformisation of the input file formats, better terrain parsing without the image rotation and some better smoothing algorithm, multiple ADT taken into account, handling of objects and good object referecing (every MCRF contains every object at the time), or add water (MH2O) support.

If someone makes nice screenshots of generated maps, I'd be happy to see them :)

Thanks a lot to Zhao for the terrain parsing algorithm. And thank you Trèsmollo for being the script alpha tester.

# Required tools and packages

- You'll need to install PIL, via pip it works fine.
- Otherwise, Python 2.x is required.

# How to customize generation

## Input files folder

All the necessary files have to be in the input/ folder, and have hardcoded names. 

You'll find examples shipped with the script. Be very careful with the file formats (greyscale or color, alpha or no alpha, dimensions), or the program will complain loudly.

## About alpha channels

Photoshop tends to automatically add an alpha channel to every png image. To avoid that, flatten your image before exporting it. Gimp doesn't do that.

## Terrain

- Image file format : greyscale, 8bit, *no* alpha channel, 255x255.
- Filename : terrain.png

About terrain handling : since the ADT grid doesn't contain the same number of vertices per line (inner/outer lines), smooth terrain is quite difficult to achieve when taking a standard pixel grid. That's why the script rotates by 45° the input heightmap before turning it into MCVT chunks.

## Textures

- Images file format : greyscale, 8bit, *no* alpha channel, whatever dimensions but square will give better results (they're resized to 1448x1448 in the script).
- Filenames : layer1.png, layer2.png, layer3.png
- Texture names : textures.txt

Each of the files represent one MCAL chunk alpha layer.

You'll find texture names in the textures.txt file. As in the sample file, you need to put the whole path to the textures, and one texture per line.

There is a "big alpha" option. Set it to True to enable it. This enables LK better alpha layers quality. 
However, you should be aware that modding tools don't always handle big alpha well, and that you can't mix ADTs with different alpha sizes on the same map. Also be careful that WDT flags are set right when using big alpha to avoid crashes (0x06 flags = big alpha + mccv).

In the code, big_alpha == True changes : 
- mcnk flags have 0x8000 set.
- mcly layer size to 4096 per layer.
- mcal_size is set to 12288.
- switch function to make int or char list with the input image, and pack it differently (ok this should be cleaner).

Ground doodads value is hardcoded at the time (id 382). You can edit that in the script directly, around lines 387, and configure a different ID for each layer. 

Ground doodads "fixing" (population of the low resolution map on each chunk) is not implemented. You'll find information on how to do this there : http://www.modcraft.io/index.php?topic=1671.0 . I don't remember exactly, but maybe Noggit includes the fix as well.

## Vertex painting and lighting

- Images file format : RGB, *no* alpha channel, 255x255.
- Filenames : vertex_painting.png, vertex_lighting.png

These respectively correspond to MCCV and MCLV chunks.

Remember, if you retroconvert the files to LK format (thanks to Adspartan Multiconverter for example), that vertex lighting doesn't exist in LK, so you'll lose that information in the process.

## Objects

- Images file format : greyscale, 8bit, *with* alpha channel, I've tested with dimensions 1024x1024.
- Filenames : objects.png
- Texture names : objects.txt

You'll find objects names in the objects.txt file. As in the sample file, you need to put the whole path to the objects, and one object per line. Be careful to use "\" in the paths and not "/". Noggit displays the objects but not the Wow client if you use the wrong separator.

Black pixels = first m2 placement. 
White pixels = no object.

Iirc, the code only handles the first m2, because it's unfinished (and MCRF references everything everywhere in a very ugly way). Adding more objects shouldn't be too much of a hassle though. Greyscale values are designed to represent one object, and pixel coordinates where to place the model on the ADT. I've only tested one object, so I've only used black value to start with. 

I advise you to moderate the amount of black pixels you want to add, since every pixel represents one instance of the model. 1024x1024 is a huge space, and you probably don't want a million bushes on your map. Your Wow client doesn't want that anyway.

# Script arguments

You can launch the script with a custom ADT name as argument.
Ex : python main.py monasteryinstance_30_30.adt

If the filename doesn't match the ADT name pattern, a default name will be used.

# How to get decent results

Here is a sample processing of the input images. Of course it's not the only way to create a good looking ADT.

- Create a nicely detailed greyscale heightmap image, square, something like 1024 ou 2048 wide. Keep it aside.
- Create 3 different versions of this image, playing with alpha, to have texturing that fits terrain heights.
- Re-save your heightmap in the right format for terrain (255x255). Don't hesitate to blur the image a lot, since big contrast on close pixels create height spikes ingame.
- Play with colors on the 255x255 image to create nice vertex painting (and lighting if you intend to keep Cata+ ADT).
- Save everything with the right format/dimensions/alpha or not/filename, and put everything in the input folder.

# To get ADT work in 3.x clients

Use Adspartan's Multiconverter on the generated ADT files (terrain, textures, objects).

If you need some Noggit editing, especially to smooth terrain a little, it's possible to retroconvert the files in 3.x, edit them, and re-convert them to 4.x with the Java ADT converter ( https://bitbucket.org/Mjollna/adtconverter or http://www.modcraft.io/index.php?topic=931.0 ).

# Using the multiple ADT script

There's an attempt at multiple ADT generation in the input folder (subfolder "test_resize"). It takes the input image and splits it in 9 rotated image files ready to be given to the generator, to make a 9 ADT map.

- Create a 540x540 image for the terrain this time (I used greyscale 8bit with alpha in the test).
- Line 34 in the big_terrain_cropper.py file, change the filename to fit your image name.
- Repeat the process for alpha layers and vertex shading.
- Take every set of generated images (terrain 1, layer 1-1, layer 1-2, layer 1-3, vertex painting 1, etc.) into the WowMapGen main script. 

All steps can be fully automated, but I didn't push this far after my initial testing. The 540x540 image is not very detailed, some maths would be necessary to use a bigger input image.

The generated map is not perfect, boundaries need some manual editing afterwards, but it still allows to gain some time. Proper multiple ADT handling would certainly be better, but I won't do it.
