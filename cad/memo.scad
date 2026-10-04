// =====================================================================
// M.E.M.O. (PCD-0451) wall terminal - parametric CAD, v0.3
// Frame: X along wall, Y out of wall, Z up. Wall face y = 0. Units: mm.
// Shoulder axis at (0, SY, 0). All joints are horizontal-plane forks except
// the head tilt (horizontal axis). Every part is modelled in its own local
// frame; assembly transforms are in assembly.scad and tools/collide.py.
// =====================================================================

$fn = 48;
FONT  = "DejaVu Sans:style=Bold";
MONO  = "DejaVu Sans Mono:style=Bold";

// ---------------------------------------------------------------- colours
C_BEIGE  = [0.85, 0.80, 0.66];
C_BEIGE2 = [0.78, 0.73, 0.60];
C_CHAR   = [0.16, 0.16, 0.17];
C_ALU    = [0.42, 0.44, 0.47];
C_BLACK  = [0.06, 0.06, 0.06];
C_AMBER  = [1.00, 0.70, 0.30, 0.85];
C_SERVO  = [0.10, 0.10, 0.12];
C_HORN   = [0.92, 0.92, 0.92];
C_PCB    = [0.05, 0.35, 0.15];
C_PAPER  = [0.97, 0.96, 0.90];
C_REC    = [1.0, 0.15, 0.10, 0.9];
C_AUD    = [1.0, 0.55, 0.05, 0.9];
C_OK     = [0.35, 0.75, 0.30, 0.9];
C_STEEL  = [0.70, 0.71, 0.73];

// ---------------------------------------------------------------- arm geometry
SY       = 108;     // shoulder axis distance from wall
L1       = 120;     // shoulder -> elbow
L2       = 100;     // elbow -> link2 end
TILT_OFF = 14;      // tilt axis past link2 end
ZT       = -184;    // tilt axis height
PT       = 4;       // link plate thickness
HUB_R    = 16;      // fork hub radius
WEB_R    = 28;      // fork webs start this far from their joint axis
CLR      = 0.4;     // print clearance

// ---------------------------------------------------------------- servo data (verify with calipers)
// MG996R: shoulder + elbow. DS3218: tilt. SG90: shutters.
MG = [40.7, 19.7, 37.0, 54.5, 26.5, 2.5, 10.0, 49.5, 10.0];   // L W H flangeL flangeZ flangeT shaftOff holeX holeY
DS = [40.0, 20.0, 40.5, 54.5, 28.5, 2.5, 10.0, 49.5, 10.0];
SG = [22.5, 12.2, 22.7, 32.2, 15.9, 2.5,  5.9, 27.8,  0.0];
HORN_D = 24; HORN_T = 3; HORN_Z = 4;      // horn sits z 4..7 above servo top face

// ---------------------------------------------------------------- housing
HW = 144; HD = 70; HZ0 = -190; HZ1 = 36; WALL = 3;
BP_T = 4;            // back plate thickness

// ---------------------------------------------------------------- head (head frame: origin at tilt axis)
HEAD_TOP = 30; HEAD_BOT = -270; HEAD_X = 45; HEAD_Y = 70;
SHELL = 2.4;
SPLIT1 = -40; SPLIT2 = -195;
EYE_Z = -116;        // eye centre
EYE_Y = 40;          // cavity half width
EYE_Z0 = -184; EYE_Z1 = -48;   // cavity bottom / top
BEZEL_X = 28;        // bezel back face (recess depth = HEAD_X - BEZEL_X - 2)
LENS_D = 60;
SHUT_TRAVEL = 27;    // per plate; slit 12 mm when closed
PIN_R = 9; PIN_M = 1; PIN_Y = 48;
EAR_P = [27.25, 30.75];     // + ear (on tilt horn)
EAR_N = [-31.0, -27.5];     // - ear (on pivot bolt)

// =====================================================================
// helpers
// =====================================================================
module rrect(x, y, r) { offset(r) offset(-r) square([x, y], center = true); }
module rbox(size, r) { linear_extrude(size[2]) rrect(size[0], size[1], r); }
module hexhead(d = 5.5, h = 1.2) { color(C_BLACK) difference() { cylinder(d = d * 1.15, h = h, $fn = 6); translate([0,0,h-0.6]) cylinder(d = 2.5, h = 1, $fn = 6); } }

