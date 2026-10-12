#!/bin/sh
# Step 3, in the fx-py image: three deliberately wrong versions of the same XML.
#  A: gross total that does not add up (2,922.00 instead of 2,922.20).
#  B: VAT wrongly split, the 5.5% line taxed at 20% (8.00 instead of 2.20), totals adjusted so that the sum adds up.
#  C: 5.5% VAT off by only 0.20 EUR (2.00 instead of 2.20), totals adjusted.
# Run from banc/: docker run --rm -v "$PWD":/banc fx-py sh 3-fausser.sh
mkdir -p sortie
sed -e 's|<ram:GrandTotalAmount>2922.20<|<ram:GrandTotalAmount>2922.00<|' \
    -e 's|<ram:DuePayableAmount>2922.20<|<ram:DuePayableAmount>2922.00<|' \
    factur-x.xml > sortie/faux-total.xml
sed -e 's|<ram:CalculatedAmount>2.20<|<ram:CalculatedAmount>2.00<|' \
    -e 's|<ram:TaxTotalAmount currencyID="EUR">482.20<|<ram:TaxTotalAmount currencyID="EUR">482.00<|' \
    -e 's|<ram:GrandTotalAmount>2922.20<|<ram:GrandTotalAmount>2922.00<|' \
    -e 's|<ram:DuePayableAmount>2922.20<|<ram:DuePayableAmount>2922.00<|' \
    factur-x.xml > sortie/faux-centimes.xml
sed -e 's|<ram:CalculatedAmount>2.20<|<ram:CalculatedAmount>8.00<|' \
    -e 's|<ram:TaxTotalAmount currencyID="EUR">482.20<|<ram:TaxTotalAmount currencyID="EUR">488.00<|' \
    -e 's|<ram:GrandTotalAmount>2922.20<|<ram:GrandTotalAmount>2928.00<|' \
    -e 's|<ram:DuePayableAmount>2922.20<|<ram:DuePayableAmount>2928.00<|' \
    factur-x.xml > sortie/faux-tva.xml
cd sortie
echo '$ diff factur-x.xml faux-total.xml'
diff ../factur-x.xml faux-total.xml
echo '$ diff factur-x.xml faux-tva.xml'
diff ../factur-x.xml faux-tva.xml
echo '$ diff factur-x.xml faux-centimes.xml'
diff ../factur-x.xml faux-centimes.xml
echo
for v in faux-total faux-tva faux-centimes; do
  echo "\$ facturx-pdfgen -w visuel-pdfa.pdf $v.xml $v.pdf"
  facturx-pdfgen -w visuel-pdfa.pdf $v.xml $v.pdf 2>&1
  echo "[exit $?]"
  # same thing without the library's Schematron check, to get the wrong PDF
  facturx-pdfgen -w -ds visuel-pdfa.pdf $v.xml $v.pdf > $v.pdfgen-ds.txt 2>&1
done
