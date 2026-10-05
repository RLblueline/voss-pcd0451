// =====================================================================
// V.O.S.S. (PCD-0451) wall terminal - parametric CAD, v0.5
// Frame: X along wall, Y out of wall, Z up. Wall face y = 0. Units: mm.
// Shoulder axis at (0, SY, 0). All joints are horizontal-plane forks except
// the head tilt (horizontal axis). Every part is modelled in its own local
// frame; assembly transforms are in assembly.scad and tools/collide.py.
// =====================================================================

$fn = 48;
COSMETIC = true;    // false = leave out cosmetic-only geometry (print exports)
ARM_Z0   = 70;      // shoulder / yaw-turret height above the housing origin (arm sits above the housing top)
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
// desk-lamp counterbalance (zero-length spring emulation): pulley P directly above the shoulder
// axis, cable eye Q on link1's axis line, both in the plane y = SPR_Y
SPR_A    = 96;      // pulley centre height above the shoulder axis
SPR_B    = 50;      // cable eye distance along link1
SPR_Y    = -42;     // cable plane (outside link1's side plate)
SPR_D    = 49;      // cable-length offset (set with the tensioner); spring stretch = (|PQ| - d) / 2
SPR_L0   = 55;      // spring free length (incl. hooks); 2:1 reeving halves its travel
SPR_COL  = -8.5;    // spring / spring-block centre x (strands at x -5 and -12)
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
HEAD_XB_T = -105;    // back of the head at the crown (stretched back)
HEAD_XB_B = -80;     // back of the head at z -230 (top half longer than the bottom)
HS = 15;             // shell frame -> tilt-axis frame shift (puts the deeper head's CG under the axis)
SHELL = 2.4;
SPLIT1 = -40; SPLIT2 = -195;
SEAM_X = [-60, 32];                 // seam screw positions (x), at each side wall
SEAM_Y = [63, 59.5];                // per seam (top/mid, mid/chin): bosses merge into the side walls
EYE_Z = -116;        // eye centre
EYE_Y = 40;          // cavity half width
EYE_Z0 = -184; EYE_Z1 = -48;   // cavity bottom / top
BEZEL_X = 29;        // back of the eye recess (slotted plate 27..29)
EYE_TRAVEL = 24;     // eye carriage moves +-24 mm up/down the slot
LIFT_R = 18;         // lift pinion pitch radius (module 1, 36 T)
LENS_D = 60;
SHUT_TRAVEL = 27;    // per plate; slit 12 mm when closed
PIN_R = 9; PIN_M = 1; PIN_Y = 48;
CAR_RODY = 30;       // carriage guide rods at y = +-30
EAR_P = [27.25, 30.75];     // + ear (on tilt horn)
EAR_N = [-31.0, -27.5];     // - ear (on pivot bolt)

// =====================================================================
// helpers
// =====================================================================
module rrect(x, y, r) { offset(r) offset(-r) square([x, y], center = true); }
module rbox(size, r) { linear_extrude(size[2]) rrect(size[0], size[1], r); }
module hexhead(d = 5.5, h = 1.2) { if (COSMETIC) color(C_BLACK) difference() { cylinder(d = d * 1.15, h = h, $fn = 6); translate([0,0,h-0.6]) cylinder(d = 2.5, h = 1, $fn = 6); } }