module gear2d(m, z) {
    rp = m * z / 2; ra = rp + m; rf = rp - 1.25 * m;
    union() {
        circle(r = rf, $fn = z * 4);
        for (i = [0 : z - 1]) rotate(i * 360 / z)
            polygon([[rf - 0.6, -m * 0.9], [ra, -m * 0.45], [ra, m * 0.45], [rf - 0.6, m * 0.9]]);
    }
}

// generic hobby servo: shaft = +Z through origin, top face z = 0, body toward -X
module servo(s, horn = true, spline = true, body = true) {
    L = s[0]; W = s[1]; H = s[2]; FL = s[3]; FZ = s[4]; FT = s[5]; OFF = s[6]; HX = s[7]; HY = s[8];
    cx = OFF - L / 2;
    if (body) color(C_SERVO) difference() {
        union() {
            translate([OFF - L, -W / 2, -H]) cube([L, W, H]);
            translate([cx - FL / 2, -W / 2, -H + FZ]) cube([FL, W, FT]);
        }
        for (sx = [-1, 1], sy = (HY > 0 ? [-1, 1] : [0]))
            translate([cx + sx * HX / 2, sy * HY / 2, -H]) cylinder(d = 4.2, h = H + 1, $fn = 16);
    }
    if (spline) color(C_SERVO) cylinder(d = (s == SG ? 4.8 : 6), h = HORN_Z + 1, $fn = 20);
    if (horn) color(C_HORN) translate([0, 0, HORN_Z]) cylinder(d = HORN_D * (s == SG ? 0.6 : 1), h = HORN_T);
}

// cutout for a servo body through a mount plate (in servo local frame)
module servo_cut(s, h = 200) {
    L = s[0]; W = s[1]; OFF = s[6];
    translate([OFF - L - CLR, -W / 2 - CLR, -h / 2]) cube([L + 2 * CLR, W + 2 * CLR, h]);
}
module servo_holes(s, h = 200) {
    L = s[0]; OFF = s[6]; HX = s[7]; HY = s[8]; cx = OFF - L / 2;
    for (sx = [-1, 1], sy = (HY > 0 ? [-1, 1] : [0]))
        translate([cx + sx * HX / 2, sy * HY / 2, -h / 2]) cylinder(d = 2.6, h = h, $fn = 16);
}
module horn_holes(h = 20) {
    cylinder(d = 3.2, h = h, center = true, $fn = 16);
    for (a = [45 : 90 : 360]) rotate(a) translate([8, 0, 0]) cylinder(d = 2.2, h = h, center = true, $fn = 12);
}

// 608 bearing (8 x 22 x 7) and 624 (4 x 13 x 5)
module bearing(od, id, w) { color(C_STEEL) difference() { cylinder(d = od, h = w); translate([0,0,-1]) cylinder(d = id, h = w + 2); } }

// =====================================================================
// WORLD-FIXED PARTS
// =====================================================================
module housing_shell() {
    difference() {
        translate([0, HD / 2, HZ0]) rbox([HW, HD, HZ1 - HZ0], 8);
        // hollow, open back
        translate([0, (HD - WALL) / 2 - 1, HZ0 + WALL]) rbox([HW - 2 * WALL, HD - WALL + 2, HZ1 - HZ0 - 2 * WALL], 5);
        // mic holes (80 mm apart)
        for (x = [-40, 40]) translate([x, HD - 5, 20]) rotate([-90, 0, 0]) cylinder(d = 3, h = 10);
        // speaker grille (40 mm speaker)
        for (r = [0, 6, 12], a = [0 : (r == 0 ? 360 : 360 / (r == 6 ? 8 : 14)) : 359])
            translate([r * cos(a), HD - 5, -45 + r * sin(a)]) rotate([-90, 0, 0]) cylinder(d = 3.2, h = 10, $fn = 12);
        // printer paper exit + tear bar recess
        translate([-31, HD - 6, -137]) cube([62, 10, 4.5]);
        translate([-36, HD - 1.2, -141]) cube([72, 2, 13]);
        // shoulder bracket screws + servo cable
        for (x = [-24, 24], z = [-42, -12]) translate([x, HD - 5, z]) rotate([-90, 0, 0]) cylinder(d = 3.4, h = 10, $fn = 16);
        translate([0, HD - 5, -26]) rotate([-90, 0, 0]) cylinder(d = 10, h = 10);
        // power jacks (5 V logic, 6 V servo) + vents in the bottom
        for (x = [-30, 30]) translate([x, 30, HZ0 - 1]) cylinder(d = 8, h = 6);
        for (x = [-12 : 6 : 12]) translate([x - 1.5, 15, HZ0 - 1]) cube([3, 40, 6]);
        // back-plate screws through the side walls
        for (sx = [-1, 1], z = [10, -160]) translate([sx * (HW / 2 - 5), 2, z]) rotate([0, 90, 0]) cylinder(d = 3.4, h = 12, center = true, $fn = 16);
        // front lettering (debossed)
        translate([0, HD - 0.6, -80]) rotate([90, 0, 180]) linear_extrude(1) text("APERTURE SCIENCE", size = 7, font = FONT, halign = "center");
        translate([0, HD - 0.6, -92]) rotate([90, 0, 180]) linear_extrude(1) text("HR TERMINAL  PCD-0451", size = 4.5, font = MONO, halign = "center");
    }
    // printer bay rails and electronics standoffs
    for (x = [-42, 40]) translate([x, 8, HZ0 + WALL]) cube([2, HD - 12, 8]);
}

