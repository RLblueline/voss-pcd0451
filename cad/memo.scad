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
SY       = 112;     // yaw axis distance from wall
ARM_Z    = 0;       // shoulder pitch axis height (sits on the yaw axis)
L1       = 120;     // shoulder -> elbow (pitch axes)
L2       = 100;     // elbow -> link2 end
TILT_OFF = 14;      // tilt axis past link2 end
TILT_DROP = 72;     // tilt axis below link2's centreline
HUB_R    = 16;      // side-plate hub radius
XB0      = 36;      // cross block (joins side plates to the centre beam) starts here
BEAM_Y   = 10; BEAM_Z = 12;   // centre beam half width / half height
PT       = 3.5;     // side plate thickness
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
        for (x = [-24, 24], z = [-136, -52]) translate([x, HD - 5, z]) rotate([-90, 0, 0]) cylinder(d = 3.4, h = 10, $fn = 16);
        translate([0, HD - 5, -90]) rotate([-90, 0, 0]) cylinder(d = 12, h = 10);
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

// =====================================================================
// CLASSIC ARM: base yaw (vertical) + shoulder / elbow / head-tilt pitch (horizontal)
// Frames:  turret = translate([0,SY,0]) rotate([0,0,YAW])
//          link1  = turret * rotate([0,-SH,0])            (SH > 0 lifts the arm)
//          link2  = link1 * translate([L1,0,0]) rotate([0,-EL,0])
//          head   = link2 * translate([L2+TILT_OFF,0,-TILT_DROP]) rotate([0,TILT,0])
// Head stays level when TILT = SH + EL.
// =====================================================================

// ---------------------------------------------------------------- yaw tower (world)
module YAW_place() { translate([0, SY, -125]) rotate([0, 0, 90]) children(); }   // MG996R, shaft up

module yaw_tower() {
    module shelf(z0, t, front) translate([0, 0, z0]) linear_extrude(t) hull() {
        translate([-16, HD + 4]) square([32, 1]); translate([0, SY]) circle(r = front);
    }
    difference() {
        union() {
            translate([-30, HD, -142]) cube([60, 4, 96]);                                 // wall plate
            shelf(-60, 8, 15);                                                            // upper 608
            shelf(-112, 8, 15);                                                           // lower 608
            translate([0, 0, -138.5]) linear_extrude(3) hull() {                          // servo shelf
                translate([-16, HD + 4]) square([32, 1]); translate([-16, SY + 18]) square([32, 1]); }
            for (sx = [-1, 1]) translate([sx * 14.5 - 1.5, HD + 4, -142]) cube([3, SY - 14 - HD - 4, 90]);
        }
        for (z = [-59.1, -111.1]) translate([0, SY, z]) cylinder(d = 22.2, h = 7.2);
        translate([0, SY, -150]) cylinder(d = 10, h = 120);
        YAW_place() { servo_cut(MG, 30); servo_holes(MG); }
        for (x = [-24, 24], z = [-136, -52]) translate([x, HD - 1, z]) rotate([-90, 0, 0]) cylinder(d = 3.4, h = 10, $fn = 16);
        translate([0, HD - 1, -90]) rotate([-90, 0, 0]) cylinder(d = 12, h = 10);
    }
}

// ---------------------------------------------------------------- pitch joint bracket
// Canonical: joint axis = Y through the origin, servo (DS-size) shaft +Y, body pointing +Z.
// Horn at y 24.25..27.25; the driven side plate goes at y 27.25..; the other side plate rides
// an M4 bolt in a 624 bearing in the pivot plate (y -27..-22).
YFL = DS[2] / 2 - DS[2] + DS[4];   // flange underside, y = 8.25
module JS_place() { translate([0, DS[2] / 2, 0]) multmatrix([[0, -1, 0, 0], [0, 0, 1, 0], [-1, 0, 0, 0], [0, 0, 0, 1]]) children(); }

module joint_bracket(reach = 0) {   // reach: extend the frame along +u (past the servo body) to this u
    top = max(38, reach);
    difference() {
        union() {
            translate([-16, YFL - 3.5, -22]) cube([32, 3.5, top + 22]);                 // flange plate
            translate([-16, -27, -16]) cube([32, 5, (reach > 0 ? reach : 16) + 16]);   // pivot plate
            for (sx = [-1, 1]) translate([sx * 14 - 2, -27, -16]) cube([4, YFL + 27, (reach > 0 ? reach : 16) + 16]);
        }
        JS_place() { servo_cut(DS, 30); servo_holes(DS); }
        translate([0, -28, 0]) rotate([-90, 0, 0]) cylinder(d = 13.2, h = 5.1);           // 624
        rotate([90, 0, 0]) cylinder(d = 4.4, h = 80, center = true);
    }
}

