#!/usr/bin/env python



import Swoop
import argparse
import sys
import itertools
from Swoop.ext.Shapes import Rectangle
from lxml import etree
import logging as log

# Board mill script
# Right now it just draws rubouts around connected pads
# Mirrored stuff is still glitchy

# e.g. package.get_pad().transform(element.get_transform())

parser = argparse.ArgumentParser(description="Helps you prepare a board file for the board mill")
parser.add_argument("-i", "--inbrd", required=True)
parser.add_argument("-o", "--outbrd", required=True)
parser.add_argument("-r", "--postroute", action="store_true",
                    help="Run after routing. Add rubouts around every pad that has a connection. Makes things easier to solder.")
parser.add_argument("-rv","--rivets", action="store_true",
                    help="Use rivets to make vias. This changes the drill diameter of everything to the next largest rivet."
                         " This gets applied to all vias, but for pads it is only applied when there is a connected trace on "
                         "the top layer")
parser.add_argument("-p", "--padding", required=False, type=float, default=0.9,
                    help="Amount of space (mm) to put around every pad when adding rubouts. Default is 0.9mm")
parser.add_argument("-t", "--preroute", action="store_true",
                    help="Run this before autorouting. Adds tRestrict to every pad with a connection so "
                         "the autorouter only puts traces on the bottom. Also puts vRestrict on every part"
                         " so you don't have vias underneath things. ")
parser.add_argument("-n","--no-restrict",action="store_true",
                    help="Don't add any tRestrict so you can solder both sides")
parser.add_argument("-nv","--no-vrestrict",action="store_true",
                    help="Don't add any vRestrict. Vias will go absolutely anywhere.")
parser.add_argument("--rubout-all",action="store_true",
                    help="Rubout all pads and vias on both layers")
parser.add_argument("-g", "--gspec", help="Gadgetron gspec file for automated options")
args = parser.parse_args()

if not (args.preroute or args.postroute):
    sys.exit("Specify --preroute or --postroute")

board = Swoop.from_file(args.inbrd)

if args.gspec is not None:
    gspec_xml = etree.parse(args.gspec)
    for i in gspec_xml.getroot().findall("option"):
        if i.get("name") == "cam-target":
            if i.get("value")  == "LPKF":
                log.info("Processing design for board mill")
            else:
                log.info("Skipping board bill processing")
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

def is_pad_connected(board, elem, pad):
    signal = find_signal_for_pad(board, elem, pad)
    if signal is not None and len(signal.get_contactrefs()) > 1:
        return True
    return False

# Place rubout around this element if there are traces nearby
def rubout_maybe(board, element, padding, override):
    rub_box = element.get_bounding_box().pad(padding)
    rubout_layers = []
    if override:
        rubout_layers = ['tRubout', 'bRubout']
    for overlap in board.get_overlapping(rub_box).with_type(Swoop.Wire):
        if overlap.get_layer()=='Top' and 'tRubout' not in rubout_layers:
            rubout_layers.append('tRubout')
        if overlap.get_layer()=='Bottom' and 'bRubout' not in rubout_layers:
            rubout_layers.append('bRubout')

    radius = max(rub_box.width, rub_box.height) / 2.0
    for layer in rubout_layers:
        board.draw_circle(center=rub_box.center(), radius=radius, layer=layer, width=0.001)


def restrict_pad(board, pad):
    restrict_box = pad.get_bounding_box().pad(0.9)
    board.draw_rect(restrict_box, 'tRestrict')


# Inner diameter of rivets (mm). The drill size to accommodate must be 0.3mm more
# Must be in ascending order
RIVET_SIZES =  [0.6, 0.8, 1.0, 1.2]
RIVET_DRILLS = [0.9, 1.1, 1.5, 1.7]

# If the rivet is just slightly too small (within this tolerance) it may still work
RIVET_TOLERANCE = 0.020

