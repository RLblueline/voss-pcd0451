// Single-part export for printing and collision checks (each part in its own local frame).
//   openscad -D 'PART="link1"' -o link1.stl tools/parts.scad
include <../memo.scad>
PART = "link1"; S = 1;
if (PART == "housing")     housing_shell();
if (PART == "back_plate")  back_plate();
if (PART == "bracket")     shoulder_bracket();
if (PART == "s1_body")     S1_place() servo(MG, horn = false, spline = false);
if (PART == "link1")       link1();
if (PART == "hanger")      elbow_hanger();
if (PART == "s2_body")     S2_place() servo(MG, horn = false, spline = false);
if (PART == "s1_horn")     translate([0, 0, HORN_Z]) cylinder(d = HORN_D, h = HORN_T);
if (PART == "link2")       link2();
if (PART == "post")        tilt_post();
if (PART == "s3_body")     S3_place() servo(DS, horn = false, spline = false);
if (PART == "s2_horn")     translate([0, 0, -69 + HORN_Z]) cylinder(d = HORN_D, h = HORN_T);
if (PART == "head_top")    head_piece(0);
if (PART == "head_mid")    head_piece(1);
if (PART == "head_chin")   head_piece(2);
if (PART == "ears")        head_ears();
if (PART == "cartridge")   eye_cartridge();
if (PART == "sg90")        translate([0, PIN_Y, EYE_Z]) SG_place_local() servo(SG, horn = false);
if (PART == "leds")        status_leds();
if (PART == "bumper")      bumper();
if (PART == "neck_boot")   neck_boot();
if (PART == "paper")       paper_strip();
if (PART == "s3_horn")     translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
if (PART == "shut_top")    shutter_top(S);
if (PART == "shut_bot")    shutter_bottom(S);
if (PART == "pinion")      translate([RKX[0] + 0.2, PIN_Y, EYE_Z]) rotate([0, 90, 0]) linear_extrude(RKX[1] - RKX[0] - 0.4) difference() { gear2d(PIN_M, 2 * PIN_R / PIN_M); circle(d = 4.8, $fn = 20); }
// print-only extras
if (PART == "ear_plus")    intersection() { head_ears(); translate([-50, 0, -50]) cube([100, 50, 100]); }
if (PART == "ear_minus")   intersection() { head_ears(); translate([-50, -50, -50]) cube([100, 50, 100]); }
if (PART == "bezel")       intersection() { eye_cartridge(); translate([BEZEL_X - 1.99, -60, -200]) cube([1.99, 120, 170]); }
if (PART == "cartridge_frame") difference() {
    intersection() { eye_cartridge(); translate([3, -100, -300]) cube([BEZEL_X - 2.01 - 3, 200, 400]); }
    translate([8.5, 0, EYE_Z]) rotate([0, 90, 0]) cylinder(d = LENS_D + 0.6, h = 16, $fn = 96);
}
if (PART == "lens") translate([14, 0, EYE_Z]) rotate([0, 90, 0]) intersection() {
    translate([0, 0, -60.25 + 8]) sphere(r = 60.25, $fn = 128); cylinder(d = LENS_D, h = 8, $fn = 96); }
