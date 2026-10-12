"""Checks the same XML against the XSD then the Schematron of each Factur-X profile.
One line per profile: OK, or the first line of the error raised by the library.
Usage: python profils.py [--en] factur-x.xml   (--en: English labels)
"""
import logging
import sys

from facturx import xml_check_schematron, xml_check_xsd

logging.disable(logging.CRITICAL)
EN = "--en" in sys.argv
args = [a for a in sys.argv[1:] if a != "--en"]
xml = open(args[0], "rb").read()
for niveau in ["minimum", "basicwl", "basic", "en16931", "extended"]:
    etape = "XSD"
    try:
        xml_check_xsd(xml, flavor="factur-x", level=niveau)
        etape = "Schematron"
        xml_check_schematron(xml, flavor="factur-x", level=niveau)
        print(f"{niveau:9} OK (XSD and Schematron)" if EN else f"{niveau:9} OK (XSD et Schematron)")
    except Exception as e:
        msg = str(e).splitlines()
        detail = next((l for l in msg if l.startswith(("1.", "Element"))), msg[0])
        if "Here is the error" in msg[0]:
            detail = msg[0].split("Here is the error, which may give you an idea on the cause of the problem: ")[-1]
        print(f"{niveau:9} rejected by {etape}: {detail}" if EN else f"{niveau:9} refusé par {etape} : {detail}")
