#!/usr/bin/env python


import SwoopGeom
import Swoop
import argparse
from Rectangle import Rectangle


# Board mill script
# Right now it just draws rubouts around connected pads
# Mirrored stuff is still glitchy


parser = argparse.ArgumentParser(description="Helps you prepare a board file for the board mill")
parser.add_argument("-i", "--inbrd", required=True)
parser.add_argument("-o", "--outbrd", required=True)
parser.add_argument("-r", "--rubouts", action="store_true",
                    help="Add rubouts around every pad that has a connection. Makes things easier to solder.")
args = parser.parse_args()

board = SwoopGeom.BoardFile(args.inbrd)

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


if args.rubouts:
    for elem in board.get_elements():
        center = elem.get_point()
        package = board.get_libraries().get_package(elem.get_package())
        for pad in package.get_pads():
            #Check if pad is connected
            if board.get_signals().get_contactrefs().\
                    with_element(elem.get_name()).with_pad(pad.get_name()).count() > 0:
                #Rubout box around pad
                #Give 0.9mm of rubout space
                rub_box = pad.get_bounding_box().move(center).pad(0.9)
                rubout_layers = []
                for overlap in board.get_overlapping(rub_box).with_type(Swoop.Wire):
                    if overlap.get_layer()=='Top' and 'tRubout' not in rubout_layers:
                        rubout_layers.append('tRubout')
                    if overlap.get_layer()=='Bottom' and 'bRubout' not in rubout_layers:
                        rubout_layers.append('bRubout')
                for layer in rubout_layers:
                    board.draw_rect(rub_box, layer)


board.write("out.brd")










