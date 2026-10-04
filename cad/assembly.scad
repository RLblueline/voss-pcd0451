// Full assembly. Override from the command line, e.g.
//   openscad -D SH=120 -D EL=-30 -D TILT=20 -D SHUT=0.2 -o view.png assembly.scad
include <memo.scad>

SH = 90; EL = 0; TILT = 0; SHUT = 1;   // joint angles (deg), shutter 0..1
SHOW_HOUSING = true; CUTAWAY = false; SHOW_HEAD = true; SHOW_WALL = true; SHOW_SHELL = true;

module tube_path(p0, p1, p2, d = 5, n = 14) {
    for (i = [0 : n - 1]) hull() for (t = [i / n, (i + 1) / n])
        translate((1 - t) * (1 - t) * p0 + 2 * t * (1 - t) * p1 + t * t * p2) sphere(d = d, $fn = 12);
}
function ry(p, a) = [p[0] * cos(a) + p[2] * sin(a), p[1], -p[0] * sin(a) + p[2] * cos(a)];

module assembly() {
    if (SHOW_WALL) color([0.93, 0.93, 0.91]) translate([-260, -12, -520]) cube([520, 12, 640]);
    if (SHOW_HOUSING) {
        if (CUTAWAY) difference() { color(C_BEIGE) housing_shell(); translate([-HW, HD - WALL - 0.5, HZ0 - 1]) cube([2 * HW, 10, HZ1 - HZ0 + 2]); }
        else color(C_BEIGE) housing_shell();
        if (!CUTAWAY) housing_inlays();
        color(C_BEIGE2) back_plate();
        electronics();
    }
    color(C_BEIGE2) shoulder_bracket();
    S1_place() servo(MG, horn = false);
    translate([0, SY, -47]) bearing(22, 8, 7);

    translate([0, SY, 0]) rotate([0, 0, SH]) {
        color(C_HORN) translate([0, 0, HORN_Z]) cylinder(d = HORN_D, h = HORN_T);
        color(C_STEEL) translate([0, 0, -58]) cylinder(d = 8, h = 18);
        link1();
        elbow_hanger();
        S2_place() servo(MG, horn = false);
        translate([L1, 0, -115]) bearing(22, 8, 7);

        translate([L1, 0, 0]) rotate([0, 0, EL]) {
            color(C_HORN) translate([0, 0, -69 + HORN_Z]) cylinder(d = HORN_D, h = HORN_T);
            color(C_STEEL) translate([0, 0, -126]) cylinder(d = 8, h = 18);
            link2();
            tilt_post();
            S3_place() servo(DS, horn = false);
            translate([L2 + TILT_OFF, -28, ZT]) rotate([-90, 0, 0]) bearing(13, 4, 5);
            // service loop cables (cosmetic)
            for (sy = [-6, 6]) color(C_BLACK) {
                h = [L2 + TILT_OFF, 0, ZT] + ry([-38, sy, HEAD_TOP - 4], TILT);
                tube_path([L2 - 16, sy, -126], [L2 - 40, sy * 1.5, -200], h, 4.5);
            }
            if (SHOW_HEAD) translate([L2 + TILT_OFF, 0, ZT]) rotate([0, TILT, 0]) {
                if (SHOW_SHELL) head_all(SHUT); else head_internals(SHUT);
                color(C_HORN) translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
                color(C_STEEL) translate([0, -36, 0]) rotate([-90, 0, 0]) cylinder(d = 4, h = 14);
            }
        }
    }
}
assembly();