module back_plate() {
    difference() {
        translate([0, BP_T / 2, HZ0 + WALL + 0.3]) translate([0, 0, 0]) linear_extrude(HZ1 - HZ0 - 2 * WALL - 0.6) rrect(HW - 2 * WALL - 0.6, BP_T, 1);
        // keyholes for a single stud (screw heads up to 9 mm)
        for (z = [0, -150]) {
            translate([0, -1, z]) rotate([-90, 0, 0]) cylinder(d = 9.5, h = BP_T + 2);
            translate([-2.4, -1, z]) cube([4.8, BP_T + 2, 12]);
        }
        // heat-set insert pockets in the plate edges
        for (sx = [-1, 1], z = [10, -160]) translate([sx * (HW / 2 - WALL - 4), 2, z]) rotate([0, 90, 0]) cylinder(d = 4.2, h = 8, center = true, $fn = 16);
        // cable pass-through
        translate([0, -1, -100]) rotate([-90, 0, 0]) cylinder(d = 12, h = BP_T + 2);
    }
    // standoffs for Pi Zero 2 W (58 x 23) and PCA9685 (56 x 19)
    for (p = [[-29, 0], [29, 0], [-29, -23], [29, -23]]) translate([p[0], BP_T, p[1] - 10]) rotate([-90, 0, 0]) difference() { cylinder(d = 6, h = 5); cylinder(d = 2.5, h = 6); }
    for (p = [[-28, 0], [28, 0], [-28, -19], [28, -19]]) translate([p[0], BP_T, p[1] - 60]) rotate([-90, 0, 0]) difference() { cylinder(d = 6, h = 5); cylinder(d = 2.5, h = 6); }
}

// shoulder servo in world frame
module S1_place() { translate([0, SY, 0]) rotate([0, 0, 90]) children(); }

module shoulder_bracket() {
    difference() {
        union() {
            translate([-30, HD, -48]) cube([60, 4, 42]);                     // mount plate
            translate([-16, HD + 4, -13.5]) cube([32, SY + 19 - HD - 4, 3]);  // shelf under servo flange
            translate([0, 0, -48]) linear_extrude(8) hull() {                  // floor with bearing
                translate([-16, HD + 4]) square([32, 1]);
                translate([0, SY]) circle(r = 15);
            }
            for (sx = [-1, 1]) translate([sx * 14.5 - 1.5, HD + 4, -48]) cube([3, SY - 14 - HD - 4, 37.5]);  // side walls
            for (sx = [-1, 1]) translate([sx * 14.5 - 1.5, HD, -48]) cube([3, 4, 42]);
        }
        S1_place() { servo_cut(MG, 40); servo_holes(MG); }
        translate([0, SY, -47]) cylinder(d = 22.2, h = 7.1);   // 608 pocket
        translate([0, SY, -60]) cylinder(d = 10, h = 30);
        for (x = [-24, 24], z = [-42, -12]) translate([x, HD - 1, z]) rotate([-90, 0, 0]) cylinder(d = 3.4, h = 10, $fn = 16);
        translate([0, HD - 1, -26]) rotate([-90, 0, 0]) cylinder(d = 10, h = 10);
    }
}

// =====================================================================
// LINK 1  (frame: origin on shoulder axis, +X along the link)
// =====================================================================
module link_plate(len, r0, r1) { hull() { circle(r = r0); translate([len, 0]) circle(r = r1); } }

