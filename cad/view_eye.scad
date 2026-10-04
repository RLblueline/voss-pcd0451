// Eye mechanism close-up (head frame). Rear plate hidden; bezel shown as a ghost.
include <memo.scad>
SHUT = 0.5;
intersection() { eye_cartridge(); translate([7.6, -100, -300]) cube([BEZEL_X - 2 - 7.6, 200, 400]); }
color([0.2, 0.2, 0.2, 0.25]) translate([BEZEL_X - 2, -EYE_Y - 6, EYE_Z0 - 6]) cube([2, 2 * EYE_Y + 12, EYE_Z1 - EYE_Z0 + 12]);
shutter_top(SHUT); shutter_bottom(SHUT); shutter_drive(SHUT);
