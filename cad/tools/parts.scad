// Single-part export for printing and collision checks (each part in its own local frame).
//   openscad -D 'PART="link1"' -o link1.stl tools/parts.scad
include <../voss.scad>
PART = "link1"; S = 1;
if (PART == "housing")     housing_shell();
if (PART == "back_plate")  back_plate();
if (PART == "tower")       yaw_tower();
if (PART == "yaw_body")    YAW_place() servo(MG, horn = false, spline = false);
if (PART == "turret")      turret();
if (PART == "coupler")     { translate([0, 0, -121]) cylinder(d = HORN_D, h = HORN_T); translate([0, 0, -118]) cylinder(d = 18, h = 5); }
if (PART == "sh_body")     SH_servo() servo(DS, horn = false, spline = false);
if (PART == "link1")       link1();
if (PART == "el_body")     EL_servo() servo(DS, horn = false, spline = false);
if (PART == "sh_horn")     translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
if (PART == "link2")       link2();
if (PART == "post")        tilt_post();
if (PART == "tl_body")     TL_servo() servo(DS, horn = false, spline = false);
if (PART == "el_horn")     translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
PE = 0;   // eye height -1..1 for carriage / shutter / pinion exports
ZE = EYE_Z + PE * EYE_TRAVEL;
// head parts, exported in the tilt-axis frame (what collide.py expects)
if (PART == "head_top")    head_frame() head_piece(0);
if (PART == "head_mid")    head_frame() head_piece(1);
if (PART == "head_chin")   head_frame() head_piece(2);
if (PART == "ears")        head_ears();
if (PART == "eye_plate")   head_frame() eye_plate();
if (PART == "eye_rods")    head_frame() eye_rods();
if (PART == "lift_sg90")   head_frame() LIFT_place() servo(SG, horn = false);
if (PART == "lift_pinion") head_frame() translate([LIFT_C[0], -22, LIFT_C[2]]) rotate([-90, 0, 0]) linear_extrude(4) difference() { gear2d(PIN_M, 2 * LIFT_R / PIN_M); circle(d = 4.8, $fn = 20); }
if (PART == "carriage")    head_frame() { eye_carriage(ZE); translate([0, PIN_Y, ZE]) SG_place_local() servo(SG, horn = false); }
if (PART == "leds")        head_frame() status_leds();
if (PART == "bumper")      head_frame() bumper();
if (PART == "paper")       head_frame() paper_strip();
if (PART == "s3_horn")     translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
if (PART == "shut_top")    head_frame() shutter_top(S, ZE);
if (PART == "shut_bot")    head_frame() shutter_bottom(S, ZE);
if (PART == "pinion")      head_frame() translate([RKX[0] + 0.2, PIN_Y, ZE]) rotate([0, 90, 0]) linear_extrude(RKX[1] - RKX[0] - 0.4) difference() { gear2d(PIN_M, 2 * PIN_R / PIN_M); circle(d = 4.8, $fn = 20); }
if (PART == "neck_boot")   neck_boot();
if (PART == "cover1")      arm_cover(46, 74);
if (PART == "cover2")      arm_cover(46, 96);
// print-only parts (shell frame)
if (PART == "ear_plus")    intersection() { head_ears(); translate([-50, 0, -50]) cube([100, 50, 100]); }
if (PART == "ear_minus")   intersection() { head_ears(); translate([-50, -50, -50]) cube([100, 50, 100]); }
if (PART == "carriage_frame") difference() {
    eye_carriage(EYE_Z);
    translate([7.5, 0, EYE_Z]) rotate([0, 90, 0]) cylinder(d = LENS_D + 0.6, h = 14.5, $fn = 96);
}
if (PART == "lens") translate([13, 0, EYE_Z]) rotate([0, 90, 0]) intersection() {
    translate([0, 0, -60.25 + 8]) sphere(r = 60.25, $fn = 128); cylinder(d = LENS_D, h = 8, $fn = 96); }
