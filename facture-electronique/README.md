# An electronic invoice, seen from the inside

The bench of the deck https://heurisme.fr/en/blog/facture-electronique/ : we build a Factur-X PDF (PDF/A-3b with an attached CII XML), validate it with Mustang, falsify it in three ways, then remove the electronic address and the color profile to see what the validator says.

File and folder names and part of the outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `banc/` = bench, `sortie/` = output, `1-generer.sh` = generate, `2-valider.sh` = validate, `3-fausser.sh` = falsify, `5-inspecter.sh` = inspect, `6-profils.sh` = profiles, `7-sans-adresse.sh` = without address, `8-sans-profil.sh` = without color profile, `couches.py` = layers, `champs.py` = fields, `visuel.py` = visual part of the invoice, `tout.sh` = run everything, `faux-total` = wrong total, `faux-tva` = wrong VAT, `faux-centimes` = wrong cents, `journal` = log. Files ending in `-en.txt` are the English outputs.

## How to replay

- Docker (tested with 29.4.2), `curl`, `shasum`.
- Image `fx-py`: `python:3.12-slim`, Ghostscript, fonts-dejavu-core, factur-x 5.0, reportlab, saxonche (PyPI packages published before 2026-06-30).
- Image `fx-mustang`: `eclipse-temurin:21-jre` and Mustang CLI 2.24.0.

Single command:

```bash
bash rejouer.sh
```

It downloads Mustang (sha256 checked), builds the two images, empties `banc/sortie/` and replays steps 1 to 8. The timestamps in the logs are those of the day of the run.

## Bench data

Everything is fictitious: seller "Atelier Fictif SAS" and buyer "Client Exemple SARL", SIREN `000000018` and `000000026` (valid for the Luhn check, absent from the Recherche d'entreprises API on 12/10/2026), IBAN made of zeros, invoice number `FX-2026-0042`. The PDFs in `banc/sortie/` contain only this data and can be published.

## File to slide

| File | Slides |
|---|---|
| `banc/1-generer.sh` (`visuel.py`, `pdfa-def.ps`, `factur-x.xml`) → `banc/sortie/1-generer.txt`, `facture.pdf` | 4 |
| `banc/2-valider.sh` → `banc/sortie/2-valider.txt`, `facture.journal.txt` | 4, 7 |
| `banc/3-fausser.sh` → `banc/sortie/3-fausser.txt`, `faux-*.pdf`, `faux-*.xml` | 8 to 10 |
| `banc/sortie/4-valider-faux-total.txt`, `4-valider-faux-tva.txt`, `4-valider-faux-centimes.txt` (and `faux-*.journal.txt`) | 8 to 10 |
| `banc/5-inspecter.sh` (`couches.py`, `champs.py`) → `banc/sortie/5-inspecter.txt`, `5-inspecter-en.txt` | 4 to 6 |
| `banc/6-profils.sh` (`profils.py`) → `banc/sortie/6-profils.txt`, `6-profils-en.txt` | 6 |
| `banc/7-sans-adresse.sh` → `banc/sortie/7-valider-sans-adresse.txt` | 7 |
| `banc/8-sans-profil.sh` → `banc/sortie/8-valider-sans-profil.txt` | 7 |
| `banc/tout.sh` | chains the steps |

## Third-party data (downloaded by `banc/tout.sh`, never copied here)

- Mustang CLI 2.24.0 (Apache 2.0): https://repo1.maven.org/maven2/org/mustangproject/Mustang-CLI/2.24.0/Mustang-CLI-2.24.0.jar, sha256 `e4904ffa0afdce3f5836dceb927c440a05ed5d60386fdd37e17a4b2f7652edbf`.
- Debian and PyPI packages and Docker images: official repositories.
- Regulatory sources cited by the deck, not copied: pages and PDFs from https://www.impots.gouv.fr (FAQ, practical guide, reform calendar, page "Facturation électronique et plateformes agréées").
