// Full assembly. Override from the command line, e.g.
//   openscad -D YAW=70 -D SH=30 -D EL=-30 -D TILT=0 -D SHUT=0.2 -o view.png assembly.scad
// TILT is the servo angle relative to link2; HEAD_LEVEL=true overrides it with SH + EL + PITCH.
include <voss.scad>

YAW = 90; SH = 20; EL = -20; TILT = 0; PITCH = 0; HEAD_LEVEL = true; SHUT = 1; EYE = 0;   // EYE -1..1 = eye height in the slot
SHOW_HOUSING = true; CUTAWAY = false; SHOW_HEAD = true; SHOW_WALL = true; SHOW_SHELL = true;
T = HEAD_LEVEL ? SH + EL + PITCH : TILT;
ZE = EYE_Z + EYE * EYE_TRAVEL;

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
    for (z = [-59, -111]) translate([0, SY, z + ARM_Z0]) bearing(22, 8, 7);

    translate([0, SY, ARM_Z0]) rotate([0, 0, YAW]) {
        color(C_STEEL) translate([0, 0, -122]) cylinder(d = 8, h = 78);                 // yaw shaft
        color(C_HORN) translate([0, 0, -127]) cylinder(d = HORN_D, h = HORN_T);
        color(C_BEIGE2) yaw_coupler();
        turret();
        service_tube([-16, 14, -40], [-6, 26, 20], ry([30, 0, 17], -SH), 8);                 // yaw/shoulder loop
        // counterbalance (2:1): eye -> top pulley -> down -> spring-block pulley -> up to the anchor pin
        Q = [SPR_B * cos(SH), SPR_Y, SPR_B * sin(SH)];
        PQ = norm(Q - [0, SPR_Y, SPR_A]);
        L = SPR_L0 + max(0, PQ - SPR_D) / 2;                       // spring length
        zb = -26 + L + 9;                                          // spring-block pulley centre
        ang_in = atan2(Q[2] - SPR_A, Q[0]);
        T = [0, SPR_Y, SPR_A] + 5 * [cos(ang_in + 90), 0, sin(ang_in + 90)];
        color(C_BLACK) {
            hull() { translate(Q) sphere(d = 1.2, $fn = 8); translate(T) sphere(d = 1.2, $fn = 8); }
            hull() { translate([-5, SPR_Y, SPR_A]) sphere(d = 1.2, $fn = 8); translate([-5, SPR_Y, zb]) sphere(d = 1.2, $fn = 8); }
            hull() { translate([-12, SPR_Y, zb]) sphere(d = 1.2, $fn = 8); translate([-12, SPR_Y, SPR_A - 10]) sphere(d = 1.2, $fn = 8); }
        }
        color(C_STEEL) for (i = [0 : floor(L / 2.6) - 1]) translate([SPR_COL, SPR_Y, -26 + i * 2.6 + 1.3]) rotate_extrude($fn = 16) translate([5.2, 0]) circle(r = 1.0, $fn = 8);
        color(C_BEIGE2) translate([-8.5, SPR_Y, zb]) spring_block();
        color(C_HORN) { translate([0, SPR_Y, SPR_A]) rotate([90, 0, 0]) pulley(); translate([-8.5, SPR_Y, zb]) rotate([90, 0, 0]) pulley_small(); }
        SH_servo() servo(DS, horn = false);
        translate([0, -28, 0]) rotate([-90, 0, 0]) bearing(13, 4, 5);

        rotate([0, -SH, 0]) {
            color(C_HORN) translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
            link1();
            arm_cover(46, 74);
            harness(30, 76);
            for (sy = [-1, 1]) service_tube([76, sy * 3, 17], [L1, sy * 4, 52], [L1, 0, 0] + ry([40, sy * 3, 17], -EL), 7);   // elbow loop
            EL_servo() servo(DS, horn = false);
            translate([L1, -28, 0]) rotate([-90, 0, 0]) bearing(13, 4, 5);

            translate([L1, 0, 0]) rotate([0, -EL, 0]) {
                color(C_HORN) translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
                link2();
                tilt_post();
                TL_servo() servo(DS, horn = false);
                translate([L2 + TILT_OFF, -28, -TILT_DROP]) rotate([-90, 0, 0]) bearing(13, 4, 5);
                arm_cover(46, 96);
                harness(40, 98);
                for (sy = [-1, 1]) {                                                       // neck service tubes
                    h = [L2 + TILT_OFF, 0, -TILT_DROP] + ry([-62, sy * 10, HEAD_TOP - 8], T);
                    service_tube([98, sy * 5, 16], [88, sy * 24, -30], h, 6);
                }
                if (SHOW_HEAD) translate([L2 + TILT_OFF, 0, -TILT_DROP]) rotate([0, T, 0]) {
                    if (SHOW_SHELL) head_all(SHUT, ze = ZE); else head_internals(SHUT, ze = ZE);
                    color(C_HORN) translate([0, DS[2] / 2 + HORN_Z, 0]) rotate([-90, 0, 0]) cylinder(d = HORN_D, h = HORN_T);
                    color(C_STEEL) translate([0, -36, 0]) rotate([-90, 0, 0]) cylinder(d = 4, h = 14);
                }
            }
        }
    }
}
assembly();
