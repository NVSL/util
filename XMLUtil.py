from lxml import etree as ET;

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def formatAndWrite(tree, file, encoding="us-ascii", xml_declaration=None, method="xml"):
    indent(tree.getroot());
    f = open(file, 'w')
    f.write("""<?xml version="1.0"?>""")
    f.write(ET.tostring(tree))

def formatAndWriteString(s, f):
    r = ET.fromstring(s)
    et = ET.ElementTree()
    et._setroot(r)
    formatAndWrite(et,f)
