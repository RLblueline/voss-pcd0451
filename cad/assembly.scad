// Full assembly. Override from the command line, e.g.
//   openscad -D YAW=70 -D SH=30 -D EL=-30 -D TILT=0 -D SHUT=0.2 -o view.png assembly.scad
// TILT is the servo angle relative to link2; HEAD_LEVEL=true overrides it with SH + EL + PITCH.
include <memo.scad>

YAW = 90; SH = 20; EL = -20; TILT = 0; PITCH = 0; HEAD_LEVEL = true; SHUT = 1;
SHOW_HOUSING = true; CUTAWAY = false; SHOW_HEAD = true; SHOW_WALL = true; SHOW_SHELL = true;
T = HEAD_LEVEL ? SH + EL + PITCH : TILT;

module tube_path(p0, p1, p2, d = 5, n = 14) {
    for (i = [0 : n - 1]) hull() for (t = [i / n, (i + 1) / n])
        translate((1 - t) * (1 - t) * p0 + 2 * t * (1 - t) * p1 + t * t * p2) sphere(d = d, $fn = 12);
}
function ry(p, a) = [p[0] * cos(a) + p[2] * sin(a), p[1], -p[0] * sin(a) + p[2] * cos(a)];

module assembly() {
    if (SHOW_WALL) color([0.93, 0.93, 0.91]) translate([-300, -12, -560]) cube([600, 12, 760]);
    if (SHOW_HOUSING) {
        if (CUTAWAY) difference() { color(C_BEIGE) housing_shell(); translate([-HW, HD - WALL - 0.5, HZ0 - 1]) cube([2 * HW, 10, HZ1 - HZ0 + 2]); }
        else color(C_BEIGE) housing_shell();
        if (!CUTAWAY) housing_inlays();
        color(C_BEIGE2) back_plate();
        electronics();
    }
    color(C_BEIGE2) yaw_tower();
    YAW_place() servo(MG, horn = false);
    for (z = [-59, -111]) translate([0, SY, z]) bearing(22, 8, 7);

    translate([0, SY, 0]) rotate([0, 0, YAW]) {
        color(C_STEEL) translate([0, 0, -116]) cylinder(d = 8, h = 70);                 // yaw shaft
        color(C_HORN) translate([0, 0, -121]) cylinder(d = HORN_D, h = HORN_T);
        color(C_BEIGE2) translate([0, 0, -118]) cylinder(d = 18, h = 5);                // shaft coupler
        turret();
        SH_servo() servo(DS, horn = false);
        translate([0, -28, 0]) rotate([-90, 0, 0]) bearing(13, 4, 5);

        rotate([0, -SH, 0]) {
            color(C_HORN) translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
            link1();
            EL_servo() servo(DS, horn = false);
            translate([L1, -28, 0]) rotate([-90, 0, 0]) bearing(13, 4, 5);

            translate([L1, 0, 0]) rotate([0, -EL, 0]) {
                color(C_HORN) translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
                link2();
                tilt_post();
                TL_servo() servo(DS, horn = false);
                translate([L2 + TILT_OFF, -28, -TILT_DROP]) rotate([-90, 0, 0]) bearing(13, 4, 5);
                for (sy = [-6, 6]) color(C_BLACK) {
                    h = [L2 + TILT_OFF, 0, -TILT_DROP] + ry([-38, sy, HEAD_TOP - 4], T);
                    tube_path([L2 - 30, sy, -BEAM_Z - 1], [L2 - 45, sy * 1.5, -90], h, 4.5);
                }
                if (SHOW_HEAD) translate([L2 + TILT_OFF, 0, -TILT_DROP]) rotate([0, T, 0]) {
                    if (SHOW_SHELL) head_all(SHUT); else head_internals(SHUT);
                    color(C_HORN) translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
                    color(C_STEEL) translate([0, -36, 0]) rotate([-90, 0, 0]) cylinder(d = 4, h = 14);
                }
            }
        }
    }
}
assembly();