// involute spur gear, 20 deg pressure angle, ~0.1 mm backlash; tooth 0 points along +x
function _inv(t) = t - atan(t) * PI / 180;
module gear2d(m, z, pa = 20, bl = 0.1) {
    rp = m * z / 2; rb = rp * cos(pa); ra = rp + m; rf = rp - 1.25 * m;
    tmax = sqrt(ra * ra / (rb * rb) - 1);
    half = 90 / z - (bl / (2 * rp)) * 180 / PI + (tan(pa) - pa * PI / 180) * 180 / PI;
    n = 10;
    flank = [for (i = [0 : n]) let(t = tmax * i / n, r = rb * sqrt(1 + t * t), a = half - _inv(t) * 180 / PI) [r * cos(a), r * sin(a)]];
    union() {
        circle(r = rf, $fn = z * 6);
        for (k = [0 : z - 1]) rotate(k * 360 / z)
            polygon(concat([[rf * cos(half + 2), rf * sin(half + 2)]], flank,
                           [for (i = [n : -1 : 0]) [flank[i][0], -flank[i][1]]], [[rf * cos(half + 2), -rf * sin(half + 2)]]));
    }
}
// 21-tooth SG90 output spline bore (press fit); the M2 horn screw goes through the hub
module sg_spline_2d() { polygon([for (i = [0 : 41]) let(r = i % 2 ? 2.45 : 2.2) [r * cos(i * 360 / 42), r * sin(i * 360 / 42)]]); }


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
        // speaker grille (40 mm speaker), left of the yaw tower
        for (r = [0, 6, 12], a = [0 : (r == 0 ? 360 : 360 / (r == 6 ? 8 : 14)) : 359])
            translate([-50 + r * cos(a), HD - 5, -40 + r * sin(a)]) rotate([-90, 0, 0]) cylinder(d = 3.2, h = 10, $fn = 12);
        // printer paper exit + tear bar in the bottom face (memos drop out under the housing)
        translate([-31, 38, HZ0 - 1]) cube([62, 4.5, 8]);
        translate([-36, 34, HZ0 - 1]) cube([72, 13, 1.2 + 1]);
        // shoulder bracket screws + servo cable
        for (x = [-24, 24], z = [-136, -52]) translate([x, HD - 5, z + ARM_Z0]) rotate([-90, 0, 0]) cylinder(d = 3.4, h = 10, $fn = 16);
        translate([0, HD - 5, -90 + ARM_Z0]) rotate([-90, 0, 0]) cylinder(d = 12, h = 10);
        // power jacks (5 V logic, 6 V servo) in the right side, vents in both sides
        for (z = [-170, -150]) translate([HW / 2 - 5, 30, z]) rotate([0, 90, 0]) cylinder(d = 8, h = 10);
        for (sx = [-1, 1], z = [-110 : 8 : -60]) translate([sx * (HW / 2 - 5) - 5, 15, z]) cube([10, 40, 3]);
        // back-plate screws through the side walls
        for (sx = [-1, 1], z = [10, -160]) translate([sx * (HW / 2 - 5), 2, z]) rotate([0, 90, 0]) cylinder(d = 3.4, h = 12, center = true, $fn = 16);
        // front lettering (debossed)
        translate([0, HD - 0.6, -174]) rotate([90, 0, 180]) linear_extrude(1) text("APERTURE SCIENCE", size = 7, font = FONT, halign = "center");
        translate([0, HD - 0.6, -184]) rotate([90, 0, 180]) linear_extrude(1) text("V.O.S.S.  HR TERMINAL  PCD-0451", size = 4.2, font = MONO, halign = "center");
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
module YAW_local() { translate([0, SY, -131]) rotate([0, 0, 90]) children(); }
module YAW_place() { translate([0, 0, ARM_Z0]) YAW_local() children(); }   // MG996R, shaft up

module yaw_tower() { translate([0, 0, ARM_Z0]) yaw_tower_local(); }
module yaw_tower_local() {
    module shelf(z0, t, front) translate([0, 0, z0]) linear_extrude(t) hull() {
        translate([-16, HD + 4]) square([32, 1]); translate([0, SY]) circle(r = front);
    }
    difference() {
        union() {
            translate([-30, HD, -148]) cube([60, 4, 102]);                                 // wall plate
            shelf(-60, 8, 15);                                                            // upper 608
            shelf(-112, 8, 15);                                                           // lower 608
            translate([0, 0, -144.5]) linear_extrude(3) hull() {                          // servo shelf
                translate([-16, HD + 4]) square([32, 1]); translate([-16, SY + 18]) square([32, 1]); }
            for (sx = [-1, 1]) translate([sx * 14.5 - 1.5, HD + 4, -148]) cube([3, SY - 14 - HD - 4, 96]);
        }
        for (z = [-59.1, -111.1]) translate([0, SY, z]) cylinder(d = 22.2, h = 7.2);
        translate([0, SY, -150]) cylinder(d = 10, h = 120);
        YAW_local() { servo_cut(MG, 30); servo_holes(MG); }
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
        spring_mast();
    }
}

