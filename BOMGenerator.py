#!/usr/bin/env python

# BOMGenerator script
import Swoop
import argparse

parser = argparse.ArgumentParser(description="Generates a Bill of Materials from a schematic file")
parser.add_argument("-i", "--insch", required=True)
args = parser.parse_args()
schematic = Swoop.from_file(args.insch )
