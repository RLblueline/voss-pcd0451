# 2. Hardware

## Bill of materials

Prices are rough, typical online prices (USD, late 2026).

| Qty | Part | Use | ~$ |
|---|---|---|---|
| 1 | Raspberry Pi Zero 2 W (with header) | brain | 15 |
| 1 | microSD 32 GB | | 7 |
| 2 | INMP441 I2S MEMS mic | 80 mm apart for direction of arrival | 6 |
| 1 | MAX98357A I2S amp + 40 mm 4 Ω 3 W speaker | voice | 8 |
| 1 | PCA9685 16-ch servo driver | OE wired to GPIO17 | 6 |
| 1 | MG996R | base yaw | 6 |
| 2 | DS3225 (25 kg·cm, standard size, 180°) | shoulder, elbow | 32 |
| 1 | DS3218 (20 kg·cm, 180°) | head tilt | 14 |
| 2 | SG90 | eyelids, eye lift | 6 |
| 1 | WS2812B 16-LED ring (44 mm OD) + 3 single WS2812B boards | eye, REC/AUD/OK | 9 |
| 1 | 58 mm TTL thermal printer + paper | memos | 25 |
| 1 | 5 V 5 A supply | Pi, amp, LEDs, printer | 12 |
| 1 | 6 V 6 A supply | servo rail | 15 |
| 2 | 608 bearings + 75 mm × 8 mm steel rod | yaw shaft | 5 |
| 3 | 624 bearings + M4 × 20 shoulder bolts | shoulder, elbow, tilt pivots | 4 |
| 2 | 3 mm steel rod, 150 mm | eye carriage guides | 2 |
| 1 | Extension spring ~0.8 N/mm, ~40 mm free length, ≥75 mm travel, ~20 N initial tension; 1 mm braided cable; 2 small pulleys | shoulder counterbalance | 6 |
| — | Split-loom tubing (6–8 mm), zip ties, servo extension leads, 22–26 AWG wire | harness and service tubes | 8 |
| — | M3 screws + heat-set inserts, M4 nylocs | | 6 |
| — | 1000 µF cap, 330 Ω resistor, 2 DC jacks | | 3 |
| — | Filament: ~1.3 kg beige PLA/PETG, charcoal, grey, TPU, translucent amber | plan 1.5–2 kg with reprints | 30–40 |
| (opt) | 74AHCT125 level shifter | only if LEDs glitch | 2 |

**Total: about $220–235 at list prices, or about $190–200 if you already have the SD
card, wire and filament.**

Where the money goes compared with the classic arm (v0.4):
- The **desk-lamp spring** saves about $5–8. The DS3225s replace the 35 kg·cm servo, and
  a 6 A supply replaces the 10 A one.
- The new **eye lift** (SG90), the **harness and tubes**, and the bigger head's filament
  add about $15–20.

Cost levers:
- the printer (about $25)
- one 6 V supply plus a 5 V buck converter
- servo multi-packs
- 1.6 mm head walls (less filament, lighter head)

## Wiring

| Signal | Pi Zero 2 W pin | Goes to |
|---|---|---|
| I2S BCLK | GPIO18 | both INMP441 SCK, MAX98357A BCLK |
| I2S LRCLK | GPIO19 | both INMP441 WS, MAX98357A LRC |
| Mic data | GPIO20 | both INMP441 SD |
| Amp data | GPIO21 | MAX98357A DIN |
| I2C SDA / SCL | GPIO2 / GPIO3 | PCA9685 |
| Servo output enable | GPIO17 | PCA9685 OE (active low) |
| LED data | GPIO10 (SPI0 MOSI) | 330 Ω → eye ring DIN → REC → AUD → OK |
| Printer | GPIO14 (UART TX) | printer RX |

- **Mics:** left mic L/R → GND (channel 0, at −X); right mic L/R → 3.3 V (channel 1, at +X).
- **Don't use GPIO16:** the voicehat overlay claims it.
- **PCA9685 channels:** 0 yaw, 1 shoulder, 2 elbow, 3 tilt, 4 eyelids, 5 eye lift.

### Harness

One bundle runs from the housing up through the yaw tower's cable hole, then:
1. through a corrugated service loop to the turret
2. along the top of link1 under its cover
3. over the elbow in a second service loop
4. along the top of link2 under its cover
5. down into the open back of the head through two neck tubes

It carries:
- 4 servo leads: elbow, tilt, eyelids, eye lift (the yaw and shoulder servos sit at the base)
- the LED data/5 V/GND line for the eye ring and status bar

Leave about 30 mm of slack at each loop for the full joint range.

## Power

```
5 V 5 A ──┬── Pi Zero 2 W (5 V pins)
          ├── MAX98357A VIN
          ├── WS2812 chain (19 LEDs)
          └── thermal printer
6 V 6 A ──┬── PCA9685 V+ (servo rail) ── 1000 µF across V+/GND
          └── (nothing else)
GND ─────── common to both supplies, the Pi and the PCA9685
```

- **Holding current:** the counterbalance spring keeps steady holding current low. The
  6 A supply covers several servos moving at once with margin.
- **Printing:** the firmware never prints while the arm moves. The joints keep holding;
  the separate rail means the printer can't brown them out.
- **Shutdown:** the arm parks at the spring's balance point before OE cuts power, so it
  barely drifts.

## Free pins

GPIO 4, 5, 6, 12, 13 and 22–27 are free, which is handy for a button or a Home Assistant
status LED.
