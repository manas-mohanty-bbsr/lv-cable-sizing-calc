# Verification

Four worked examples, two for each code, are checked by `tests/test_worked_examples.py` on every push.
Each case was sized by hand from IS 732:2019 before the tool was run, and the expected values were
written from the hand calculation, never from the tool's output. The tool then had to reproduce every
figure within 0.5 %.

| File | Case | Size | Governing check | Worked by | Checked by | Date |
|---|---|---|---|---|---|---|
| `WE-IEC-1.json` | Motor feeder, Cu PVC, method C, 415 V 3-phase | 25 mm2 | Short-circuit withstand | Hand calculation from IS 732:2019 | Manas Mohanty | 21 Sep 2026 |
| `WE-IEC-2.json` | Distribution board feeder, Al XLPE, method E, 400 V 3-phase | 120 mm2 | Current-carrying capacity | Hand calculation from IS 732:2019 | Manas Mohanty | 21 Sep 2026 |
| `WE-IS-1.json` | Lighting circuit, Cu PVC, method B1, 230 V single-phase | 6 mm2 | Voltage drop | Hand calculation from IS 732:2019 | Manas Mohanty | 21 Sep 2026 |
| `WE-IS-2.json` | Buried feeder, Cu XLPE, method D2, 415 V 3-phase | 50 mm2 | Current-carrying capacity | Hand calculation from IS 732:2019 | Manas Mohanty | 21 Sep 2026 |

All three checks (current-carrying capacity, voltage drop, short-circuit withstand) are exercised, and
each of them governs at least one case.

## Statement

I ran the four worked examples through the tool myself on 22 September 2026. For every case the size,
the governing check and each figure matched the hand calculation made to IS 732:2019, which I had
reviewed and accepted. I find the tool useful where a design has many feeders to size, because each
result can be checked line by line against the code.

Manas Mohanty