// ---------------------------------------------------------------- turret (turret frame)
module turret() {
    color(C_BEIGE2) {
        rotate([0, 180, 0]) joint_bracket(reach = 44);       // body down; frame reaches z -44
        difference() {
            translate([0, 0, -50]) cylinder(r = 22, h = 6.01);
            translate([0, 0, -51]) cylinder(d = 8.1, h = 10);
            translate([12, 0, -47]) rotate([0, 90, 0]) cylinder(d = 3.2, h = 12);   // shaft clamp screw
        }
        translate([-16, -27, -44.01]) cube([32, YFL + 27, 6]);
    }
}
module SH_servo() { rotate([0, 180, 0]) JS_place() children(); }   // shoulder servo, turret frame

// ---------------------------------------------------------------- links (link frame: origin on proximal pitch axis)
module side_plate_2d() { hull() { circle(r = HUB_R); translate([XB0, -BEAM_Z]) square([8, 2 * BEAM_Z]); } }

module link_body(len) {
    // two side plates wrap the proximal joint bracket, a cross block joins them to a centre box beam
    difference() {
        union() {
            translate([0, DS[2] / 2 + HORN_Z + HORN_T, 0]) rotate([-90, 0, 0]) linear_extrude(PT) side_plate_2d();
            translate([0, -27.5, 0]) rotate([90, 0, 0]) linear_extrude(PT) side_plate_2d();
            translate([XB0, -27.5 - PT, -BEAM_Z]) cube([8, 55 + 2 * PT + 0.25, 2 * BEAM_Z]);
            translate([XB0, -BEAM_Y, -BEAM_Z]) cube([len - XB0, 2 * BEAM_Y, 2 * BEAM_Z]);
        }
        rotate([-90, 0, 0]) translate([0, 0, 20]) horn_holes(30);
        rotate([90, 0, 0]) cylinder(d = 4.3, h = 80, center = true);
        translate([XB0 + 10, -BEAM_Y + 2, -BEAM_Z + 2]) cube([len - XB0 - 20, 2 * BEAM_Y - 4, 2 * BEAM_Z - 4]);  // hollow beam
        translate([XB0 + 10, -BEAM_Y - 1, -4]) cube([len - XB0 - 20, 2 * BEAM_Y + 2, 8]);                    // cable slot
    }
}

module link1() {
    color(C_BEIGE) link_body(L1 - 36);
    color(C_BEIGE2) translate([L1, 0, 0]) {                  // elbow bracket, servo body pointing back
        rotate([0, -90, 0]) joint_bracket();
        translate([-44, -27, -16]) cube([8, YFL + 27, 32]);
    }
    for (x = [XB0 + 14, L1 - 50]) translate([x, 0, BEAM_Z]) hexhead(4.5, 1);
    // optional counterbalance spring anchor (tension spring to the turret)
    color(C_BEIGE2) translate([60, 0, BEAM_Z]) difference() { translate([-6, -4, 0]) cube([12, 8, 8]); translate([0, 5, 4]) rotate([90, 0, 0]) cylinder(d = 3.2, h = 10); }
}
module EL_servo() { translate([L1, 0, 0]) rotate([0, -90, 0]) JS_place() children(); }   // link1 frame

module link2() {
    X = L2 + TILT_OFF;
    color(C_BEIGE) difference() {
        union() {
            link_body(X + 16);
            translate([X - 16, -BEAM_Y, -BEAM_Z]) cube([32, YFL + 10.5 + BEAM_Y, 2 * BEAM_Z]);   // end block over the post
        }
        for (x = [X - 10, X + 10]) translate([x, 11, -20]) cylinder(d = 3.4, h = 40, $fn = 16);
    }
    for (x = [XB0 + 14, L2 - 10]) translate([x, 0, BEAM_Z]) hexhead(4.5, 1);
}

// tilt post (link2 frame): canonical joint bracket at the tilt axis, body up, narrow neck to link2
module tilt_post() {
    X = L2 + TILT_OFF; ZA = -TILT_DROP;
    color(C_BEIGE2) difference() {
        union() {
            translate([X, 0, ZA]) joint_bracket();
            translate([X - 16, YFL - 3.5, ZA + 37]) cube([22, 3.5, -BEAM_Z - (ZA + 37) - 4]);  // narrow neck (tilt clearance)
            translate([X - 16, YFL - 3.5, -BEAM_Z - 4]) cube([32, 14, 4]);                   // foot under the beam
        }
        for (x = [X - 10, X + 10]) translate([x, 11, -40]) cylinder(d = 2.6, h = 40, $fn = 16);
    }
}
module TL_servo() { translate([L2 + TILT_OFF, 0, -TILT_DROP]) JS_place() children(); }   // link2 frame

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
