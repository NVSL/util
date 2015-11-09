#!/usr/bin/env python

# Check that a board file made with Jet does not have any overlapping components

import argparse
import Swoop.ext.Geometry as SwoopGeom
from Swoop.ext.Shapes import Rectangle
import Swoop
import itertools
import sys

parser = argparse.ArgumentParser(description="Test that a jet board doesn't have any overlapping components")
parser.add_argument("boardfile")
args = parser.parse_args()

brd = SwoopGeom.WithMixin.from_file(args.boardfile)
# print brd

locked_elements = Swoop.From(brd.get_elements()).filtered_by(lambda p: p.get_locked())

for elem in locked_elements:
    t = elem.get_transform()
    # print elem.get_name()
    total_bbox = t.apply(elem.find_package().get_bounding_box())
    # print total_bbox.eagle_code()
    pkg = elem.find_package().get_children()
    # print ""

    for layer in ["tKeepout", "bKeepout"]:
        setattr(elem, layer + "_bbox", total_bbox)
        filtered = Swoop.From(pkg).filtered_by(lambda c: hasattr(c, "get_layer") and c.get_layer()==layer)
        if len(filtered) > 0:
            bbox = filtered.get_bounding_box().reduce(Rectangle.union)
            bbox = t.apply(bbox)
            setattr(elem, layer + "_bbox", bbox)

Good = True

for layer in ["tKeepout","bKeepout"]:
    for elem1, elem2 in itertools.combinations(locked_elements, 2):
        # print elem1.get_name() + " " + elem2.get_name()
        if elem1.get_name() == "LED1_6_LED" and elem2.get_name() == "L_9_DRIVE":
            print "HELP"
            r1 = getattr(elem1, layer+"_bbox")
            r2 = getattr(elem2, layer+"_bbox")
            print r1.eagle_code()
            print r2.eagle_code()
            print r1,r2
            print r1.overlaps(r2)
            print r2.overlaps(r1)
        if getattr(elem1, layer+"_bbox").overlaps(getattr(elem2, layer+"_bbox")):
            Good = False
            sys.stderr.write("{0} overlaps {1} on layer {2}\n".
                             format(elem1.get_name(), elem2.get_name(), layer))

if Good:
    sys.exit(0)
else:
    sys.exit(-1)


