"""Draws the readable part of the fictitious invoice (what a human reads), embedded font.
Usage: python visuel.py sortie.pdf
"""
import sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

c = canvas.Canvas(sys.argv[1], pagesize=A4, invariant=1)
c.setTitle("Facture FX-2026-0042 (fictive)")
c.setAuthor("Atelier Fictif SAS")
W, H = A4
y = H - 60
c.setFont("DVB", 18); c.drawString(50, y, "FACTURE FX-2026-0042")
c.setFont("DV", 9); c.drawRightString(W - 50, y, "Document de test entièrement fictif")
y -= 22
c.setFont("DV", 10)
c.drawString(50, y, "Date : 15/06/2026    Livraison : 12/06/2026    Échéance : 15/07/2026")
y -= 34
for x, titre, lignes in [
    (50, "Vendeur", ["Atelier Fictif SAS", "1 rue de l'Exemple", "75000 Paris", "SIREN 000 000 018", "TVA FR66000000018"]),
    (320, "Acheteur", ["Client Exemple SARL", "2 avenue du Test", "69000 Lyon", "SIREN 000 000 026", "TVA FR90000000026"]),
]:
    c.setFont("DVB", 11); c.drawString(x, y, titre)
    c.setFont("DV", 10)
    for k, l in enumerate(lignes):
        c.drawString(x, y - 15 * (k + 1), l)
y -= 110
c.setFont("DVB", 10)
cols = [50, 300, 360, 430, 490]
for x, t in zip(cols, ["Désignation", "Qté", "PU HT", "TVA", "Total HT"]):
    c.drawString(x, y, t)
c.line(50, y - 4, W - 50, y - 4)
c.setFont("DV", 10)
for ligne in [("Conseil technique (jour)", "3", "800,00", "20 %", "2 400,00"),
              ("Guide technique imprimé", "1", "40,00", "5,5 %", "40,00")]:
    y -= 18
    for x, t in zip(cols, ligne):
        c.drawString(x, y, t)
y -= 30
for lib, val in [("Total HT", "2 440,00 €"), ("TVA 20 % sur 2 400,00", "480,00 €"),
                 ("TVA 5,5 % sur 40,00", "2,20 €"), ("Total TTC", "2 922,20 €")]:
    c.setFont("DVB" if lib == "Total TTC" else "DV", 10)
    c.drawString(330, y, lib); c.drawRightString(W - 50, y, val); y -= 16
y -= 20
c.setFont("DV", 9)
for l in ["Paiement par virement à 30 jours. IBAN FR76 0000 0000 0000 0000 0000 097 (fictif).",
          "Pénalités de retard : trois fois le taux d'intérêt légal.",
          "Indemnité forfaitaire pour frais de recouvrement : 40 euros. Pas d'escompte pour paiement anticipé."]:
    c.drawString(50, y, l); y -= 13
c.showPage(); c.save()
