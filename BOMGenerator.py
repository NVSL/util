#!/usr/bin/env python

# BOMGenerator script
import Swoop
import argparse
import xml.etree.ElementTree as ET

def parseSchematic( schematic ):
     for n in (Swoop.From(schematic).get_parts()):
         print n.get_name() 

parser = argparse.ArgumentParser(description="Generates a Bill of Materials from a schematic file")
parser.add_argument("-i", "--insch", required=True)
args = parser.parse_args()
schematic = Swoop.from_file(args.insch )
parseSchematic( schematic )
tree = ET.parse('../../Libraries/Components/Catalog/Catalog/Components.cat')
root = tree.getroot()
for child in root:
    elem = child.find("supplier")
    if( elem != None ):
       price = elem.attrib["price"]
       print child.attrib["keyname"], "price: ", price