// spring mast on the turret: a column in the cable plane with ONE pulley directly above the
// shoulder axis, so link1's cable eye, the pulley and the spring are coplanar. Everything here
// sits above the housing top at every yaw.
module spring_mast() {   // 2:1 reeving: eye -> top pulley -> down -> spring-block pulley -> up to the anchor pin
    cx = SPR_COL; y0 = SPR_Y;
    difference() {
        union() {
            translate([-18, y0 - 9, -30]) cube([17.5, 18, SPR_A + 9 + 30]);                   // column
            translate([-10, y0 - 9, SPR_A - 9]) cube([20, 18, 18]);                          // pulley head
            translate([-20, y0 - 9, -30]) cube([22, -y0 - 22 + 9 + 0.01, 6]);                // bracket to the pivot plate
        }
        translate([-16, y0 - 7.5, -26]) cube([15, 15, SPR_A + 20]);                          // spring bore
        translate([-20, y0 - 2.5, -10]) cube([5, 5, SPR_A - 25]);                            // window: see the spring
        translate([0, y0, SPR_A]) rotate([90, 0, 0]) cylinder(r = 6.5, h = 5.4, center = true);   // top pulley slot
        translate([0, y0 - 2.7, SPR_A - 30]) cube([12, 5.4, 30]);                            // cable entry, front-low
        translate([0, y0, SPR_A]) rotate([90, 0, 0]) cylinder(d = 3.2, h = 30, center = true);  // M3 axle
        translate([-12, y0, SPR_A - 10]) rotate([90, 0, 0]) cylinder(d = 3.2, h = 30, center = true);    // cable anchor pin
        translate([cx, y0, -40]) cylinder(d = 3.4, h = 20);                                  // tensioner screw
    }
}
module spring_block() {  // rides on the spring: 7 mm pulley on an M3 axle, hook hole underneath
    difference() {
        translate([-6, -5, -9]) cube([12, 10, 16]);
        translate([-7, -3, -4]) cube([14, 6, 12]);                                          // pulley slot
        rotate([90, 0, 0]) cylinder(d = 3.2, h = 12, center = true);
        translate([0, 0, -7]) rotate([90, 0, 0]) cylinder(d = 2.5, h = 12, center = true);  // spring hook
    }
}
module pulley_small() { rotate_extrude($fn = 40) difference() { translate([1.6, -2.4]) square([2.1, 4.8]); translate([4.1, 0]) circle(r = 0.9, $fn = 16); } }
module pulley() {        // 10 mm cable pulley, 5 wide, M3 axle
    rotate_extrude($fn = 48) difference() { translate([1.6, -2.5]) square([3.6, 5]); translate([5.6, 0]) circle(r = 1.1, $fn = 16); }
}
module yaw_coupler() {   // MG996R horn -> 8 mm yaw shaft (turret frame)
    difference() {
        union() { translate([0, 0, -124]) cylinder(d = HORN_D, h = 3); translate([0, 0, -121]) cylinder(d = 18, h = 8); }
        translate([0, 0, -125]) horn_holes(6);
        translate([0, 0, -122]) cylinder(d = 8.05, h = 20, $fn = 32);
        translate([0, 0, -117]) rotate([0, 90, 0]) cylinder(d = 4.2, h = 20);
    }
}
module SH_servo() { rotate([0, 180, 0]) JS_place() children(); }   // shoulder servo, turret frame

// ---------------------------------------------------------------- links (link frame: origin on proximal pitch axis)
module side_plate_2d() { hull() { circle(r = HUB_R); translate([XB0, -BEAM_Z]) square([8, 2 * BEAM_Z]); } }

module link_body(len, pads = []) {
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
        difference() {
            translate([XB0 + 10, -BEAM_Y + 2, -BEAM_Z + 2]) cube([len - XB0 - 20, 2 * BEAM_Y - 4, 2 * BEAM_Z - 4]);  // hollow beam
            for (x = pads) translate([x - 5, -BEAM_Y, -BEAM_Z]) cube([10, 2 * BEAM_Y, 2 * BEAM_Z]);   // solid pads
        }
        for (x = pads) translate([x, 0, BEAM_Z - 7]) cylinder(d = 4.2, h = 8, $fn = 20);   // M3 inserts for the cover
        translate([XB0 + 10, -BEAM_Y - 1, -4]) cube([len - XB0 - 20, 2 * BEAM_Y + 2, 8]);                    // cable slot
    }
}

module link1() {
    color(C_BEIGE) link_body(L1 - 36, pads = [52, 68]);
    color(C_BEIGE2) translate([L1, 0, 0]) {                  // elbow bracket, servo body pointing back
        rotate([0, -90, 0]) joint_bracket();
        translate([-44, -27, -16]) cube([8, YFL + 27, 32]);
    }
    for (x = [XB0 + 14, L1 - 50]) translate([x, 0, BEAM_Z]) hexhead(4.5, 1);
    // counterbalance cable eye on the axis line, in the spring plane
    color(C_BEIGE2) difference() {
        hull() {
            translate([XB0, -27.5 - PT, -8]) cube([8, 1, 16]);
            translate([SPR_B, SPR_Y, 0]) rotate([90, 0, 0]) cylinder(r = 5, h = 5, center = true);
        }
        translate([SPR_B, SPR_Y, 0]) rotate([90, 0, 0]) cylinder(d = 3, h = 10, center = true);
    }
}
module EL_servo() { translate([L1, 0, 0]) rotate([0, -90, 0]) JS_place() children(); }   // link1 frame

