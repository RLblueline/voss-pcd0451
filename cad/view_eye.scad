// Eye mechanism close-up (shell frame): fixed slotted plate as a ghost, carriage, shutters, lift drive.
include <voss.scad>
SHUT = 0.5; EYE = 0;
ze = EYE_Z + EYE * EYE_TRAVEL;
color([0.2, 0.2, 0.2, 0.25]) eye_plate();
eye_rods(); lift_drive(ze); eye_carriage(ze);
shutter_top(SHUT, ze); shutter_bottom(SHUT, ze); shutter_drive(SHUT, ze);
