#!/usr/bin/env python

import argparse
from EagleBoard import *
from PlacerBoard import *

parser = argparse.ArgumentParser(description="Count the number of movable parts that actually do something in a brd file")
parser.add_argument("brdfile")
args = parser.parse_args()


board = PlacerBoard()
board.import_board(EagleBoard(args.brdfile))
print board.num_movable_parts
