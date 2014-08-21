from lxml import etree as ET;
import pipes

def formatAndWrite(tree, file, encoding="us-ascii", xml_declaration=None, method="xml"):
    t = pipes.Template()
    t.append("xmllint --format $IN", "f-")
    tree.write(open(file, 'w'), encoding=encoding, xml_declaration=xml_declaration, method=method)