module link2() {
    X = L2 + TILT_OFF;
    color(C_BEIGE) difference() {
        union() {
            link_body(X + 16, pads = [52, 90]);
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
// outer envelope (shell frame): flat front, deep back that is longer at the crown, tapered chin
module head_slab(z, xb, xf, hy, r, inset) {
    translate([(xb + xf) / 2, 0, z]) linear_extrude(0.01) rrect(xf - xb - 2 * inset, 2 * hy - 2 * inset, r);
}
module head_solid(inset = 0) {
    hull() {
        head_slab(HEAD_TOP - inset - 0.01, HEAD_XB_T, HEAD_X, HEAD_Y, 9, inset);
        head_slab(-230, HEAD_XB_B, HEAD_X, HEAD_Y - 6, 9, inset);
        head_slab(HEAD_BOT + inset, -52, 38, 46, 6, inset);
    }
}
module head_frame() { translate([HS, 0, 0]) children(); }   // shell frame -> tilt-axis frame

module cavity_2d() { rrect(EYE_Z1 - EYE_Z0, 2 * EYE_Y, 18); }

module head_features_cut() {
    // eye cavity: rounded vertical recess down to the bezel
    translate([BEZEL_X - 0.01, 0, (EYE_Z0 + EYE_Z1) / 2]) rotate([0, 90, 0]) linear_extrude(30) cavity_2d();
    // chin "printer" slot
    translate([HEAD_X - 6, -46, -212]) cube([12, 92, 4]);
    // status windows REC AUD OK (viewer's right = +Y)
    for (y = [14, 34, 54]) translate([HEAD_X - 6, y, 12]) rotate([0, 90, 0]) linear_extrude(12) rrect(9, 15, 1.5);
    // M3 screws through the side walls into the eye rod-mount bars
    for (sy = [-1, 1], pz = [[-3, -45], [-3, -187], [-27, -187]]) translate([pz[0], sy * 60, pz[1]]) rotate([90, 0, 0]) cylinder(d = 3.4, h = 30, center = true, $fn = 16);
    // neck slot: open through the crown and the whole upper back, so the post, the service tubes
    // and a wide tilt range all fit (defined in the tilt-axis frame: x <= 32)
    translate([-250, EAR_N[1], -28]) cube([250 + 40 - HS, EAR_P[0] - EAR_N[1], 80]);
    translate([-250, -35, -28]) cube([250 - 36 - HS, 70, 80]);      // wider behind the ears: link2's cross block dips in on deep nods
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
        intersection() { head_shell(); translate([-200, -100, zs[i][0]]) cube([400, 200, zs[i][1] - zs[i][0]]); }
        // alignment lip on the lower edge of the upper pieces (fused 3 mm up, 5 mm skirt down)
        if (i < 2) difference() {
            union() {
                intersection() { difference() { head_solid(SHELL - 0.6); head_solid(SHELL + 1.6); }
                                 translate([-200, -100, zs[i][0]]) cube([400, 200, 3]); }
                intersection() { difference() { head_solid(SHELL + 0.2); head_solid(SHELL + 1.6); }
                                 translate([-200, -100, zs[i][0] - 5]) cube([400, 200, 5.01]); }
            }
            head_features_cut();
            translate([BEZEL_X - 0.5, 0, (EYE_Z0 + EYE_Z1) / 2]) rotate([0, 90, 0]) linear_extrude(HEAD_X) offset(SHELL + 3) cavity_2d();
        }
        if (i == 0) translate([-HS, 0, 0]) head_ears();    // ears are printed with the crown
        // internal screw bosses at the seams
        // seam joints: insert boss on the upper piece, clearance boss on the lower piece; M3 x 16
        // screws go up from inside the lower piece into heat-set inserts
        if (i < 2) for (x = SEAM_X, sy = [-1, 1]) intersection() {
            translate([x, sy * SEAM_Y[i], zs[i][0]]) difference() { cylinder(d = 8, h = 10); translate([0,0,-1]) cylinder(d = 4.2, h = 7); }
            head_solid(0.5);
        }
        if (i > 0) for (x = SEAM_X, sy = [-1, 1]) intersection() {
            translate([x, sy * SEAM_Y[i - 1], zs[i][1] - 15.5]) difference() { cylinder(d = 8, h = 10); translate([0,0,-1]) cylinder(d = 3.4, h = 12); }
            head_solid(0.5);
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
                circle(r = 16); translate([-30, HEAD_TOP - SHELL - 6]) square([60, 6.8]);
            }
            translate([0, 20, 0]) rotate([-90, 0, 0]) horn_holes(40);
        }
        // - ear rides the pivot bolt
        difference() {
            translate([0, EAR_N[0], 0]) rotate([90, 0, 0]) mirror([0,0,1]) linear_extrude(EAR_N[1] - EAR_N[0]) hull() {
                circle(r = 16); translate([-30, HEAD_TOP - SHELL - 6]) square([60, 6.8]);
            }
            rotate([90, 0, 0]) cylinder(d = 4.3, h = 80, center = true);
        }
    }
}

// ----------------------------------------------------------------- moving eye (shell frame)
// The eye rides a carriage that slides +-EYE_TRAVEL up and down the slot on two 3 mm rods,
// lifted by an SG90 with a 36 T pinion on a rack. The shutter eyelids ride on the carriage.
// x stack (front to back): face 45 | recess | slotted plate 27..29 | carriage mask 25..26.6 |
// shutters 22.6..24.6 | racks + pinion 18.8..22.4 | rails 15.4..18.6 | lens 13..21 |
// LED ring 8..12 | rear plate 3..6 | bushings + lift rack -4..3 | rods x -0.5 | mount bars -8..2
SHX = [22.6, 24.6]; RKX = [18.8, 22.4]; RLX = [15.4, 18.6]; MASKX = [25, 26.6];
SG_TOP_X = RKX[0] - 4;
LIFT_C = [-19.25, -20, EYE_Z];   // lift pinion centre (axis along Y)

module SG_place_local() { multmatrix([[0, 0, 1, SG_TOP_X], [0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]]) children(); }
module LIFT_place() { translate([LIFT_C[0], -26, LIFT_C[2]]) multmatrix([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]]) children(); }
module slot_2d() { hull() for (z = [-EYE_TRAVEL, EYE_TRAVEL]) translate([z, 0]) circle(r = 34, $fn = 96); }

