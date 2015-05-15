#!/usr/bin/env python

import argparse
import Swoop.ext.Geometry as SwoopGeom
import Swoop
from lxml import etree as ET
import os
import sys
import glob
from os.path import join
from Dingo.Rectangle import Rectangle
import svgwrite
import numpy as np
import re

def missing_tag(name, bad_tag, missing_attr):
    sys.stderr.write("Error in component {0}: <{1}> is missing attribute {2}\n".
                     format(name, bad_tag.tag, missing_attr))


def check_artwork_against_package(svg_path,
                                  swoop_from_package,
                                  placed_part_tag,
                                  tolerance = 2.0):
    """
    Do the SVG dimensions match the eagle package?

    """

    def close(val1, val2, atol = 0.5):
         # Custom compare with tolerance
        return abs(val1 - val2) <= atol

    # Get height/width attributes
    def get_svg_dim(svg, attr):
        match = re.match(r"(\d+(\.\d+)?)mm", svg.get(attr))
        if match is None:
            sys.stderr.write("{0} has an invalid {1}: {2}\n".format(svg_name, attr, svg.get(attr)))
            return False
        return float(match.group(1))

    def compare_dims(name, svg_dim, package_dim, override=None):
        if override is not None:
            if not close(svg_dim, override, tolerance):
                sys.stderr.write("{svg} has {dim} {sd}mm, but the gcom file says {o}mm\n".
                             format(svg=svg_name, dim=name, sd=svg_dim, o=override))
                return False
        else:
            if not close(svg_dim, package_dim, tolerance):
                sys.stderr.write("{svg} has {dim} {sd}mm, but the package has {dim} {pd}mm\n".
                             format(svg=svg_name, dim=name, sd=svg_dim, pd=package_dim))
                return False
        return True

    assert isinstance(swoop_from_package, Swoop.From)
    assert len(swoop_from_package)==1
    assert isinstance(swoop_from_package[0], Swoop.Package)

    boxes = package.get_children().get_bounding_box()
    if len(boxes)==0:
        sys.stderr.write("Package {0} has no bounding box\n".format(swoop_from_package[0].get_name()))
        return False
    rect = boxes.reduce(Rectangle.union)
    svg_name = os.path.basename(svg_path)
    try:
        svg = ET.parse(svg_path).getroot()
    except ET.XMLSyntaxError:
        sys.stderr.write("Invalid SVG: {0}\n".format(svg_path))
        return False

    package_art_height=None
    package_art_width=None
    package_art_minxy=None
    if placed_part_tag.get("art-height"):
        package_art_height=float(placed_part_tag.get("art-height"))
    if placed_part_tag.get("art-width"):
        package_art_width=float(placed_part_tag.get("art-width"))
    if placed_part_tag.get("art-minxy"):
        package_art_minxy=np.array(map(float, placed_part_tag.get("art-minxy").split()))

    svg_ok = True
    svg_height = get_svg_dim(svg, "height")
    svg_width = get_svg_dim(svg, "width")

    if svg_width is None or svg_height is None:
        return False

    if not compare_dims("height", svg_height, rect.height, package_art_height):
        svg_ok = False
    if not compare_dims("width", svg_width, rect.width, package_art_width):
        svg_ok = False


    bottom_left = np.array(map(float, svg.get("viewBox").split()[:2]))
    bottom_left[1] *= -1
    bottom_left[1] -= svg_height
    if package_art_minxy is not None:
        if not np.allclose(bottom_left, package_art_minxy, atol=tolerance):
            sys.stderr.write("{0} has its lower-left at {1}, the gcom file says {2}\n".\
                format(svg_name, bottom_left, rect.bounds[0]))
            svg_ok=False
    else:
        if not np.allclose(bottom_left, rect.bounds[0], atol=tolerance):
            sys.stderr.write("{0} has its lower-left at {1}, the package has it at {2}\n".\
                format(svg_name, bottom_left, rect.bounds[0]))
            svg_ok=False
    return svg_ok




def get_package(all_libraries, libname, device_name, variant):
    lib = libraries.get(libname)
    if lib is None:
        sys.stderr.write("Nonexistent library {0}\n".
                         format(libname))
        return None
    deviceset = lib.get_deviceset(device_name)
    if variant is None:
        sys.stderr.write("Missing variant\n")
        return None
    return deviceset.get_device(variant).find_package()

class LazyItem(object):
    def __init__(self, path):
        self.path = path
        self.library = None

# Only Swoop (swipe?) libraries when you need them
# People may have a ton of Eagle libraries
class LibraryCollectionLazy(object):
    def __init__(self, libs_dir):
        self._libraries = {}
        for lib in glob.glob(libs_dir + "/*.lbr"):
            basename = os.path.basename(lib)
            self._libraries[os.path.splitext(basename)[0]] = LazyItem(lib)

    def get(self, libname):
        path_lib = self._libraries.get(libname)
        if path_lib is None:
            return None
        if path_lib.library is None:
            path_lib.library = SwoopGeom.from_file(path_lib.path).get_library()
        return path_lib.library


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


libraries = LibraryCollectionLazy(lib_dir)

ARE_WE_GOOD = True

good_components = 0
num_components = 0

for component in xml.findall("component"):
    num_components += 1
    component_ok = True
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
        # Check from the <eagledevice> tag
        # Only one artwork file means we know which it is
        device_name = device.get("device-name")
        if device_name is None:
            missing_tag(keyname, device, "device-name")
            ARE_WE_GOOD = False
        libname = device.get("library")
        if libname=="NONE":
            continue
        variant = device.get("variant")
        package = get_package(libraries, libname, device_name, variant)
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
        component_ok = component_ok and check_artwork_against_package(artwork_svg_file, package, placed_parts[0])
        ARE_WE_GOOD = ARE_WE_GOOD and component_ok


    # Pull the package from the schematic
    # Either there is no <eagledevice> or there are multiple artwork files
    if component.find("schematic") is not None:
        dir = join(components_dir, "Catalog", component.find("homedirectory").text)
        schematic_file = join(dir, component.find("schematic").get("filename"))
        if not os.path.isfile(schematic_file):
            sys.exit(keyname)
        schematic = SwoopGeom.from_file(schematic_file)

        for placedpart in placed_parts:
            refdes = placedpart.get("refdes")
            if refdes is None:
                missing_tag(keyname, placedpart, "refdes")
                ARE_WE_GOOD=False
                continue
            part = schematic.get_part(refdes)
            if len(part)==0:
                sys.stderr.write("refdes '{0}' of {1} refers to a nonexistent schematic part. "
                                 "Schematic file: {2}\n".
                                 format(placedpart.get("refdes"),keyname,schematic_file))
                ARE_WE_GOOD=False
                continue

            package = get_package(libraries, part.get_library()[0], part.get_deviceset()[0], part.get_device()[0])
            if len(package)==0:
                #TODO: probably a koala part
                # sys.stderr.write("Part {0} in {1} has no package\n".format(refdes, schematic_file))
                continue
            artwork_svg_file = join(catalog_dir, placedpart.get("model2D"))
            component_ok = component_ok and check_artwork_against_package(artwork_svg_file, package, placedpart)
            ARE_WE_GOOD = ARE_WE_GOOD and component_ok

    if not component_ok:
        pass
        # sys.stderr.write("{0} is bugged\n".format(keyname))
    else:
        good_components += 1


print "{0} good components out of {1}".format(good_components, num_components)

if not ARE_WE_GOOD:
    sys.exit("Some components have errors")
else:
    print "Success!"

