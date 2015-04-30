#!/usr/bin/env python

import argparse
import SwoopGeom
from lxml import etree as ET
import os
import sys
import glob
from os.path import join
from Dingo.Rectangle import Rectangle
import numpy as np

def missing_tag(name, bad_tag, missing_attr):
    sys.stderr.write("Error in component {0}: <{1}> is missing attribute {2}\n".
                     format(name, bad_tag.tag, missing_attr))


def check_artwork_against_package(svg_path, swoop_package):
    pass


parser = argparse.ArgumentParser(description="Checks that the component artwork viewbox"
                                             " matches the bounding box of the Eagle package")
parser.add_argument("-c","--catalog",required=True,
                    help="XML catalog file containing all the components you want to check. "
                         "Requires that each component specify an SVG artwork file with the bounding box already set")
args = parser.parse_args()

xml = ET.parse(args.catalog)

lib_dir = os.environ.get("EAGLE_LIBS") or sys.exit("Did you source setup_gadgets?")

components_dir = os.environ.get("GADGETRON_COMPONENT_LIB")
catalog_dir = os.path.dirname(args.catalog)

print "Loading libraries..."
libraries = {}
for lib in glob.glob(lib_dir + "/*.lbr"):
    basename = os.path.basename(lib)
    libraries[os.path.splitext(basename)[0]] = SwoopGeom.from_file(lib).get_library()

ARE_WE_GOOD = True

for component in xml.findall("component"):
    device = component.find("eagledevice")
    package = None
    placed_parts = component.findall("placedparts/placedpart")
    keyname = component.get("keyname")
    artwork_svg_file = None
    if component.find("schematic") is None:
        print keyname + " has no schematic"

    if len(placed_parts)==0:
        sys.stderr.write("{0} has no placedparts section".format(keyname))
        ARE_WE_GOOD=False
        continue

    if device is not None and len(placed_parts)==1:
        device_name = device.get("device-name")
        if device_name is None:
            missing_tag(keyname, device, "device-name")
            ARE_WE_GOOD = False
        libname = device.get("library")
        if libname=="NONE":
            continue
        lib = libraries.get(libname)
        if lib is None:
            sys.stderr.write("{0} specified nonexistent library {1} in <{2}>\n".
                             format(keyname, libname, device.tag))
            ARE_WE_GOOD = False
            continue
        deviceset = lib.get_deviceset(device.get("device-name"))
        variant = device.get("variant")
        if variant is None:
            sys.stderr.write("{0} does not specify a variant in <{1}>\n".
                             format(keyname, device.tag))
            ARE_WE_GOOD=False
            continue
        package = deviceset.get_device(variant).find_package()
        if len(package)==0:
            sys.stderr.write("Could not find the package for {0} from its <{1}> tag\n".
                             format(keyname, device.tag))
            ARE_WE_GOOD=False
            continue

        svg = placed_parts[0].get("model2D")
        if svg is None:
            missing_tag(keyname, placed_parts[0], "model2D")
            ARE_WE_GOOD=False
            continue

        artwork_svg_file = join(catalog_dir, svg)

    #Pull the package from the schematic
    # sys.exit("{0} has no <eagledevice> defined".format(component.get("keyname")))
    if component.find("schematic") is not None:
        dir = join(components_dir, "Catalog", component.find("homedirectory").text)
        schematic_file = join(dir, component.find("schematic").get("filename"))
        if not os.path.isfile(schematic_file):
            sys.exit(keyname)
        schematic = SwoopGeom.from_file(schematic_file)

        for placedpart in placed_parts:
            part = schematic.get_part(placedpart.get("refdes"))
            if len(part)==0:
                sys.stderr.write("refdes {0} of {1} refers to a nonexistent schematic part {2}\n".
                                 format(placedpart.get("refdes"),keyname,placedpart.get("model2D")))
                ARE_WE_GOOD=False
                continue
    continue


    boxes = package.get_children().get_bounding_box()
    if len(boxes)==0:
        print package.get_children()
        sys.stderr.write("{0} has a package but no bounding box\n".format(keyname))
        ARE_WE_GOOD = False
        continue

    rect = boxes.reduce(Rectangle.union)

if not ARE_WE_GOOD:
    sys.exit("Some components have errors")
