#!/usr/bin/env python3
# Copyright (c) 2018-2019, Darren Hart and the archviz-vr-tools contributors
# SPDX-License-Identifier: BSD 2-Clause "Simplified" License
#
# mkvrjpg.py assembles a stereoscopic jpeg image from left and right eye
# images.  These images can be separate files, or a single image with
# both images, either stacked (left on top) or side by side (left on the
# left). It sets the required XMP properties and embeds the two images
# which allows the image to be viewed in any image viewer (left eye
# image), as well as in photosphere viewers such as the Google Photos
# web viewer, and in stereoscopic VR viewers, such as Google Carboard
# [1] and Google Daydream.
#
# Thanks to Andrew Perry and the Cardboard Camera Toolkit project for
# for the functional example of how to embed the GImage properties.
# https://bitbucket.org/pansapiens/cardboardcam/src/master/
#
# 1. https://developers.google.com/vr/reference/cardboard-camera-vr-photo-format

# Python built-in dependencies
import atexit
import base64
import getopt
import imghdr
import os
import sys
from shutil import copyfile
from tempfile import mkstemp

# External dependencies
import libxmp
from libxmp import XMPFiles
from libxmp.consts import XMP_NS_TIFF
from PIL import Image

# XMP property namespaces
GPANO = u'http://ns.google.com/photos/1.0/panorama/'
GIMAGE = u'http://ns.google.com/photos/1.0/image/'
GAUDIO = u'http://ns.google.com/photos/1.0/audio/'


def usage():
    print('Usage: %s [OPTIONS] [stereo_img || left_img right_img]' %
            os.path.basename(sys.argv[0]))
    print('  -h, --help          display this help and exit')
    print('  -l, --left          left eye image')
    print('  -o, --out           output image')
    print('  -r, --right         right eye image')
    print('  -s, --stereo        stereo image')


# Verify the image exists and is a jpeg image
def check_image(image):
    if not os.path.isfile(image):
        print("%s does not exist or is not a file" % image)
        return False
    if not imghdr.what(image) == 'jpeg':
        print("%s is not a jpeg image" % image)
        return False
    return True


# Embed 'image' as an xmp data property, this is how we have both the
# left and the right eye contained in the same image, while still being
# able to view it in normal viewers as a single image.
def add_gimage_xmp(xmp, image):
    f = open(image, 'rb')
    data = f.read()
    f.close()
    b64data = base64.b64encode(data)
    xmp.set_property(GIMAGE, u'GImage:Mime', 'image/jpeg')
    xmp.set_property(GIMAGE, u'GImage:Data', b64data.decode('utf-8'))
    del b64data


# Add the XMP properties and embed the left and right image data in the
# image specified by out.
def make_vr_image(left, right, out):
    out_image = Image.open(out)
    width, height = out_image.size
    out_image.close()

    xmpfile = XMPFiles(file_path=out, open_forupdate=True)
    xmp = xmpfile.get_xmp()

    xmp.register_namespace(GPANO, 'GPano')
    xmp.register_namespace(GIMAGE, 'GImage')
    xmp.register_namespace(GAUDIO, 'GAudio')
    xmp.register_namespace(XMP_NS_TIFF, 'tiff')

    xmp.set_property_int(GPANO, u'GPano:CroppedAreaLeftPixels', 0)
    xmp.set_property_int(GPANO, u'GPano:CroppedAreaTopPixels', 0)
    xmp.set_property_int(GPANO, u'GPano:CroppedAreaImageWidthPixels', width)
    xmp.set_property_int(GPANO, u'GPano:CroppedAreaImageHeightPixels', height)
    xmp.set_property_int(GPANO, u'GPano:FullPanoWidthPixels', width)
    xmp.set_property_int(GPANO, u'GPano:FullPanoHeightPixels', int(width/2.0))
    xmp.set_property_float(GPANO, u'GPano:InitialViewHeadingDegrees', 180)

    xmp.set_property_int(XMP_NS_TIFF, u'tiff:ImageWidth', width)
    xmp.set_property_int(XMP_NS_TIFF, u'tiff:ImageHeight', height)
    xmp.set_property_int(XMP_NS_TIFF, u'tiff:Orientation', 0)
    xmp.set_property(XMP_NS_TIFF, u'tiff:Make', 'mkvrjpg')
    xmp.set_property(XMP_NS_TIFF, u'tiff:Model', '')

    if left:
        add_gimage_xmp(xmp, left)
    if right:
        add_gimage_xmp(xmp, right)

    if xmpfile.can_put_xmp(xmp):
        xmpfile.put_xmp(xmp)
        print("VR Image saved to: %s" % out)
    else:
        print("Error: cannot put xmp:")
        print(xmp)
    xmpfile.close_file()

# Split a stereo image into temporary left and right eye images
def split_stereo(stereo, left, right):
        stereo_img = Image.open(stereo)
        width, height = stereo_img.size
        if (width == height):
            # left on top, right on bottom
            left_img = stereo_img.crop((0, 0, width, int(height/2.0)))
            right_img = stereo_img.crop((0, int(height/2.0), width, height))
        elif (width == 4 * height):
            # left then right
            left_img = stereo_img.crop((0, 0, int(width/2.0), height))
            right_img = stereo_img.crop((int(width/2.0), 0, width, height))
        else:
            print("Unknown stereo image layout: %s x %s", width, height)
            stereo_img.close()
            exit(1)

        left_img.save(left)
        right_img.save(right)
        stereo_img.close()


def main():
    left = None
    right = None
    out = None
    stereo = None
    mono = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hl:r:o:s:m:",
                ["help","left=","right=","out=","stereo=","mono="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif o in ('-s', '--stereo'):
            if (mono or left or right):
                usage()
                exit(1)
            stereo = a
        elif o in ('-l', '--left'):
            if (stereo or mono):
                usage()
                exit(1)
            left = a
        elif o in ('-r', '--right'):
            if (stereo or mono):
                usage()
                exit(1)
            right = a
        elif o in ('-o', '--out'):
            out = a
            if os.path.exists(out):
                print("Output file already exists: %s" % out)
                exit(1)
        elif o in ('-m', '--mono'):
            if (stereo or left or right):
                usage()
                exit(1)
            mono = a
        else:
            assert False, "unhandled option"

    # Verify we received either stereo or both the left and the right image
    # Verify the arguments are consistent
    if not (mono or stereo or (left and right)):
        if len(args) == 1:
            stereo = args[0]
        elif len(args) == 2:
            left = args[0]
            right = args[1]
        else:
            print('Invalid number of arguments: %s' % len(args))
            usage()
            exit(1)
    elif len(args) > 0:
        usage()
        exit(1)

    # Create an output name if one is not provided
    if not out:
        fd, out = mkstemp('.vr.jpg', 'mkvrjpg-', os.getcwd())
        os.close(fd)

    if mono:
        if not check_image(mono):
            exit(1)
        copyfile(mono, out)
    else:
        if (stereo):
            if not check_image(stereo):
                exit(1)

            # Create the temporary left and right images
            fd, left = mkstemp("-left.jpg")
            os.close(fd)
            atexit.register(os.remove, left)

            fd, right = mkstemp("-right.jpg")
            os.close(fd)
            atexit.register(os.remove, right)

            split_stereo(stereo, left, right)

        if not check_image(left) or not check_image(right):
            exit(1)

        # Create an output image to start with
        copyfile(left, out)

    # Image files are ready go, create the vr image
    make_vr_image(left, right, out)

if __name__ == "__main__":
    main()
