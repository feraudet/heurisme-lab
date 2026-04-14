"""Float additions are not associative: the order changes the result.
usage: python3 flottants.py [--lang en]"""
import random, sys
import numpy as np

en = "--lang" in sys.argv and sys.argv[sys.argv.index("--lang") + 1] == "en"
L = (["float16, 4096 values, left to right       :", "float16, same values, right to left      :",
      "float16, blocks of 256, then the total   :", "float64, reference                       :"] if en else
     ["float16, 4096 valeurs, de gauche à droite :", "float16, mêmes valeurs, de droite à gauche :",
      "float16, par blocs de 256 puis total      :", "float64, référence                        :"])

print("(0.1 + 0.2) + 0.3 =", repr((0.1 + 0.2) + 0.3))
print("0.1 + (0.2 + 0.3) =", repr(0.1 + (0.2 + 0.3)))

random.seed(0)
x = np.array([random.gauss(0, 1) for _ in range(4096)], dtype=np.float16)
def somme(v):
    s = np.float16(0)
    for e in v: s = np.float16(s + e)
    return s
L = [l.rstrip(" :").ljust(max(len(x.rstrip(" :")) for x in L)) + " :" for l in L]
print(L[0], repr(float(somme(x))))
print(L[1], repr(float(somme(x[::-1]))))
print(L[2], repr(float(somme([somme(x[i:i + 256]) for i in range(0, 4096, 256)]))))
print(L[3], repr(float(np.sum(x.astype(np.float64)))))