def fix_drill_for_rivet(pad_or_via, board_element):
    # Change the drill size of the pad
    new_drill = None

    # Find the next largest rivet for the pad
    # Allow for some tolerance wiggle room
    for i,rivet in enumerate(RIVET_SIZES):
        if rivet + RIVET_TOLERANCE >= pad_or_via.get_drill():
            new_drill = RIVET_DRILLS[i]
            break
    if new_drill is None:
        sys.stderr.write("Cannot use a rivet for pad/via at location {l} in component {c}"
                         ". Its drill diameter ({d}mm) is too large. Forcing bottom soldering instead.\n".
                         format(l=pad_or_via.get_point(),
                                d=pad_or_via.get_drill(),
                                c=elem.get_name()))
        return False
    else:
        pad_or_via.set_drill(new_drill)
        return True


tRub = Swoop.Layer()
tRub.set_color(13)
tRub.set_fill(11)
tRub.set_number(164)
tRub.set_name("tRubout")
tRub.set_visible(True)
tRub.set_active(True)
board.add_layer(tRub)

bRub = Swoop.Layer()
bRub.set_color(3)
bRub.set_fill(5)
bRub.set_number(165)
bRub.set_name("bRubout")
bRub.set_visible(True)
bRub.set_active(True)
board.add_layer(bRub)

rivet_label = Swoop.Layer()
rivet_label.set_color(7)
rivet_label.set_fill(1)
rivet_label.set_visible(True)
rivet_label.set_active(True)
rivet_label.set_number(171)
rivet_label.set_name("rivetDoc")
board.add_layer(rivet_label)

# Change DRC settings

# Default all DRC settings to 10mil first
stuff = ['Wire', 'Pad', 'Via']
for s1,s2 in itertools.product(stuff, stuff):
    param = board.get_designrules().get_param("md" + s1 + s2)
    param.set_value("10mil")

# And here you can tweak each parameter individually
OTHER_DRC = {
    'msDrill': "0.9mm",  # the smallest a via can be
    'msWidth': "0.6mm",
    'mdWireVia':'0.40mm',
    'mdPadVia':'0.50mm',
    'mdPadPad':'0.50mm',
    'mdViaVia':'0.38mm',
    'mdWireWire':'15mil',
    'mdWirePad':'0.60mm'
}

for k,v in OTHER_DRC.items():
    board.get_designrules().get_param(k).set_value(v)


AUTOROUTER = {
    'cfVia' : '99',
    'mnRipupLevel' : '50',
    'mnRipupSteps':'500',
    'mnRipupTotal':'500',
    'tpViaShape':'round',
    'PrefDir.16':'a',
    'PrefDir.1':'a',
    'TopRouterVariant':'1',
    'Efforts':'2',
    'RoutingGrid':'25mil'
}


for apass in board.get_autorouter_passes():
    for param in apass.get_params():
        if param.get_name() in AUTOROUTER:
            param.set_value(AUTOROUTER[param.get_name()])

        # print apass.get_param(k).value
        # if apass.get_param(k) is not None:
        #     apass.get_param(k).set_value(v)


vias = []   # All vias
pads_moved = []   # Connected pads in package_moved (a clone)

# Make tRestrict rectangles or rubouts
for elem in board.get_elements():
    if args.preroute and not args.no_vrestrict:
        bbox = elem.get_package_moved().get_bounding_box()
        assert bbox is not None
        board.draw_rect(bbox, 'vRestrict')

    for pad in elem.get_package_moved().get_pads():
        #Check if pad is connected
        if is_pad_connected(board, elem, pad) or args.rubout_all:
            pads_moved.append(pad)

#Add rubouts for vias
for via in board.get_signals().get_vias():
    vias.append(via)

if args.preroute and not args.no_restrict:
    for pad in pads_moved:
        restrict_pad(board, pad)

if args.postroute:
    for via in vias:
        if args.rivets:
            assert any(abs(via.get_drill() - d) < 0.002 for d in RIVET_DRILLS), "Invalid drill size {0}mm for via".format(via.get_drill())
        rubout_maybe(board, via, args.padding, args.rubout_all)

    # Keep track of already processed pads
    # Some elements have the exact same package and the pads get processed twice
    processed_pads = set()
    for elem in board.get_elements():
        for pad in board.get_libraries().get_package(elem.get_package()).get_pads():
            if is_pad_connected(board, elem, pad) and args.rivets and pad not in processed_pads:
                fix_drill_for_rivet(pad, elem)
                processed_pads.add(pad)

    for pad in pads_moved:
        rubout_maybe(board, pad, args.padding, args.rubout_all)


board.write(args.outbrd)

