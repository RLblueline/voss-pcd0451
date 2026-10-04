# 2. Hardware

## Bill of materials

Prices are rough, typical online prices (USD, late 2026) and will vary.

| Qty | Part | Notes | ~$ |
|---|---|---|---|
| 1 | Raspberry Pi Zero 2 W | with header | 15 |
| 1 | microSD 32 GB | | 7 |
| 2 | INMP441 I2S MEMS mic | 80 mm apart for direction of arrival | 6 |
| 1 | MAX98357A I2S amp | | 5 |
| 1 | 40 mm 4 Ω 3 W speaker | | 3 |
| 1 | PCA9685 16-ch servo driver | OE pin wired to GPIO17 | 6 |
| 2 | MG996R servo | shoulder, elbow | 12 |
| 1 | DS3218 servo (20 kg·cm, 180°) | head tilt | 14 |
| 1 | SG90 servo | eye shutters | 3 |
| 1 | WS2812B 16-LED ring, 44 mm OD | behind the lens | 5 |
| 3 | WS2812B single-LED boards | REC / AUD / OK | 4 |
| 1 | 58 mm TTL thermal printer module + paper | 9600 baud ESC/POS | 25 |
| 1 | 5 V 5 A supply | Pi, amp, LEDs, printer | 12 |
| 1 | 6 V 5 A+ supply | servo rail only | 13 |
| 2 | 608 bearing (8×22×7) | shoulder and elbow pivots | 2 |
| 1 | 624 bearing (4×13×5) | tilt pivot | 1 |
| — | M8×30 bolts ×2, M4×20 + nyloc, M3 screws, M3 heat-set inserts | | 8 |
| — | 1000 µF 10 V cap, 330 Ω resistor, 2 DC jacks, wire | | 5 |
| — | Filament: ~1.0 kg beige PLA/PETG, charcoal, grey, a little TPU and translucent amber | plan 1.5 kg with reprints | 25–35 |
| (opt) | 74AHCT125 level shifter | only if LEDs glitch | 2 |

**Total: about $175–185 at list prices.** It comes to about $145–155 if you already have
the microSD card, wire and filament on hand. The biggest cost levers are:
- the printer (about $25),
- using one 6 V 10 A supply plus a 5 V buck converter instead of two bricks,
- buying servos in multi-packs.

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
- **Do not use GPIO16.** The `googlevoicehat-soundcard` overlay claims it.
- **PCA9685 channels:** 0 shoulder, 1 elbow, 2 tilt, 3 shutter.

## Power

```
5 V 5 A ──┬── Pi Zero 2 W (5 V pins)
          ├── MAX98357A VIN
          ├── WS2812 chain (19 LEDs)
          └── thermal printer
6 V 5 A ──┬── PCA9685 V+ (servo rail) ── 1000 µF across V+/GND
          └── (nothing else)
GND ─────── common to both supplies, the Pi and the PCA9685
```

- **Servo current:** the MG996R and DS3218 can each pull 2 A or more at stall, which is
  why they get their own rail.
- **Printing:** the firmware never prints while the arm moves. It also cuts servo
  outputs through OE during printing and at rest.

## Pin budget left

GPIO 4, 5, 6, 12, 13, 22–27 are free, which is useful for a future button or a
Home Assistant status LED.
