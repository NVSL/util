#!/usr/bin/env python



import Swoop
import argparse
import sys
import itertools
from Rectangle import Rectangle
from lxml import etree


# Board mill script
# Right now it just draws rubouts around connected pads
# Mirrored stuff is still glitchy


parser = argparse.ArgumentParser(description="Helps you prepare a board file for the board mill")
parser.add_argument("-i", "--inbrd", required=True)
parser.add_argument("-o", "--outbrd", required=True)
parser.add_argument("-r", "--postroute", action="store_true",
                    help="Add rubouts around every pad that has a connection. Makes things easier to solder.")
parser.add_argument("-t", "--preroute", action="store_true",
                    help="Run this before autorouting. Adds tRestrict to every pad with a connection so "
                         "the autorouter only puts traces on the bottom. Also puts vRestrict on every part"
                         "so you don't have vias underneath things. ")
parser.add_argument("-g", "--gspec", help="Gadgetron gspec file for automated options")
args = parser.parse_args()

if not (args.preroute or args.postroute):
    sys.exit("Specify --preroute or --postroute")

board = Swoop.from_file(args.inbrd)

if args.gspec is not None:
    gspec_xml = etree.parse(args.gspec)
    target = gspec_xml.getroot().get("target")
    if target != "LPKF":
        board.write(args.outbrd)
        sys.exit(0)


import Swoop.ext.Geometry as SwoopGeom
board = SwoopGeom.BoardFile(args.inbrd)

def find_signal_for_pad(board, elem, pad):
    for signal in board.get_signals():
        for cref in signal.get_contactrefs():
            if cref.element == elem.name and cref.pad == pad.name:
                return signal
    return None

# Place rubout around this element if there are traces nearby
def rubout_maybe(board, element):
    rub_box = element.get_bounding_box().pad(0.9)
    rubout_layers = []
    for overlap in board.get_overlapping(rub_box).with_type(Swoop.Wire):
        if overlap.get_layer()=='Top' and 'tRubout' not in rubout_layers:
            rubout_layers.append('tRubout')
        if overlap.get_layer()=='Bottom' and 'bRubout' not in rubout_layers:
            rubout_layers.append('bRubout')
    for layer in rubout_layers:
        board.draw_rect(rub_box, layer)


def restrict_pad(board, pad):
    restrict_box = pad.get_bounding_box().pad(0.9)
    board.draw_rect(restrict_box, 'tRestrict')


tRub = Swoop.Layer()
tRub.set_color(13)
tRub.set_fill(11)
tRub.set_number(164)
tRub.set_name("tRubout")
tRub.set_visible("yes")
tRub.set_active("yes")
board.add_layer(tRub)

bRub = Swoop.Layer()
bRub.set_color(3)
bRub.set_fill(5)
bRub.set_number(165)
bRub.set_name("bRubout")
bRub.set_visible("yes")
bRub.set_active("yes")
board.add_layer(bRub)


# Change DRC settings
stuff = ['Wire', 'Pad', 'Via']
for s1,s2 in itertools.product(stuff, stuff):
    param = board.get_designrules().get_param("md" + s1 + s2)
    param.set_value("10mil")

OTHER_DRC = {
    'msDrill': "0.9mm",
    'msWidth': "0.2mm"
}

for k,v in OTHER_DRC.items():
    board.get_designrules().get_param(k).set_value(v)


# Make tRestrict rectangles or rubouts
for elem in board.get_elements():
    if args.preroute:
        bbox = elem.get_package_moved().get_bounding_box()
        assert bbox is not None
        board.draw_rect(bbox, 'vRestrict')

    for pad in elem.get_package_moved().get_pads():
        #Check if pad is connected
        signal = find_signal_for_pad(board, elem, pad)
        if signal is not None and len(signal.get_contactrefs()) > 1:
            #Rubout box around pad
            #Give 0.9mm of rubout space
            if args.postroute:
                rubout_maybe(board, pad)
            if args.preroute:
                restrict_pad(board, pad)

if args.postroute:
    for via in board.get_signals().get_vias():
        rubout_maybe(board, via)



board.write(args.outbrd)


