#!/usr/bin/env python

import Swoop.ext.Geometry as SG
import Swoop
import argparse
import numpy as np
from Rectangle import Rectangle
import sys
import math

def make_wire(v1, v2, layer="Dimension", width=0.0):
    wire = SG.WithMixin.class_map["wire"]()
    wire.set_point(v1,0)
    wire.set_point(v2,1)
    wire.set_layer(layer)
    wire.set_width(width)
    return wire

def make_drill(v, drill):
    hole = SG.WithMixin.class_map["hole"]()
    hole.set_point(v)
    hole.set_drill(drill)
    return hole


parser = argparse.ArgumentParser(description="Panelize your Eagle boards")
parser.add_argument("brdfile",help="Board file to panelize")
parser.add_argument("outfile",help="Name of output file")
parser.add_argument("-r","--rows",type=int)
parser.add_argument("-c","--columns",type=int)
parser.add_argument("-s","--spacing", type=float, default=1.0,
                    help="Spacing(mm) between each board (width of cut)")
parser.add_argument("-f","--fit",type=float,
                    help="Automatically set the rows and columns so the total area is no bigger than this (in mm^2)")
parser.add_argument("-m","--min-aspect",type=float,default=0.1,
                    help="Minimum aspect ratio when fitting to avoid crazy shapes")
parser.add_argument("-u","--cutout",action="store_true",
                    help="Depanelize information. Everything in the dimension layer indicates where to cut. ")
parser.add_argument("-t","--tab-size", default=1.5, type=float,
                    help="The size of the tabs that you have to cut out after the milling process.")
args = parser.parse_args()

if args.fit is None and args.rows is None and args.columns is None:
    sys.exit("Specify a fit area or the rows and columns")

board = SG.from_file(args.brdfile)

output = board.clone()[0]

output.clear_elements()
output.clear_signals()
output.clear_plain_elements()

dim_filter = lambda p: p.get_layer()=="Dimension"
board_box = board.\
    get_plain_elements().\
    filtered_by(dim_filter).\
    get_bounding_box().\
    reduce(Rectangle.union)


for elem in board.get_plain_elements().filtered_by(dim_filter):
    board.remove_plain_element(elem)

if args.fit is None:
    rows = args.rows
    columns = args.columns
else:
    max_boards = args.fit / board_box.area()
    print "Maximum possible boards: {0}".format(max_boards)
    best_count = 0
    best = []
    H = board_box.height
    W = board_box.width
    S = args.spacing
    for r in xrange(1, int(max_boards)+2):
        for c in xrange(1, int(max_boards)+2):
            # don't allow crazy aspect ratios
            if (min(r,c) / float(max(r,c))) > args.min_aspect:
                area = (r*H + (r-1)*S) * (c*W + (c-1)*S)
                if area <= args.fit and r*c >= best_count:
                    if r*c==best_count:
                        best.append((r,c))
                    else:
                        best=[(r,c)]
                        best_count = r*c
    rows,columns = min(best, key=lambda rc: abs(rc[0]*H - rc[1]*W))
    print "Fit {0} boards, rows,columns={1}".format(rows*columns, (rows,columns))


x_move = board_box.width + args.spacing
y_move = board_box.height + args.spacing


#Copy all elements, plain elements, and signals
for i in xrange(rows):
    for j in xrange(columns):
        offset = np.array([x_move*j, y_move*i])
        for plain in board.get_plain_elements():
            moved = plain.clone()
            moved.move(offset)
            output.add_plain_element(moved)
        for elem in board.get_elements():
            moved = elem.clone()
            moved.move(offset)
            moved.set_name("{0}PANELIZED{1}{2}".format(elem.get_name(),i,j))
            output.add_element(moved)
        for signal in board.get_signals():
            moved_sig = signal.clone()
            moved_sig.set_name("PANELIZED{0}{1}{2}".format(i,j,signal.get_name()))
            for child in moved_sig.get_children():
                child.move(offset)
                if isinstance(child, Swoop.Contactref):
                    child.set_element("{0}PANELIZED{1}{2}".format(child.get_element(),i,j))
            output.add_signal(moved_sig)

TAB_GAP = args.tab_size
DRILL = 1.0

for i in xrange(rows):
    for j in xrange(columns):
        offset = np.array([x_move*j, y_move*i])
        tab_box = board_box.copy().move(offset)
        verts = list(tab_box.vertices())
        if i < rows - 1:
            v1 = verts[0] + np.array([TAB_GAP/2.0, args.spacing/2.0])   #left
            v2 = verts[1] + np.array([-TAB_GAP/2.0, args.spacing/2.0])  #right
            if j==0:
                v1[0] += TAB_GAP/2.0
            if j==columns-1:
                v2[0] -= TAB_GAP/2.0
            if args.cutout:
                horiz = make_wire(v1, v2, width=DRILL)
                output.add_plain_element(horiz)
            else:
                output.add_plain_element(make_drill(v1, DRILL))
                output.add_plain_element(make_drill(v2, DRILL))
        if j < columns - 1:
            v1 = verts[2] + np.array([args.spacing/2.0, TAB_GAP/2.0])   #lower
            v2 = verts[1] + np.array([args.spacing/2.0, -TAB_GAP/2.0])  #upper
            if i==0:
                v1[1] += TAB_GAP/2.0    #full distance to edge
            if i==rows-1:
                v2[1] -= TAB_GAP/2.0
            if args.cutout:
                vertical = make_wire(v1, v2, width=DRILL)
                output.add_plain_element(vertical)
            else:
                output.add_plain_element(make_drill(v1, DRILL))
                output.add_plain_element(make_drill(v2, DRILL))

width = columns*board_box.width + (columns-1)*args.spacing
height = rows*board_box.height + (rows-1)*args.spacing
new_box = Rectangle(board_box.bounds[0], size=(width, height))
verts = list(new_box.vertices())
if not args.cutout:
    for i in xrange(4):
        output.add_plain_element(make_wire(verts[i], verts[(i+1)%4]))


output.write(args.outfile)