module link1() {
    color(C_BEIGE) difference() {
        union() {
            translate([0, 0, HORN_Z + HORN_T]) linear_extrude(PT) link_plate(L1, HUB_R, HUB_R);   // top z 7..11
            translate([0, 0, -56]) linear_extrude(PT) link_plate(L1, HUB_R, HUB_R);              // bottom z -56..-52
            for (sy = [-1, 1]) translate([WEB_R, sy * 14 - 2, -52]) cube([L1 - 22 - WEB_R, 4, 59]); // box-beam webs
            translate([WEB_R, -14, -52]) cube([3, 28, 59]);
            // raised panel detail on top
            translate([0, 0, 11]) linear_extrude(1.2) translate([WEB_R + 6, -9]) square([L1 - WEB_R - 40, 18]);
        }
        horn_holes();
        translate([0, 0, -60]) cylinder(d = 8.2, h = 10);
        // hanger bolts
        for (x = [L1 - 54, L1 - 42], y = [-9, 9]) translate([x, y, -60]) cylinder(d = 3.4, h = 10, $fn = 16);
    }
    // cosmetic hex screws on the top plate
    for (x = [WEB_R + 2, L1 - 24], y = [-12, 12]) translate([x, y, 11]) hexhead(4.5, 1);
}

// elbow servo placement in link1 frame (body points back toward the shoulder)
module S2_place() { translate([L1, 0, -69]) children(); }

module elbow_hanger() {
    color(C_BEIGE2) difference() {
        union() {
            translate([L1 - 58, -16, -116]) cube([20, 32, 60]);                               // back block
            translate([L1 - 58, -16, -82.5]) cube([58 + 19, 32, 3]);                          // shelf
            translate([0, 0, -116]) linear_extrude(8) hull() {                                // bearing floor
                translate([L1 - 58, -16]) square([1, 32]);
                translate([L1, 0]) circle(r = 15);
            }
        }
        S2_place() { servo_cut(MG, 30); servo_holes(MG); }
        translate([L1, 0, -115]) cylinder(d = 22.2, h = 7.1);
        translate([L1, 0, -130]) cylinder(d = 10, h = 30);
        for (x = [L1 - 54, L1 - 42], y = [-9, 9]) translate([x, y, -70]) cylinder(d = 2.6, h = 20, $fn = 16);
        translate([L1 - 48, 0, -110]) rotate([90, 0, 0]) cylinder(d = 9, h = 40, center = true);  // cable window
    }
}

// =====================================================================
// LINK 2  (frame: origin on elbow axis, +X along the link)
// =====================================================================
module link2() {
    color(C_BEIGE) difference() {
        union() {
            translate([0, 0, -62]) linear_extrude(PT) link_plate(L2, HUB_R, 14);                     // top z -62..-58
            translate([0, 0, -124]) linear_extrude(PT) link_plate(L2 + TILT_OFF, HUB_R, 16);         // bottom, tab to tilt axis
            for (sy = [-1, 1]) translate([WEB_R + 2, sy * 12 - 2, -120]) cube([L2 - WEB_R - 2, 4, 58]);
            translate([L2 - 4, -14, -120]) cube([4, 28, 58]);
            translate([WEB_R + 2, -14, -120]) cube([3, 28, 58]);
        }
        horn_holes();
        translate([0, 0, -130]) cylinder(d = 8.2, h = 10);
        for (x = [L2 + TILT_OFF - 10, L2 + TILT_OFF + 10]) translate([x, 11, -130]) cylinder(d = 3.4, h = 10, $fn = 16);
    }
    for (x = [WEB_R + 6, L2 - 12], y = [-10, 10]) translate([x, y, -58]) hexhead(4.5, 1);
}

// tilt servo placement in link2 frame: shaft along +Y, body pointing up
module S3_place() {
    translate([L2 + TILT_OFF, DS[2] / 2, ZT]) multmatrix([[0, -1, 0, 0], [0, 0, 1, 0], [-1, 0, 0, 0], [0, 0, 0, 1]]) children();
}

