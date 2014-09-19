from lxml import etree as ET;

def formatAndWrite(tree, file, encoding="us-ascii", xml_declaration=None, method="xml"):
    open(file, 'w').write(ET.tostring(tree, 
                                      pretty_print = True,
                                      encoding=encoding, 
                                      xml_declaration=xml_declaration, 
                                      method=method))

def formatAndWriteString(s, f):
    r = ET.fromstring(s)
    et = ET.ElementTree()
    et._setroot(r)
    formatAndWrite(et,f)
