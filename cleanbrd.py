#!/usr/bin/env python

#   Clean up a brd file so it works in the (maybe autoplacer) + autorouter

#   No funny board outlines, only rectangles
#   Clean up routing planes (only <wire> and <contactref> allowed in <signal>)
#   No differential pairs so I don't have to constantly click the "ARE YOU SURE??" box during tests
#   Setting autorouting effort to max, directions to *

import argparse
import Component
from EagleBoard import EagleBoard
from lxml import etree as ET
import numpy as np
import itertools
import hashlib
import re
import logging as log

def make_wire(start,end):
    w = ET.Element('wire')
    w.set('layer','20')
    w.set('width','0')
    w.set('x1',str(start[0]))
    w.set('y1',str(start[1]))
    w.set('x2',str(end[0]))
    w.set('y2',str(end[1]))
    return w


parser = argparse.ArgumentParser(description="Clean up a board for the autoplacer and autorouter")
parser.add_argument("-i","--inbrd",required=True)
parser.add_argument("-o","--outbrd",required=True)
parser.add_argument("-v",help="Verbose",action="store_true")
args = parser.parse_args()

if args.v:
    log.basicConfig(level=log.DEBUG)

eagle = EagleBoard(args.inbrd)
plain = eagle.getPlain()
outline = Component.get_bounding_rectangle(plain)

#Rectangular outlines
plain.clear()
verts = list(outline.vertices())
for i in xrange(4):
    plain.append(make_wire(verts[i],verts[(i+1)%4]))


#Clean anything routed or routing plane nonsense
for signal in eagle.getSignals():
    for elem in signal:
        if elem.tag != 'contactref':
            signal.remove(elem)
            log.info("Removed signal elem " + elem.tag)


#Remove differential pairs
for signal in eagle.getSignals():
    if re.search(r"_[NP]$",signal.attrib['name']):
        first_part = signal.attrib['name'][0:-2]
        #Give it a new name unlikely to collide with anything else
        signal.attrib['name'] = first_part + "_" + hashlib.md5(signal.attrib['name']).hexdigest()[0:5]
        log.info("Removed differential pair " + first_part)

#Find the autorouter effort AND PUSH IT TO THE LIMIT
#PAST THE POINT OF NO RETURN
auto_settings = {
    'RoutingGrid':'0.25mm',
    'AutoGrid':'1',
    'Efforts':'2',
    'TopRouterVariant':'1'
}

for router_pass in eagle.getAutorouter():
    if router_pass.attrib['name']=='Default':
        for k in auto_settings.keys():
            if len(router_pass.findall("param[@name='{0}']".format(k)))==0:
                e = ET.Element('param')
                e.attrib['name']= k
                router_pass.append(e)
                log.info("Added autorouter " + k + " element")

        for param in router_pass:
            if param.attrib['name'] in auto_settings.keys():
                param.attrib['value'] = auto_settings[param.attrib['name']]
            elif param.attrib['name'].startswith('PrefDir') and param.attrib['value'] != '0':
                param.attrib['value'] = 'a'
            else:
                continue
            log.info("Changed autorouter setting " + param.attrib['name'])



eagle.write(args.outbrd)


