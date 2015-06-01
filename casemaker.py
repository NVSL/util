#!/usr/bin/env python

import argparse
import Swoop.ext.Geometry as SwoopGeom
import Swoop
from solid import *
import numpy as np

def rect2scad(rect, height, z_start = 0):
    """
    Convert a Rectangle into an openscad cube
    """
    return translate([rect.left(), rect.bot(), z_start])(
        cube([rect.width, rect.height, height])
    )


def make_cutout_rect(container, rect, thickness):
    """
    If rect intersects container, return a rectangle to cut out the container
    """
    if container.encloses(rect):
        return None

    cut = rect
    for axis in xrange(2):
        if rect.low(axis) < container.low(axis):    #left/bottom cut
            move = np.array([0,0])
            move[axis] = -thickness*2
            if cut is not None:
            cut = Rectangle.union(cut, rect.copy().move(move))
            cut = rect.copy().move(move)
            # print cut
        if rect.high(axis) > container.high(axis):  #right/top cut
            move = np.array([0,0])
            move[axis] = thickness*2
            cut = Rectangle.union(cut, rect.copy().move(move))
            # print cut
    return cut

parser = argparse.ArgumentParser(description="Make 3D printed cases for your gadgets")
parser.add_argument("brdfile", help="Board file to make a case from")
parser.add_argument("-f","--file", help="SCAD output file")
args = parser.parse_args()

board = SwoopGeom.from_file(args.brdfile)

#Find the bounding box of the board
board_box = board.get_bounding_box()


SPACE = 15.0    #space between board and top/bottom of case
thickness = 6   #thickness of plastic around case

#The shell, which will be hollowed out
inner = translate([board_box.left(), board_box.bot(), -SPACE])(
            cube([board_box.width, board_box.height, SPACE*2])
)

outer_shell = minkowski()(inner, sphere(thickness))

case = outer_shell - inner

tfaceplate_filter = lambda p: hasattr(p,"layer") and p.layer=="tFaceplate"

#Subtract out all the top faceplate stuff
tfaceplate = board.get_elements().\
    get_package_moved().\
    get_children().\
    filtered_by(tfaceplate_filter).\
    get_bounding_box()

tfaceplate += board.get_plain_elements().filtered_by(tfaceplate_filter).get_bounding_box()

for rect in tfaceplate:
    case -= rect2scad(rect,SPACE + 30) #top
    container = rect.copy().pad(1.0)
    if not board_box.encloses(container):  #faceplate sticks out the side
        # print "side cut {0}".format(rect.eagle_code())
        cut = make_cutout_rect(board, container, thickness)
        if cut is not None:
            case -= rect2scad(cut, SPACE)

side_cuts = board.get_plain_elements().\
    filtered_by(lambda p: hasattr(p,"layer") and p.layer=="sideCut").\
    get_bounding_box()


if args.file:
    scad_render_to_file(case, args.file)
else:
    print scad_render(case)

