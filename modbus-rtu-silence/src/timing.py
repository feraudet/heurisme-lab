"""t1.5 and t3.5 by baud rate: 11 bits per character; above 19200, fixed values (V1.02, 2.5.1.1)."""
print(f"{'bauds':>7}  {'caractère':>10}  {'t1.5':>8}  {'t3.5':>8}")
for baud in (9600, 19200, 38400, 115200):
    tc = 11 / baud * 1e6
    t15, t35 = (1.5 * tc, 3.5 * tc) if baud <= 19200 else (750, 1750)
    fixe = "" if baud <= 19200 else "  (fixe)"
    print(f"{baud:>7}  {tc:>7.0f} us  {t15:>5.0f} us  {t35:>5.0f} us{fixe}")
