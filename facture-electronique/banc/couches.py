"""Opens a Factur-X PDF and displays its three layers: the page, the attached file, the XMP metadata.
Usage: python couches.py [--en] facture.pdf   (--en: English labels)
"""
import re
import sys

import pypdf

EN = "--en" in sys.argv
args = [a for a in sys.argv[1:] if a != "--en"]
L = {"page": "== 1. The page (what a human reads)" if EN else "== 1. La page (ce que l'humain lit)",
     "pages": "pages:" if EN else "pages :",
     "joint": "== 2. The attached file" if EN else "== 2. Le fichier joint",
     "nom": "name:" if EN else "nom :",
     "taille": "size: {} bytes" if EN else "taille : {} octets",
     "af": "/AF in the catalog: {} associated file(s)" if EN else "/AF dans le catalogue : {} fichier(s) associé(s)",
     "oi": "OutputIntent:" if EN else "OutputIntent :",
     "xmp": "== 3. The XMP metadata" if EN else "== 3. Les métadonnées XMP",
     "absent": "(missing)" if EN else "(absent)",
     "sep": ":" if EN else " :"}
r = pypdf.PdfReader(args[0])
cat = r.trailer["/Root"]

print(L["page"])
print(f"{L['pages']} {len(r.pages)}")
for ligne in r.pages[0].extract_text().splitlines()[:3]:
    print(f"  {ligne}")
print("  ...")

print(L["joint"])
noms = cat["/Names"]["/EmbeddedFiles"]["/Names"]
for i in range(0, len(noms), 2):
    fs = noms[i + 1].get_object()
    ef = fs["/EF"]["/F"].get_object()
    print(f"{L['nom']} {fs['/F']}")
    print(f"AFRelationship{L['sep']} {fs['/AFRelationship']}")
    print(f"Subtype{L['sep']} {ef['/Subtype']}")
    print(L["taille"].format(len(ef.get_data())))
print(L["af"].format(len(cat['/AF'].get_object())))
oi = cat["/OutputIntents"][0].get_object()
print(f"{L['oi']} {oi['/S']} {oi['/OutputConditionIdentifier']}")

print(L["xmp"])
xmp = cat["/Metadata"].get_object().get_data().decode()
for balise in ["pdfaid:part", "pdfaid:conformance", "fx:DocumentType", "fx:DocumentFileName",
               "fx:Version", "fx:ConformanceLevel"]:
    m = re.search(rf"<{balise}>(.*?)</{balise}>", xmp)
    print(f"{balise} = {m.group(1) if m else L['absent']}")
