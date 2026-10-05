// Single-part export for printing and collision checks (each part in its own local frame).
//   openscad -D 'PART="link1"' -o link1.stl tools/parts.scad
// Cosmetic-only geometry (screw heads, inlays, labels) is left out.
include <../voss.scad>
COSMETIC = false;
PART = "link1"; S = 1; PE = 0;
ZE = EYE_Z + PE * EYE_TRAVEL;

// ---- world frame
if (PART == "housing")     housing_shell();
if (PART == "back_plate")  back_plate();
if (PART == "tower")       yaw_tower();
if (PART == "yaw_body")    YAW_place() servo(MG, horn = false, spline = false);
// ---- turret frame
if (PART == "turret")      turret();
if (PART == "coupler")     { yaw_coupler(); translate([0, 0, -127]) cylinder(d = HORN_D, h = HORN_T); }
if (PART == "sh_body")     SH_servo() servo(DS, horn = false, spline = false);
// ---- link frames
if (PART == "link1")       link1();
if (PART == "el_body")     EL_servo() servo(DS, horn = false, spline = false);
if (PART == "sh_horn")     translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
if (PART == "link2")       link2();
if (PART == "post")        tilt_post();
if (PART == "tl_body")     TL_servo() servo(DS, horn = false, spline = false);
if (PART == "el_horn")     translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
if (PART == "cover1")      arm_cover(46, 74);
if (PART == "cover2")      arm_cover(46, 96);
// ---- head, tilt-axis frame (collision checks)
if (PART == "head_top")    head_frame() head_piece(0);      // includes the ears
if (PART == "head_mid")    head_frame() head_piece(1);
if (PART == "head_chin")   head_frame() head_piece(2);
if (PART == "ears")        head_ears();
if (PART == "eye_plate")   head_frame() eye_plate();
if (PART == "eye_rods")    head_frame() eye_rods();
if (PART == "lift_sg90")   head_frame() LIFT_place() servo(SG, horn = false);
if (PART == "lift_pinion") head_frame() translate([LIFT_C[0], -22, LIFT_C[2]]) lift_pinion(ZE);
if (PART == "carriage")    head_frame() { eye_carriage(ZE); translate([0, PIN_Y, ZE]) SG_place_local() servo(SG, horn = false); }
if (PART == "leds")        head_frame() status_leds();
if (PART == "bumper")      head_frame() bumper();
if (PART == "paper")       head_frame() paper_strip();
if (PART == "s3_horn")     translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
if (PART == "shut_top")    head_frame() shutter_top(S, ZE);
if (PART == "shut_bot")    head_frame() shutter_bottom(S, ZE);
if (PART == "pinion")      head_frame() translate([RKX[0] + 0.2, PIN_Y, ZE]) shutter_pinion(S);
if (PART == "neck_boot")   neck_boot();

// ---- print-only parts (own frames; orientation is set in the slicer / by the print service)
if (PART == "p_head_top")       head_piece(0);
if (PART == "p_head_mid")       head_piece(1);
if (PART == "p_head_chin")      head_piece(2);
if (PART == "p_eye_plate")      eye_plate();
if (PART == "p_rod_bar_top")    intersection() { eye_rods(rods = false); translate([-50, -80, -60]) cube([100, 160, 30]); }
if (PART == "p_rod_bar_bottom") intersection() { eye_rods(rods = false); translate([-50, -80, -200]) cube([100, 160, 120]); }
if (PART == "p_carriage")       difference() { eye_carriage(EYE_Z); translate([7.5, 0, EYE_Z]) rotate([0, 90, 0]) cylinder(d = LENS_D + 0.6, h = 14.5, $fn = 96); }
if (PART == "p_lens")           translate([13, 0, EYE_Z]) rotate([0, 90, 0]) intersection() {
                                    translate([0, 0, -60.25 + 8]) sphere(r = 60.25, $fn = 128); cylinder(d = LENS_D, h = 8, $fn = 96); }
if (PART == "p_lid_top")        shutter_top(1, EYE_Z);
if (PART == "p_lid_bottom")     shutter_bottom(1, EYE_Z);
if (PART == "p_pinion18")       shutter_pinion(0);
if (PART == "p_pinion36")       lift_pinion(EYE_Z);
if (PART == "p_yaw_coupler")    yaw_coupler();
if (PART == "p_pulley")         pulley();
if (PART == "p_pulley_small")   pulley_small();
if (PART == "p_spring_block")   spring_block();
if (PART == "p_neck_boot")      neck_boot();
if (PART == "p_bumper")         bumper();
