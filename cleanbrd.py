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
parser.add_argument("--layers", action="store_true", help="Convert to 4 layer", required=False)
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
    'RoutingGrid':'0.12mm',
    'AutoGrid':'1',
    'Efforts':'2',
    'TopRouterVariant':'1',
    'PrefDir.1': 'a',
    'PrefDir.16': 'a'
}

if args.layers:
    auto_settings['PrefDir.2'] = 'a'
    auto_settings['PrefDir.3'] = 'a'


route_layers = [1,2,3,16]

for router_pass in eagle.getAutorouter():
    if router_pass.attrib['name']=='Default':
        #Add autorouter settings if they're not there
        for k in auto_settings.keys():
            if len(router_pass.findall("param[@name='{0}']".format(k)))==0:
                e = ET.Element('param')
                e.attrib['name']= k
                router_pass.append(e)
                log.info("Added autorouter " + k + " element")

        #Change the settings to what we want
        for param in router_pass:
            if param.attrib['name'] in auto_settings.keys():
                param.attrib['value'] = auto_settings[param.attrib['name']]
            elif param.attrib['name'].startswith('PrefDir'):
                param.attrib['value'] = '0'
            else:
                continue
            log.info("Changed autorouter setting " + param.attrib['name'])

if args.layers:
    route_names = {
        1:'Top',
        2:'Route2',
        3:'Route3',
        16:'Bottom'
    }
    route_colors = {
        1:"4",
        2:"13",
        3:"11",
        16:"1"
    }


    for layer in route_layers:
        if eagle.getLayers().find("layer[@number='{0}']".format(layer)) is None:
            e=ET.Element('layer')
            e.attrib['number'] = str(layer)
            eagle.getLayers().append(e)
            log.info('Added layer ' + str(layer))

    nlayers = int(args.layers)
    for layer in eagle.getLayers():
        layer_num = int(layer.attrib['number'])
        if 1 <= layer_num <= 16:
            if layer_num in route_layers:
                layer.attrib['visible']='yes'
                layer.attrib['active']='yes'
                layer.attrib['fill']='1'
                layer.attrib['color']=route_colors[layer_num]
                layer.attrib['name'] = route_names[layer_num]
            else:
                layer.attrib['visible']='no'
                layer.attrib['active']='no'

    if eagle.getDesignrules().find("param[@name='layerSetup']") is None:
        e =ET.Element('param')
        e.attrib['name']='layerSetup'
        eagle.getDesignrules().append(e)

    lsetup = eagle.getDesignrules().find("param[@name='layerSetup']")
    lsetup.attrib['value']='(1*2*3*16)'



eagle.write(args.outbrd)


