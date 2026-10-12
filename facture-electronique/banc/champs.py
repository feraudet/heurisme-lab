"""Extracts factur-x.xml from a PDF and displays the key fields with their EN 16931 number (BT-xx).
Usage: python champs.py [--en] facture.pdf   (--en: English labels)
"""
import sys

from facturx import get_xml_from_pdf
from lxml import etree

EN = "--en" in sys.argv
args = [a for a in sys.argv[1:] if a != "--en"]


def tr(fr, en):
    return en if EN else fr


nom, xml = get_xml_from_pdf(open(args[0], "rb").read(), check_xsd=False, check_schematron=False)
print(tr(f"extrait : {nom}, {len(xml)} octets", f"extracted: {nom}, {len(xml)} bytes"))
t = etree.fromstring(xml)
ns = {"rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
      "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
      "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100"}
A = "rsm:SupplyChainTradeTransaction/ram:ApplicableHeaderTradeAgreement/"
S = "rsm:SupplyChainTradeTransaction/ram:ApplicableHeaderTradeSettlement/"
M = S + "ram:SpecifiedTradeSettlementHeaderMonetarySummation/"
champs = [
    ("BT-24", tr("profil", "profile"), "rsm:ExchangedDocumentContext/ram:GuidelineSpecifiedDocumentContextParameter/ram:ID"),
    ("BT-1", tr("numéro", "number"), "rsm:ExchangedDocument/ram:ID"),
    ("BT-3", tr("type (380 = facture)", "type (380 = invoice)"), "rsm:ExchangedDocument/ram:TypeCode"),
    ("BT-2", tr("date", "date"), "rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString"),
    ("BT-27", tr("vendeur", "seller"), A + "ram:SellerTradeParty/ram:Name"),
    ("BT-30", tr("SIREN vendeur", "seller SIREN"), A + "ram:SellerTradeParty/ram:SpecifiedLegalOrganization/ram:ID"),
    ("BT-31", tr("TVA vendeur", "seller VAT number"), A + "ram:SellerTradeParty/ram:SpecifiedTaxRegistration/ram:ID"),
    ("BT-34", tr("adresse électronique vendeur", "seller electronic address"), A + "ram:SellerTradeParty/ram:URIUniversalCommunication/ram:URIID"),
    ("BT-44", tr("acheteur", "buyer"), A + "ram:BuyerTradeParty/ram:Name"),
    ("BT-47", tr("SIREN acheteur", "buyer SIREN"), A + "ram:BuyerTradeParty/ram:SpecifiedLegalOrganization/ram:ID"),
    ("BT-48", tr("TVA acheteur", "buyer VAT number"), A + "ram:BuyerTradeParty/ram:SpecifiedTaxRegistration/ram:ID"),
    ("BT-49", tr("adresse électronique acheteur", "buyer electronic address"), A + "ram:BuyerTradeParty/ram:URIUniversalCommunication/ram:URIID"),
]
for bt, lib, xp in champs:
    for n in t.xpath(xp, namespaces=ns):
        sch = n.get("schemeID")
        print(f"{bt:6} {lib:31} {n.text}" + (f"  (schemeID {sch})" if sch else ""))
for li in t.xpath("rsm:SupplyChainTradeTransaction/ram:IncludedSupplyChainTradeLineItem", namespaces=ns):
    g = lambda xp: li.xpath(xp, namespaces=ns)[0].text
    num = g('ram:AssociatedDocumentLineDocument/ram:LineID')
    print(tr(f"ligne {num} : ", f"line {num}: ") + f"{g('ram:SpecifiedTradeProduct/ram:Name')}, "
          f"{g('ram:SpecifiedLineTradeDelivery/ram:BilledQuantity')} x "
          f"{g('ram:SpecifiedLineTradeAgreement/ram:NetPriceProductTradePrice/ram:ChargeAmount')} = "
          f"{g('ram:SpecifiedLineTradeSettlement/ram:SpecifiedTradeSettlementLineMonetarySummation/ram:LineTotalAmount')}"
          + tr(" HT, TVA ", " excl. VAT, VAT ")
          + f"{g('ram:SpecifiedLineTradeSettlement/ram:ApplicableTradeTax/ram:RateApplicablePercent')} %")
for tx in t.xpath(S + "ram:ApplicableTradeTax", namespaces=ns):
    g = lambda xp: tx.xpath(xp, namespaces=ns)[0].text
    print(tr(f"BG-23  TVA {g('ram:RateApplicablePercent'):>5} % : base {g('ram:BasisAmount')}, montant {g('ram:CalculatedAmount')}",
             f"BG-23  VAT {g('ram:RateApplicablePercent'):>5} %: basis {g('ram:BasisAmount')}, amount {g('ram:CalculatedAmount')}"))
for bt, lib, el in [("BT-106", tr("somme des lignes", "sum of lines"), "LineTotalAmount"),
                    ("BT-109", tr("total HT", "total excl. VAT"), "TaxBasisTotalAmount"),
                    ("BT-110", tr("total TVA", "total VAT"), "TaxTotalAmount"),
                    ("BT-112", tr("total TTC", "total incl. VAT"), "GrandTotalAmount"),
                    ("BT-115", tr("à payer", "amount due"), "DuePayableAmount")]:
    print(f"{bt:6} {lib:31} {t.xpath(M + 'ram:' + el, namespaces=ns)[0].text}")
for n in t.xpath("rsm:ExchangedDocument/ram:IncludedNote", namespaces=ns):
    print(f"BT-21  note {n.find('ram:SubjectCode', ns).text}{tr(' :', ':')} {n.find('ram:Content', ns).text}")
