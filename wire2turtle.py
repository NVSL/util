#!/usr/bin/env python

import argparse
import Swoop.ext.Geometry as SG
import Swoop
import numpy as np
from Swoop.ext.Shapes import Rectangle


def process_wire_path(board, to_process_set, point_array):
    wire = to_process_set.pop()
    p1 = wire.get_point(0)
    p2 = wire.get_point(1)

    i = 0
    # print p1
    # print p2

    while True:
        # print map(lambda w: list(w.get_points()), to_process)
        # print p1

        #Append first point of init wire
        point_array.append(p1)

        #Use 2nd point as a query to find the next connecting wire
        width = np.array([wire.get_width(), wire.get_width()])
        wires = board.get_overlapping(Rectangle(p2 - width, p2 + width)).\
            with_type(Swoop.Wire).filtered_by(lambda w: w in to_process)

        #If there is no wire, we are back where we started
        if len(wires)==0:
            point_array.append(p2)
            return
        assert len(wires)==1
        wire = wires[0]
        to_process.remove(wire)

        # p1 of the new wire is our query point, p2 is a new point
        if SG.distance(wire.get_point(0), p2) < SG.distance(wire.get_point(1), p2):
            p1, p2 = wire.get_point(0), wire.get_point(1)
        else:
            p2, p1 = wire.get_point(0), wire.get_point(1)

def center_path(points):
    center = np.array([args.width/2.0, args.height/2.0])
    centroid = reduce(lambda s,v: s + v,points,np.zeros(2)) / len(points)
    for i in xrange(len(points)):
        points[i] = points[i] - centroid + center


def scale_path(points, scaling, centroid = None):
    # Apply scaling
    if centroid is None:
        centroid = reduce(lambda s,v: s + v,points,np.zeros(2)) / len(points)
    for i in xrange(len(points)):
        points[i] = (points[i] - centroid)*scaling + centroid

def codegen_path(points, turtle_name):
    i=0
    print "{0}.penUp();".format(turtle_name)
    for p in points:
        print "{0}.moveTo({1}, {2});".format(turtle_name, int(p[0]), args.height - int(p[1]))
        if i==0:
            print "{0}.penDown();".format(turtle_name)
        i += 1



parser = argparse.ArgumentParser(description="Convert a collection of Eagle paths to laser turtle code.")
parser.add_argument("brdfile",help="Board file with wires drawn as plain elements")
parser.add_argument("--turtle",help="Turtle instance name", default="turtle")
parser.add_argument("--height",help="Height of turtle world", type=int, default=1000)
parser.add_argument("--width",help="Width of turtle world", type=int, default=1000)
parser.add_argument("--scale",help="Scale your drawing", type=float, default=1.0)
parser.add_argument("--center",action="store_true",help="Place drawing in the center of the world")
args = parser.parse_args()

board = SG.from_file(args.brdfile)

to_process = set(board.get_plain_elements().with_type(Swoop.Wire))

to_process |= set(board.get_signals().get_wires().with_type(Swoop.Wire))

paths = []

while len(to_process) > 0:
    points = []
    print "Path: "
    process_wire_path(board, to_process, points)
    for p in points:
        print p
    paths.append(points)

centroid = np.zeros(2)
for path in paths:
    for point in path:
        centroid += point
centroid /= sum([len(path) for path in paths])

for path in paths:
    scale_path(path, args.scale, centroid)

center = np.array([args.width/2, args.height/2])
if args.center:
    for path in paths:
        for i in xrange(len(path)):
            path[i] = path[i] - centroid + center


i=0
for p in paths:
    print "// Path {0}".format(i)
    codegen_path(p, args.turtle)
    print ""
    i += 1


