#!/usr/bin/env python

# Check that a board file made with Jet does not have any overlapping components

import argparse
import Swoop.ext.Geometry as SwoopGeom
import Swoop

parser = argparse.ArgumentParser(description="Test that a jet board doesn't have any overlapping components")
parser.add_argument("boardfile")
args = parser.parse_args()

brd = Swoop.From(SwoopGeom.WithMixin.from_file(args.boardfile))
print brd

for elem in brd.get_elements():
    # print elem
    print elem.find_package().get_bounding_box()





