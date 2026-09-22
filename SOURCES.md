# Sources of the shipped tables

Every number the calculator uses comes from a CSV file in `src/cablecalc/data/`, and every row of every
file names its source. This page records where those values were read, how they were checked, and what
the tool therefore covers. No value was typed from memory.

Provenance grades: **A** = read from the primary text itself; **B** = read from a reputable source that
names and reproduces the primary.

## What was read

| Code | Document held | Grade |
|---|---|---|
| IS | IS 732:2019, *Code of Practice for Electrical Wiring Installations* (Fourth Revision), BIS, full text | A |
| IEC | IEC 60364-5-52:2009 is **not** held. IS 732:2019 states that it is "largely based on" IEC 60364-5-52:2009, and its Annex S tables reproduce that standard's Annex B tables. The IEC values are therefore cited *as reproduced in IS 732:2019*. | B |

A 22-page third-party summary of IEC 60364-5-52:2009 was also available. It reproduces some of the IEC
tables as images. Wherever it carries a table, that table was compared with IS 732 cell by cell, and
every cell agreed. The summary is used only as that cross-check; no value is taken from it.

The standards themselves are copyright documents and are not included in this repository.

## Table by table

| File | IS 732:2019 | IEC 60364-5-52:2009 | Read | Cross-checked against |
|---|---|---|---|---|
| `ampacity.csv` methods A1-D2 | Tables 21, 22, 23, 24 | B.52.2, B.52.3, B.52.4, B.52.5 | IS text layer, by position | Page images; IEC images for B.52.2, .4, .5 |
| `ampacity.csv` method E | Tables 29, 30, 31, 32, columns 2 and 3 | B.52.10, B.52.11, B.52.12, B.52.13 | IS text layer, by position | Page images; IEC images for B.52.12, .13 |
| `temp_factor.csv` air | Table 33 | B.52.14 | IS text and page image | IEC image |
| `temp_factor.csv` ground | Table 34 | B.52.15 | IS text and page image | IEC image |
| `soil_factor.csv` | Table 35 | B.52.16 | IS text and page image | - |
| `group_factor.csv` | Tables 36, 37, 38 (A); clause S-4.1 | B.52.17, B.52.18, B.52.19 (A) | IS text and page images | IEC images |
| `k_factor.csv` | Table 3 | IEC 60364-4-43:2008, as reproduced in IS 732 Table 3 | IS text | - |
| `impedance.csv` | Annex Y (method) | Annex G (method) | IS text | IEC summary quotes the same formula and the 0.08 mohm/m reactance |

The IEC numbers B.52.3, B.52.10, B.52.11 and B.52.16 were not seen in any document. They follow from the
numbering, which holds for every table where both numbers were seen (IS Table *n* = IEC Table
B.52.(*n* - 19)). Their source strings say so.

**The installation method codes are the same in both standards.** IS 732 Table 19 was compared item by
item with IEC Table A.52.3 as reproduced in the summary (items 1 to 72): every item carries the same
description and the same reference method (A1, A2, B1, B2, C, D1, D2, E, F or G). IS Table 20 = IEC
Table B.52.1, and the ampacity tables of both head their columns with the same codes. The short method
descriptions in the template's Guide sheet are taken from IS 732 Tables 19 and 20 and clause S-6.1.
One difference in print only: IS Table 19 goes from item 71 to item 73 and leaves out item 72
(sheathed cable direct in the ground, without added mechanical protection), which IEC Table A.52.3 lists
as D2. IS Table 18 still refers to item 72, and both items use D2, so no value changes.

A second, independent extraction of the three-loaded-conductor values (methods C, D1, D2 and E, copper
and aluminium, 248 cells) made earlier from the same page images agreed with this one in every cell.

## Two things the standard prescribes that shape the tables

**Conductor resistance is not taken from a resistance table.** IS 732 Annex Y (and IEC 60364-5-52
Annex G) calculate voltage drop from a resistivity of 0.0225 ohm.mm2/m for copper and 0.036 ohm.mm2/m
for aluminium, which is 1.25 times the value at 20 deg C, and a reactance of 0.08 mohm/m. `impedance.csv`
holds R = resistivity / S and X = 0.08 ohm/km for every size, as that method instructs. It is the
standard's own simplification, and it does not vary with insulation. The engine's voltage-drop formula
is the same one: for three-phase circuits, sqrt(3) x I x Z on the line voltage equals Annex Y's I x Z on
the phase voltage.

**One circuit takes no group reduction.** Tables 37 and 38 start at two circuits. Clause S-4.1 states that
the tabulated capacities relate to a single circuit, so the one-circuit row for D1 and D2 is 1.00 and cites
that clause.

## What version 1 covers

- Conductors: copper and aluminium. Insulation: PVC (70 deg C) and XLPE (90 deg C).
- The input names the cable construction (`2 x 1C`, `3 x 1C`, `4 x 1C`, `2C`, `3C`, `3.5C`, `4C`). The
  tables' `cores` column is the number of **loaded** conductors, and the tool derives it from the phase:
  2 for single-phase, 3 for three-phase. IS 732 clause 5.2.6.6.1: where polyphase currents are balanced
  the neutral need not be taken into consideration, and a four-core cable is given the same rating as a
  three-core cable of the same size; so 3.5C and 4C use the three-loaded-conductor column. Harmonic
  neutral current (Annex V, Table 45) is not covered.
- Single-core cables are refused in method E (single-core in free air is methods F and G, IS 732 Table 19
  items 31 to 33) and in method A2 (multi-core only, Table 19 item 2; single-core is item 1, method A1).
- Installation methods: A1, A2, B1, B2, C, E (multi-core), D1 (multi-core cables in ducts in the ground) and
  D2 (direct in the ground).
- Sizes: copper 1.5 to 300 mm2; aluminium 2.5 to 300 mm2. For D2 in aluminium the standard gives no rating
  below 16 mm2, so none is offered.
- Grouping: A1 to B2 use Table 36 item 1 (bunched or enclosed, up to 20 circuits); C uses item 2 (single
  layer on a wall, up to 9); E uses item 4 (single layer on perforated tray, up to 9); D2 and D1 use the
  touching column of Tables 37 and 38 A. **Buried cables are always taken as touching, which is the worst
  case.**
- Soil thermal resistivity (D1, D2): 0.5 to 3 K.m/W; the default is the reference value 2.5.

## Not covered, and why

- Single-core cables in methods F and G, and sizes above 300 mm2: these need the cable formation, which
  the engine does not yet model.
- Mineral-insulated cables (Tables 25 to 28).
- Buried spacings other than touching.
- More than 9 circuits for C or E: Table 36 says there is no further reduction beyond nine, but that rule
  is not applied yet, so such inputs are refused rather than guessed.
- Harmonic currents (Annex V) and cables exposed to solar radiation (the correction factors exclude it).

## One oddity in the source, recorded

Table 37 (IEC B.52.18), 16 circuits at 0.5 m spacing, reads 0.38 between 0.71 (12 circuits) and 0.66 (20
circuits). Both IS 732:2019 and the IEC 2009 table print it this way. The tool does not use that column.
