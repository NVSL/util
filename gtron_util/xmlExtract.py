#!/usr/bin/env python

import argparse
from lxml import etree as ET;
import sys
import pipes
import re
import StringIO

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract the data from an xml file according to an xpath expression")

    parser.add_argument('path', metavar='XPATH', type=str, nargs='?',
                        help='XML Files')
    parser.add_argument('xml', metavar='XML', type=str, nargs='*',
                        help='XML Files')

#    parser.add_argument("-f", required=False,  type=str, action="append", nargs='+', dest='xml', help="xml file")
#    parser.add_argument("-p", required=False,  type=str, action="append", nargs='+', dest='path', help="xpath expression")
    parser.add_argument("-o", required=False, type=str, nargs=1, dest='out', help="output file")
    parser.add_argument("-1", required=False, action='store_true', dest='onlyOne', help="Fail if more than one result is found")
    parser.add_argument("--verbatim", required=False, action='store_true', dest='doVerbatim', help="Don't try to be smart about the xpath expression")
 
    args = parser.parse_args()

    # if args.path is None:
    #     args.path = [args.argv[0]]
    #     args.argv = arg.argv[1:]

    # if args.xml is None:
    #     args.xml = args.argv

#    if args.xml 

#    print args.path
#    print args.xml

    if args.out is not None:
        out = open(args.out[0], "w")
    else:
        out = sys.stdout
    
    found = 0
    for f in args.xml:
        try:
            et = ET.parse(f)
        except Exception as e:
            sys.stderr.write("Couldn't parse " + f + "\n")
            sys.exit(1)

        for p in [args.path]:
            if re.search("/@[\w\-]+$",p):
                isText = True
            elif re.search("/text\(\)$",p):
                isText = True
            else:
                if not args.doVerbatim:
                    p = p + "/text()"
                    isText = True
                else:
                    isText = False


            try:
                matches = et.getroot().xpath(p)
                if len(matches) == 0:
                    raise Exception("No matches for '" + p + "' found in " + f)
                for e in matches:
                    if found == 1 and args.onlyOne:
                        sys.exit(1)

                    s = StringIO.StringIO()
                    if isText:
                        s.write(str(e))
                    else:
                        s.write(ET.tostring(e))
                    out.write(s.getvalue())
                    if not args.doVerbatim and len(s.getvalue()) > 0 and s.getvalue()[-1] is not "\n":
                        out.write("\n")
                    found = found + 1
            except ET.XPathEvalError as e:
                sys.stderr.write(str(e) + ": " + p + "\n")
                sys.exit(1)
#            except Exception as e:
#                print str(e)
#                raise e
#                sys.exit(1)