module tilt_post() {
    X = L2 + TILT_OFF;
    yfl = DS[2] / 2 - DS[2] + DS[4];     // flange underside y
    color(C_BEIGE2) difference() {
        union() {
            translate([X - 16, yfl - 3.5, ZT - 22]) cube([32, 3.5, 60]);                       // mount plate (flange zone)
            translate([X - 16, yfl - 3.5, ZT + 37]) cube([22, 3.5, -124 - (ZT + 37)]);       // narrowed neck up to link2 (tilt clearance)
            translate([X - 16, -27, ZT - 16]) cube([32, 5, 32]);                                     // pivot plate
            for (sx = [-1, 1]) translate([X + sx * 14 - 2, -27, ZT - 16]) cube([4, yfl + 27, 32]);   // side bars
            translate([X - 16, yfl - 3.5, -128]) cube([32, 14, 4]);                                 // top foot under link2
        }
        S3_place() { servo_cut(DS, 30); servo_holes(DS); }
        translate([X, -28, ZT]) rotate([-90, 0, 0]) cylinder(d = 13.2, h = 5.1);   // 624 bearing
        for (x = [X - 10, X + 10]) translate([x, 11, -140]) cylinder(d = 2.6, h = 30, $fn = 16);
    }
}

// =====================================================================
// HEAD  (frame: origin on tilt axis, +X forward, tilt 0 = level)
// =====================================================================
// outer envelope: flat front, slight taper, tapered chin
module head_solid(inset = 0) {
    hull() {
        translate([0, 0, HEAD_TOP - inset - 0.01]) linear_extrude(0.01) translate([0, 0]) rrect(2 * HEAD_X - 2 * inset, 2 * HEAD_Y - 2 * inset, 7);
        translate([1.5, 0, -230]) linear_extrude(0.01) rrect(2 * HEAD_X - 3 - 2 * inset, 2 * HEAD_Y - 12 - 2 * inset, 7);
        translate([5, 0, HEAD_BOT + inset]) linear_extrude(0.01) rrect(66 - 2 * inset, 92 - 2 * inset, 6);
    }
}

module cavity_2d() { rrect(EYE_Z1 - EYE_Z0, 2 * EYE_Y, 18); }

module head_features_cut() {
    // eye cavity: rounded vertical recess down to the bezel
    translate([BEZEL_X - 0.01, 0, (EYE_Z0 + EYE_Z1) / 2]) rotate([0, 90, 0]) linear_extrude(30) cavity_2d();
    // chin "printer" slot
    translate([HEAD_X - 6, -46, -212]) cube([12, 92, 4]);
    // status windows REC AUD OK (viewer's right = +Y)
    for (y = [14, 34, 54]) translate([HEAD_X - 6, y, 12]) rotate([0, 90, 0]) linear_extrude(12) rrect(9, 15, 1.5);
    // neck slot: post and tilt servo pass through the crown and upper back
    translate([-HEAD_X - 1, EAR_N[1], -28]) cube([HEAD_X + 33, EAR_P[0] - EAR_N[1], 80]);
}

module head_shell() {
    difference() {
        head_solid();
        difference() {
            head_solid(SHELL);
            translate([BEZEL_X, 0, (EYE_Z0 + EYE_Z1) / 2]) rotate([0, 90, 0]) linear_extrude(HEAD_X) offset(SHELL) cavity_2d();
        }
        head_features_cut();
        translate([HEAD_X - 0.6, -62, 8]) rotate([90, 0, 90]) linear_extrude(1) text("APERTURE HR", size = 6.5, font = FONT, halign = "left");
        for (t = [["REC", 14], ["AUD", 34], ["OK", 54]])
            translate([HEAD_X - 0.5, t[1], 1.5]) rotate([90, 0, 90]) linear_extrude(1) text(t[0], size = 3.4, font = MONO, halign = "center");
    }
}

// split into three printable pieces
module head_piece(i) {
    zs = [[SPLIT1, HEAD_TOP + 1], [SPLIT2, SPLIT1], [HEAD_BOT - 1, SPLIT2]];
    color(i == 1 ? C_BEIGE : C_BEIGE2) union() {
        intersection() { head_shell(); translate([-100, -100, zs[i][0]]) cube([200, 200, zs[i][1] - zs[i][0]]); }
        // alignment lip on the lower edge of the upper pieces (fused 3 mm up, 5 mm skirt down)
        if (i < 2) difference() {
            union() {
                intersection() { difference() { head_solid(SHELL - 0.6); head_solid(SHELL + 1.6); }
                                 translate([-100, -100, zs[i][0]]) cube([200, 200, 3]); }
                intersection() { difference() { head_solid(SHELL + 0.2); head_solid(SHELL + 1.6); }
                                 translate([-100, -100, zs[i][0] - 5]) cube([200, 200, 5.01]); }
            }
            head_features_cut();
            translate([BEZEL_X - 0.5, 0, (EYE_Z0 + EYE_Z1) / 2]) rotate([0, 90, 0]) linear_extrude(HEAD_X) offset(SHELL + 3) cavity_2d();
        }
        // internal screw bosses at the seams
        if (i < 2) for (p = [[-30, 55], [-30, -55], [20, 60], [20, -60]]) intersection() {
            translate([p[0], p[1], zs[i][0]]) difference() { cylinder(d = 8, h = 10); translate([0,0,-1]) cylinder(d = 2.6, h = 12); }
            head_solid(1);
        }
    }
    // visible black hex screws on the front at each seam
    if (i < 2) for (y = [-58, 58]) translate([HEAD_X, y, zs[i][0] + 6]) rotate([0, 90, 0]) hexhead(6, 1.2);
    if (i == 0) for (y = [-58, 58]) translate([HEAD_X, y, 24]) rotate([0, 90, 0]) hexhead(6, 1.2);
}

