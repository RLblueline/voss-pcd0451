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
| 1 | MG996R servo | base yaw | 6 |
| 1 | 35 kg·cm standard-size servo, 180° (DS3235 class) | shoulder | 20 |
| 2 | DS3218 servo (20 kg·cm, 180°) | elbow, head tilt | 28 |
| 1 | SG90 servo | eye shutters | 3 |
| 1 | WS2812B 16-LED ring, 44 mm OD | behind the lens | 5 |
| 3 | WS2812B single-LED boards | REC / AUD / OK | 4 |
| 1 | 58 mm TTL thermal printer module + paper | 9600 baud ESC/POS | 25 |
| 1 | 5 V 5 A supply | Pi, amp, LEDs, printer | 12 |
| 1 | 6 V 10 A supply | servo rail only | 18 |
| 2 | 608 bearing (8×22×7) | yaw shaft | 2 |
| 3 | 624 bearing (4×13×5) | shoulder, elbow, tilt pivots | 2 |
| 1 | 8 mm steel rod, 75 mm | yaw shaft | 3 |
| — | M4×20 shoulder bolts ×3 + nylocs, M3 screws, M3 heat-set inserts | | 8 |
| (rec.) | Tension spring, about 10 kg·cm at the shoulder | counterbalance, see [Mechanical → Known risks](03-mechanical.md#known-risks) | 3 |
| — | 1000 µF 10 V cap, 330 Ω resistor, 2 DC jacks, wire | | 5 |
| — | Filament: ~1.0 kg beige PLA/PETG, charcoal, grey, a little TPU and translucent amber | plan 1.5 kg with reprints | 25–35 |
| (opt) | 74AHCT125 level shifter | only if LEDs glitch | 2 |

**Total: about $210–220 at list prices.** It comes to about $180–190 if you already have
the microSD card, wire and filament on hand. The classic arm adds about $35 over the
v0.3 fold-flat arm, mostly for the 35 kg·cm shoulder servo, the second DS3218 and a
bigger servo supply.

Cost levers:
- the printer (about $25)
- one 6 V 10 A supply plus a 5 V buck converter instead of two bricks
- servo multi-packs
- a counterbalance spring, which would let a DS3218 replace the 35 kg·cm shoulder servo (about −$6)

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
- **PCA9685 channels:** 0 yaw, 1 shoulder, 2 elbow, 3 tilt, 4 shutter.

## Power

```
5 V 5 A ──┬── Pi Zero 2 W (5 V pins)
          ├── MAX98357A VIN
          ├── WS2812 chain (19 LEDs)
          └── thermal printer
6 V 10 A ─┬── PCA9685 V+ (servo rail) ── 1000 µF across V+/GND
          └── (nothing else)
GND ─────── common to both supplies, the Pi and the PCA9685
```

- **Servo current:** the shoulder and elbow hold the arm all the time, and each servo can
  pull 2–3 A at stall. That's why they get their own 10 A rail.
- **Printing:** the firmware never prints while the arm moves. The joints keep holding
  during printing; the separate rail means the printer can't brown them out.
- **Shutdown:** OE is only cut on shutdown, after the arm has been lowered to its stop.

## Pin budget left

GPIO 4, 5, 6, 12, 13, 22–27 are free, which is useful for a future button or a
Home Assistant status LED.