module eye_plate() {          // fixed, visible back of the recess, with the travel slot
    color(C_CHAR) difference() {
        translate([BEZEL_X - 2, -EYE_Y - 6, EYE_Z0 - 6]) cube([2, 2 * EYE_Y + 12, EYE_Z1 - EYE_Z0 + 12]);
        translate([BEZEL_X - 3, 0, EYE_Z]) rotate([0, 90, 0]) linear_extrude(5) slot_2d();
    }
}
function inner_y(z) = HEAD_Y - 6 * (HEAD_TOP - z) / 260 - SHELL;    // shell inner half-width (straight sides)
module eye_rods(rods = true) {  // fixed: guide rods + mount bars + lift servo strut
    if (rods) color(C_STEEL) for (y = [-CAR_RODY, CAR_RODY]) translate([-0.5, y, -190]) cylinder(d = 3, h = 148, $fn = 16);
    ht = inner_y(-45) - 0.2; hb = inner_y(-187) - 0.2;
    color(C_CHAR) {
        difference() {
            union() {
                translate([-8, -ht, -48]) cube([10, 2 * ht, 6]);
                translate([-32, -hb, -190]) cube([34, 2 * hb, 6]);
                translate([-30, -36, -184]) cube([8, 6, 56.01]);                         // lift servo strut
                translate([-40, -35.3, EYE_Z - 12]) cube([32, 2.5, 24]);                // lift servo plate
            }
            for (y = [-CAR_RODY, CAR_RODY]) translate([-0.5, y, -200]) cylinder(d = 3.1, h = 200, $fn = 16);
            LIFT_place() { servo_cut(SG, 30); servo_holes(SG); }
            for (sy = [-1, 1]) {                                                               // M3 inserts in the bar ends
                translate([-3, sy * ht, -45]) rotate([90, 0, 0]) cylinder(d = 4.2, h = 12, center = true, $fn = 16);
                for (x = [-3, -27]) translate([x, sy * hb, -187]) rotate([90, 0, 0]) cylinder(d = 4.2, h = 12, center = true, $fn = 16);
            }
        }
    }
}
module lift_drive(ze = EYE_Z) {
    color(C_HORN) translate([LIFT_C[0], -22, LIFT_C[2]]) lift_pinion(ze);
    LIFT_place() servo(SG, horn = false);
}
module eye_carriage(ze = EYE_Z) {
    color([0.24, 0.24, 0.26]) difference() {                                            // mask (eye socket)
        translate([MASKX[0], -50, ze - 83]) cube([MASKX[1] - MASKX[0], 110, 166]);
        translate([MASKX[0] - 1, 0, ze]) rotate([0, 90, 0]) cylinder(d = LENS_D + 6, h = 5, $fn = 96);
    }
    color(C_CHAR) {
        difference() {                                                                   // rear plate
            translate([3, -50, ze - 42]) cube([3, 110, 84]);
            translate([2, 0, ze]) rotate([0, 90, 0]) cylinder(d = 20, h = 5);
            translate([2, PIN_Y - 6.6, ze - 17.1]) cube([5, 13.2, 23.5]);
        }
        for (z = [ze - 40, ze + 36]) translate([3, -50, z]) cube([MASKX[0] - 3, 4, 4]);     // left standoffs
        translate([3, PIN_Y + 10.25, ze + 36]) cube([RLX[0] - 3 + 0.01, 3.25, 4]);         // right: rear plate -> rail
        translate([RLX[1] - 0.01, PIN_Y + 10.25, ze + 70]) cube([MASKX[0] - RLX[1] + 0.02, 3.25, 4]);  // rail -> mask, above the racks
        translate([5.5, 0, ze]) rotate([0, 90, 0]) difference() {                          // lens holder + seat lip
            cylinder(d = LENS_D + 8, h = 10.5, $fn = 96);
            translate([0, 0, -1]) cylinder(d = LENS_D - 4, h = 13, $fn = 96);
            translate([0, 0, 7.5]) cylinder(d = LENS_D + 0.6, h = 4, $fn = 96); }
        difference() {                                                                   // left guide rail
            translate([RKX[0] + 1.2, -49, ze - 80]) cube([MASKX[0] - RKX[0] - 1.2, 6, 160]);
            translate([SHX[0] - 0.4, -45, ze - 81]) cube([SHX[1] - SHX[0] + 0.8, 3.2, 162]);
        }
        translate([RLX[0], PIN_Y - 14, ze - 24]) cube([RLX[1] - RLX[0], 3.75, 100]);       // rack backing rails
        translate([RLX[0], PIN_Y + 10.25, ze - 24]) cube([RLX[1] - RLX[0], 3.25, 100]);
        translate([3, PIN_Y - 14, ze + 36]) cube([RLX[0] - 3 + 0.01, 3.75, 4]);
        difference() {                                                                   // shutter SG90 mount
            translate([5.5, PIN_Y - 8.4, ze - 28]) cube([2.5, 17, 46]);
            translate([0, PIN_Y, ze]) SG_place_local() { servo_cut(SG, 30); servo_holes(SG); }
        }
        translate([5.5, PIN_Y - 8.4, ze - 28]) cube([RLX[1] - 5.5, 2, 46]);
        translate([5.5, PIN_Y + 6.6, ze - 28]) cube([RLX[1] - 5.5, 2, 46]);
        for (y = [-CAR_RODY, CAR_RODY], z = [ze - 42, ze + 28]) difference() {             // rod bushings
            translate([-4, y - 5, z]) cube([7.01, 10, 14]);
            translate([-0.5, y, z - 1]) cylinder(d = 3.3, h = 16, $fn = 16);
        }
        translate([0, -22, ze - 35]) cube([3.01, 4, 70]);                                 // lift rack (pitch line x -1.25)
        translate([0, -18, ze - 35]) rotate([90, 0, 0]) linear_extrude(4)
            for (k = [0 : 22]) let(c = 2.013 + k * RACK_P) if (c + 1.19 <= 70) rack_tooth_2d(0.01, -2.25, c);
    }
    color(C_AMBER) translate([13, 0, ze]) rotate([0, 90, 0]) intersection() {             // lens dome
        translate([0, 0, -60.25 + 8]) sphere(r = 60.25, $fn = 128);
        cylinder(d = LENS_D, h = 8, $fn = 96);
    }
    color(C_PCB) translate([6, 0, ze]) rotate([0, 90, 0]) difference() { cylinder(d = 44, h = 1.6); translate([0,0,-1]) cylinder(d = 32, h = 4); }
    for (a = [0 : 360 / 16 : 359]) color([1, 0.75, 0.4]) translate([8.2, 19 * cos(a), ze + 19 * sin(a)]) cube([1.2, 4, 4], center = true);
}