module head_ears() {
    color(C_BEIGE2) {
        // + ear bolts to the tilt horn
        difference() {
            translate([0, EAR_P[0], 0]) rotate([90, 0, 0]) mirror([0,0,1]) linear_extrude(EAR_P[1] - EAR_P[0]) hull() {
                circle(r = 16); translate([-30, HEAD_TOP - SHELL - 6]) square([60, 6]);
            }
            translate([0, 20, 0]) rotate([-90, 0, 0]) horn_holes(40);
        }
        // - ear rides the pivot bolt
        difference() {
            translate([0, EAR_N[0], 0]) rotate([90, 0, 0]) mirror([0,0,1]) linear_extrude(EAR_N[1] - EAR_N[0]) hull() {
                circle(r = 16); translate([-30, HEAD_TOP - SHELL - 6]) square([60, 6]);
            }
            rotate([90, 0, 0]) cylinder(d = 4.3, h = 80, center = true);
        }
    }
}

// ----------------------------------------------------------------- eye cartridge
// x stack (front to back): face 45 | recess | bezel 26..28 | shutters 23.6..25.6 |
// racks + pinion 19.8..23.4 | rails 16.4..19.6 | lens dome 14..22 | LED ring 9..12 | rear plate 4..7
SHX = [23.6, 25.6]; RKX = [19.8, 23.4]; RLX = [16.4, 19.6];
SG_TOP_X = RKX[0] - 4;

module SG_place_local() { multmatrix([[0, 0, 1, SG_TOP_X], [0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]]) children(); }

module eye_cartridge() {
    color(C_CHAR) difference() {         // bezel = visible back of the recess
        translate([BEZEL_X - 2, -EYE_Y - 6, EYE_Z0 - 6]) cube([2, 2 * EYE_Y + 12, EYE_Z1 - EYE_Z0 + 12]);
        translate([BEZEL_X - 3, 0, EYE_Z]) rotate([0, 90, 0]) cylinder(d = LENS_D + 6, h = 5, $fn = 96);
    }
    color(C_CHAR) {
        difference() {                   // rear plate
            translate([4, -62, -190]) cube([3, 124, 142]);
            translate([3, 0, EYE_Z]) rotate([0, 90, 0]) cylinder(d = 20, h = 5);
            translate([3, PIN_Y - 6.6, EYE_Z - 17.1]) cube([5, 13.2, 23.5]);
        }
        for (y = [-58, 54], z = [-186, -54]) translate([4, y, z]) cube([BEZEL_X - 6, 4, 4]);
        translate([8, 0, EYE_Z]) rotate([0, 90, 0]) difference() {      // lens holder
            cylinder(d = LENS_D + 8, h = 9, $fn = 96); translate([0,0,-1]) cylinder(d = LENS_D + 0.6, h = 11, $fn = 96); }
        difference() {                   // left guide rail with groove for both shutter tongues
            translate([RKX[0] + 1.2, -49, -190]) cube([BEZEL_X - 2 - RKX[0] - 1.2, 6, 140]);
            translate([SHX[0] - 0.4, -45, -191]) cube([SHX[1] - SHX[0] + 0.8, 3.2, 142]);
        }
        translate([RLX[0], PIN_Y - 14, -190]) cube([RLX[1] - RLX[0], 3.75, 140]);     // rack backing rails
        translate([RLX[0], PIN_Y + 10.25, -190]) cube([RLX[1] - RLX[0], 3.75, 140]);
        difference() {                   // SG90 mount plate + straps
            translate([6.5, PIN_Y - 8.4, EYE_Z - 28]) cube([2.5, 17, 46]);
            translate([0, PIN_Y, EYE_Z]) SG_place_local() { servo_cut(SG, 30); servo_holes(SG); }
        }
        translate([6.5, PIN_Y - 8.4, EYE_Z - 28]) cube([RLX[1] - 6.5, 2, 46]);
        translate([6.5, PIN_Y + 6.6, EYE_Z - 28]) cube([RLX[1] - 6.5, 2, 46]);
    }
    color(C_AMBER) translate([14, 0, EYE_Z]) rotate([0, 90, 0]) intersection() {   // lens dome
        translate([0, 0, -60.25 + 8]) sphere(r = 60.25, $fn = 128);
        cylinder(d = LENS_D, h = 8, $fn = 96);
    }
    color(C_PCB) translate([9, 0, EYE_Z]) rotate([0, 90, 0]) difference() { cylinder(d = 44, h = 1.6); translate([0,0,-1]) cylinder(d = 32, h = 4); }
    for (a = [0 : 360 / 16 : 359]) color([1, 0.75, 0.4]) translate([11.2, 19 * cos(a), EYE_Z + 19 * sin(a)]) cube([1.2, 4, 4], center = true);
}

