#!/usr/bin/env python

from lxml import etree as ET;
import argparse
import pipes
import sys
import csv
import time
import StringIO
import subprocess
import os
import pyUtil

from lxml import html
from lxml import etree

parser = argparse.ArgumentParser(description="Tool to build an arduino sketch book and library folder that has all our components in it.")
parser.add_argument("--gcom", required=False, type=str, nargs='+', dest='gcom', help="Component manifest files")
parser.add_argument("--target", required=False, type=str, nargs=1, dest='target', help="Name of the sketchbook")
parser.add_argument("-n", required=False, action="store_true", dest='simulate', default=False, help="Just print what would be done")

args = parser.parse_args()


for n in args.gcom:
#    print n
    gcom = ET.parse(open(n, "r")).getroot()
    basedir = "/".join(n.split("/")[0:-1])
    if basedir[0] != "/":
        basedir = os.getcwd() + "/" + basedir

    for i in gcom.xpath("API/arduino/libdirectory"):
        path = basedir + "/" + i.get("path")
        pyUtil.docmd("rm -rf " + args.target[0] + "/libraries/" + (i.get("link-as") if i.get("link-as") is not None else i.get("path").split("/")[-1]), args.simulate)
        pyUtil.docmd("ln -sf " + path + " " +  args.target[0] + "/libraries/" + (i.get("link-as") if i.get("link-as") is not None else i.get("path").split("/")[-1]), args.simulate)
        
        