// shutter eyelids on the carriage; s = 1 open, 0 closed (12 mm squint slit)
RACK_P = PI * PIN_M;     // 3.1416 mm pitch, 20 deg flanks, matches gear2d
module rack_tooth_2d(root, tip, c) {        // in (across, along) coordinates
    polygon([[root, c - 1.19], [tip, c - 0.371], [tip, c + 0.371], [root, c + 1.19]]);
}
// rack along +z from z0 with its pitch line at y = yp; teeth face +y (dir 1) or -y (dir -1)
module rack(yp, z0, dir, len = 50, w = 3.75, phase = 0) {
    root = yp - dir * 1.25 * PIN_M; tip = yp + dir * PIN_M;
    translate([RKX[0], dir > 0 ? root - w : root, z0]) cube([RKX[1] - RKX[0], w, len]);
    translate([RKX[0], 0, z0]) rotate([90, 0, 90]) linear_extrude(RKX[1] - RKX[0])
        for (k = [0 : floor(len / RACK_P)]) let(c = phase + k * RACK_P)
            if (c - 1.19 >= 0 && c + 1.19 <= len) rack_tooth_2d(root - dir * 0.01, tip, c);
}
module shutter_top(s = 1, ze = EYE_Z) {
    zb = ze + 6 + SHUT_TRAVEL * s;
    color(C_ALU) {
        translate([SHX[0], -42, zb]) cube([SHX[1] - SHX[0], 84, 40]);
        translate([SHX[0], -44.6, zb]) cube([SHX[1] - SHX[0], 3, 40]);
        rack(PIN_Y - PIN_R, zb - 40, 1, 50, 3.75, 1.013);       // phase: tooth space at the pinion when closed
        translate([RKX[1] - 0.01, PIN_Y - 14, zb]) cube([SHX[0] - RKX[1] + 0.02, 3.75, 10]);
    }
}
module shutter_bottom(s = 1, ze = EYE_Z) {
    zt = ze - 6 - SHUT_TRAVEL * s;
    color(C_ALU) {
        translate([SHX[0], -42, zt - 40]) cube([SHX[1] - SHX[0], 84, 40]);
        translate([SHX[0], -44.6, zt - 40]) cube([SHX[1] - SHX[0], 3, 40]);
        translate([RKX[0], 42.5, zt - 14]) cube([SHX[1] - RKX[0], PIN_Y + 12 - 42.5, 8]);
        translate([SHX[0], 41.9, zt - 14]) cube([SHX[1] - SHX[0], 0.7, 14]);
        rack(PIN_Y + PIN_R, zt - 14, -1, 60, 3.25, 2.72);
    }
}
module shutter_pinion(s = 1) {     // 18 T, module 1; tooth faces each rack when closed
    rotate([0, 90, 0]) rotate(10 - SHUT_TRAVEL * s / PIN_R * 180 / PI) linear_extrude(RKX[1] - RKX[0] - 0.4)
        difference() { gear2d(PIN_M, 2 * PIN_R / PIN_M); sg_spline_2d(); }
}
module lift_pinion(ze = EYE_Z) {    // 36 T, module 1; axis along Y
    rotate([-90, 0, 0]) rotate(-(ze - EYE_Z) / LIFT_R * 180 / PI) linear_extrude(4)
        difference() { gear2d(PIN_M, 2 * LIFT_R / PIN_M); sg_spline_2d(); }
}
module shutter_drive(s = 1, ze = EYE_Z) {
    color(C_HORN) translate([RKX[0] + 0.2, PIN_Y, ze]) shutter_pinion(s);
    translate([0, PIN_Y, ze]) SG_place_local() servo(SG, horn = false);
}
module eye_all(s = 1, ze = EYE_Z) {
    eye_plate(); eye_rods(); lift_drive(ze); eye_carriage(ze);
    shutter_top(s, ze); shutter_bottom(s, ze); shutter_drive(s, ze);
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

// Original department seal (not the Aperture logo): ring text + stacked filing drawers + "04"
module seal(d = 46, h = 0.8) {
    t = "PERSONNEL COMPLIANCE * BRANCH 04 * ";
    n = len(t);
    color(C_CHAR) {
        difference() { cylinder(d = d, h = h, $fn = 96); translate([0, 0, -1]) cylinder(d = d - 2, h = h + 2, $fn = 96); }
        difference() { cylinder(d = d * 0.62, h = h, $fn = 96); translate([0, 0, -1]) cylinder(d = d * 0.62 - 1.6, h = h + 2, $fn = 96); }
        for (i = [0 : n - 1]) rotate(90 - i * 360 / n) translate([0, d * 0.40]) rotate(0)
            linear_extrude(h) text(t[i], size = d * 0.075, font = MONO, halign = "center", valign = "center");
        linear_extrude(h) for (k = [0 : 2]) translate([-d * 0.13, d * 0.09 - k * d * 0.085]) {   // filing drawers
            difference() { square([d * 0.26, d * 0.07]); translate([d * 0.02, d * 0.015]) square([d * 0.22, d * 0.04]); }
            translate([d * 0.105, d * 0.025]) square([d * 0.05, d * 0.02]);
        }
        translate([0, -d * 0.19]) linear_extrude(h) text("04", size = d * 0.08, font = FONT, halign = "center", valign = "center");
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
        translate([0, HD - 0.5, -174]) rotate([90, 0, 180]) linear_extrude(0.6) text("APERTURE SCIENCE", size = 7, font = FONT, halign = "center");
        translate([0, HD - 0.5, -184]) rotate([90, 0, 180]) linear_extrude(0.6) text("V.O.S.S.  HR TERMINAL  PCD-0451", size = 4.2, font = MONO, halign = "center");
    }
    // department seal, top centre of the housing front
    translate([46, HD - 0.01, -2]) rotate([90, 0, 180]) seal(36, 0.8);
    color(C_BLACK) {
    }
}

module head_seal() {   // on the viewer's left (-Y) side face
    a = atan(6 / 260);
    translate([-52, -HEAD_Y, HEAD_TOP]) rotate([a, 0, 0]) translate([0, 0, -125]) rotate([90, 0, 0]) seal(64, 0.8);
}

module bumper() { color(C_BLACK) translate([-7, 0, HEAD_BOT - 8]) cylinder(d = 22, h = 8.5); }

module neck_boot() {     // one-piece TPU bellows, 1.2 mm wall
    pts = [for (k = [0 : 12]) [k % 2 ? 18.5 : 21, HEAD_TOP + 1 + k * 2.3]];
    color([0.12, 0.12, 0.12]) translate([-2, 0, 0]) scale([1.25, 1.35, 1]) rotate_extrude($fn = 48)
        for (k = [0 : 11]) hull() { translate(pts[k]) circle(r = 0.6, $fn = 10); translate(pts[k + 1]) circle(r = 0.6, $fn = 10); }
}

module head_internals(s = 1, ze = EYE_Z) {
    head_ears();
    head_frame() { eye_all(s, ze); status_leds(); color([0.85, 0.8, 0.66, 0.18]) head_piece(2); }
}

module head_all(s = 1, cosmetic = true, ze = EYE_Z) {
    head_frame() {
        for (i = [0 : 2]) head_piece(i);
        eye_all(s, ze);
        status_leds();
        paper_strip();
        bumper();
        if (cosmetic) { dymo_labels(); head_inlays(); head_seal(); }
    }
    if (cosmetic) neck_boot();
}

// =====================================================================
// ARM COVERS + WIRE HARNESS (top-only shrouds, open underneath)
// =====================================================================
module cover_profile() {
    difference() {
        translate([0, 14.5]) rrect(30, 21, 5);                 // y +-15, z 4..25
        translate([0, 12.5]) square([26, 21], center = true);  // open bottom, 2 mm walls
    }
}
module arm_cover(x0, x1) {
    color(C_BEIGE) difference() {
        hull() {
            translate([x0 + 4, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0 - 8) offset(0) translate([0, 0]) cover_profile_outer();
            translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) offset(-3) cover_profile_outer();
        }
        translate([x0 - 1, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0 + 2) translate([0, 12.5]) square([26, 21], center = true);
        for (x = [x0 + 6, x1 - 6]) translate([x, 0, 20]) cylinder(d = 3, h = 10);      // clip screws
    }
    for (x = [x0 + 6, x1 - 6]) translate([x, 0, 25]) hexhead(4.5, 0.8);
}
module cover_profile_outer() { translate([0, 14.5]) rrect(30, 21, 5); }

// wire bundle along the top of a beam (servo leads + LED/mic/eye lines), with zip ties
module harness(x0, x1, z = 15) {
    cols = [[0.75, 0.1, 0.1], [0.08, 0.08, 0.08], [0.9, 0.75, 0.1], [0.15, 0.3, 0.75], [0.85, 0.85, 0.85]];
    for (i = [0 : 4]) color(cols[i]) translate([x0, -3.6 + i * 1.8, z + (i % 2) * 1.6]) rotate([0, 90, 0]) cylinder(d = 1.8, h = x1 - x0, $fn = 10);
    color(C_BLACK) for (x = [x0 + 8 : 22 : x1 - 4]) translate([x, 0, z + 0.8]) rotate([0, 90, 0]) difference() { cylinder(d = 8.4, h = 2, $fn = 20); translate([0,0,-1]) cylinder(d = 7, h = 4, $fn = 20); }
}

// corrugated service tube along a quadratic curve
module service_tube(p0, p1, p2, d = 6, n = 28) {
    color([0.1, 0.1, 0.1]) for (i = [0 : n - 1]) hull() for (t = [i / n, (i + 1) / n])
        translate((1 - t) * (1 - t) * p0 + 2 * t * (1 - t) * p1 + t * t * p2) sphere(d = d, $fn = 12);
    color([0.16, 0.16, 0.16]) for (i = [1 : n - 1]) let(t = i / n)
        translate((1 - t) * (1 - t) * p0 + 2 * t * (1 - t) * p1 + t * t * p2) sphere(d = d * 1.2, $fn = 12);
}

// =====================================================================
// electronics placeholders (world frame)
// =====================================================================
module electronics() {
    color(C_PCB) translate([-32.5, BP_T + 5, -38]) cube([65, 1.6, 30]);                 // Pi Zero 2 W
    color(C_PCB) translate([-31, BP_T + 5, -84]) cube([62, 1.6, 25.4]);                 // PCA9685
    color(C_PCB) translate([-60, HD - 26, -75]) cube([18, 1.6, 18]);                    // MAX98357A
    color(C_SERVO) translate([-50, HD - 13, -40]) rotate([-90, 0, 0]) cylinder(d = 40, h = 9);  // speaker
    for (x = [-40, 40]) color(C_PCB) translate([x - 7, HD - 6.5, 13]) cube([14, 1.6, 14]); // INMP441
    color([0.85, 0.85, 0.85]) translate([-40, 14, -185]) cube([80, 50, 55]);            // 58 mm printer, exit facing down
    color([0.15, 0.15, 0.6]) translate([45, 10, -30]) cylinder(d = 10, h = 16);          // 1000 uF
}