// s = 1 open, 0 closed (12 mm squint slit)
module rack(y0, z0, teeth_dir, len = 50) {   // bar 3.75 wide + 1 mm-module teeth
    translate([RKX[0], y0, z0]) cube([RKX[1] - RKX[0], 3.75, len]);
    for (k = [0 : len - 1]) translate([RKX[0], teeth_dir > 0 ? y0 + 3.75 : y0 - 2.25, z0 + k + 0.25]) cube([RKX[1] - RKX[0], 2.25, 0.5]);
}
module shutter_top(s = 1) {
    zb = EYE_Z + 6 + SHUT_TRAVEL * s;
    color(C_ALU) {
        translate([SHX[0], -42, zb]) cube([SHX[1] - SHX[0], 84, 40]);
        translate([SHX[0], -44.6, zb]) cube([SHX[1] - SHX[0], 3, 40]);                   // guide tongue
        rack(PIN_Y - 9 - 1.25 - 3.75, zb - 40, 1);                                        // pitch line y = PIN_Y - 9
        translate([RKX[1] - 0.01, PIN_Y - 14, zb]) cube([SHX[0] - RKX[1] + 0.02, 3.75, 10]);  // bridge
    }
}
module shutter_bottom(s = 1) {
    zt = EYE_Z - 6 - SHUT_TRAVEL * s;
    color(C_ALU) {
        translate([SHX[0], -42, zt - 40]) cube([SHX[1] - SHX[0], 84, 40]);
        translate([SHX[0], -44.6, zt - 40]) cube([SHX[1] - SHX[0], 3, 40]);
        translate([RKX[0], 42.5, zt - 20]) cube([SHX[1] - RKX[0], PIN_Y + 14 - 42.5, 8]);  // arm
        translate([SHX[0], 41.9, zt - 20]) cube([SHX[1] - SHX[0], 0.7, 20]);
        rack(PIN_Y + 9 + 1.25, zt - 20, -1, 60);                                              // pitch line y = PIN_Y + 9
    }
}
module shutter_drive(s = 1) {
    ang = SHUT_TRAVEL * s / PIN_R * 180 / PI;
    color(C_HORN) translate([RKX[0] + 0.2, PIN_Y, EYE_Z]) rotate([0, 90, 0]) rotate(ang) linear_extrude(RKX[1] - RKX[0] - 0.4) difference() { gear2d(PIN_M, 2 * PIN_R / PIN_M); circle(d = 4.8, $fn = 20); }
    translate([0, PIN_Y, EYE_Z]) SG_place_local() servo(SG, horn = false);
}

module status_leds() {
    for (i = [0 : 2]) {
        y = [14, 34, 54][i];
        color(C_PCB) translate([37, y - 5, 7]) cube([1.6, 10, 10]);
        color([C_REC, C_AUD, C_OK][i]) translate([HEAD_X - 2.6, y, 12]) rotate([0, 90, 0]) linear_extrude(2.4) rrect(8.4, 14.4, 1.3);
    }
}

module paper_strip() {
    color(C_PAPER) translate([HEAD_X + 0.6, -29, -282]) cube([0.6, 58, 72]);
    color(C_BLACK) translate([HEAD_X + 1.21, 0, -224]) rotate([90, 0, 90]) linear_extrude(0.3) {
        text("FORM 1040-HR", size = 4.6, font = MONO, halign = "center");
        translate([0, -8]) text("OUTSTANDING", size = 4.6, font = MONO, halign = "center");
        translate([0, -20]) text("- - - - - - - -", size = 4, font = MONO, halign = "center");
    }
}

module dymo_labels() {
    labels = ["PROPERTY OF APERTURE SCIENCE - BRANCH 04 (HR)", "UNIT ID: PCD-0451 // VOSS, H.", "MANDATORY SERVICE INTERVAL: 30 DAYS"];
    lens   = [168, 115, 136];
    a = -atan(6 / 260);                      // side face slope
    for (i = [0 : 2]) translate([24 - i * 13, HEAD_Y, HEAD_TOP]) rotate([a, 0, 0]) translate([0, 0, -38]) {
        color(C_BLACK) translate([-5, -0.4, -lens[i]]) cube([10, 1.0, lens[i]]);
        color([0.93, 0.93, 0.93]) translate([0, 0.55, -2])
            multmatrix([[0, -1, 0, 0], [0, 0, 1, 0], [-1, 0, 0, 0], [0, 0, 0, 1]]) linear_extrude(0.35) text(labels[i], size = 4.3, font = MONO, valign = "center");
    }
}

module head_inlays() {   // black fill in the engraved lettering
    color(C_BLACK) {
        translate([HEAD_X - 0.5, -62, 8]) rotate([90, 0, 90]) linear_extrude(0.6) text("APERTURE HR", size = 6.5, font = FONT, halign = "left");
        for (t = [["REC", 14], ["AUD", 34], ["OK", 54]])
            translate([HEAD_X - 0.4, t[1], 1.5]) rotate([90, 0, 90]) linear_extrude(0.5) text(t[0], size = 3.4, font = MONO, halign = "center");
    }
}
module housing_inlays() {
    color(C_BLACK) {
        translate([0, HD - 0.5, -80]) rotate([90, 0, 180]) linear_extrude(0.6) text("APERTURE SCIENCE", size = 7, font = FONT, halign = "center");
        translate([0, HD - 0.5, -92]) rotate([90, 0, 180]) linear_extrude(0.6) text("HR TERMINAL  PCD-0451", size = 4.5, font = MONO, halign = "center");
    }
}

module bumper() { color(C_BLACK) translate([5, 0, HEAD_BOT - 8]) cylinder(d = 22, h = 8.5); }

module neck_boot() {
    color([0.12, 0.12, 0.12]) for (i = [0 : 6]) translate([-2, 0, HEAD_TOP + 1 + i * 4]) scale([1.25, 1.35, 1]) rotate_extrude($fn = 40) translate([20 - (i % 2) * 2, 0]) circle(r = 2.2, $fn = 16);
}

module head_internals(s = 1) {
    head_ears(); eye_cartridge(); shutter_top(s); shutter_bottom(s); shutter_drive(s); status_leds();
    color([0.85, 0.8, 0.66, 0.18]) head_piece(2);
}

module head_all(s = 1, cosmetic = true) {
    for (i = [0 : 2]) head_piece(i);
    head_ears();
    eye_cartridge();
    shutter_top(s); shutter_bottom(s); shutter_drive(s);
    status_leds();
    paper_strip();
    bumper();
    if (cosmetic) { dymo_labels(); neck_boot(); head_inlays(); }
}

// =====================================================================
// electronics placeholders (world frame)
// =====================================================================
module electronics() {
    color(C_PCB) translate([-32.5, BP_T + 5, -38]) cube([65, 1.6, 30]);                 // Pi Zero 2 W
    color(C_PCB) translate([-31, BP_T + 5, -84]) cube([62, 1.6, 25.4]);                 // PCA9685
    color(C_PCB) translate([20, HD - 26, -60]) cube([18, 1.6, 18]);                     // MAX98357A
    color(C_SERVO) translate([0, HD - 13, -45]) rotate([-90, 0, 0]) cylinder(d = 40, h = 9);   // speaker
    for (x = [-40, 40]) color(C_PCB) translate([x - 7, HD - 6.5, 13]) cube([14, 1.6, 14]); // INMP441
    color([0.85, 0.85, 0.85]) translate([-40, 8, -186]) cube([80, 55, 47]);             // 58 mm printer module
    color([0.15, 0.15, 0.6]) translate([45, 10, -30]) cylinder(d = 10, h = 16);          // 1000 uF
}
