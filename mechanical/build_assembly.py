# -*- coding: utf-8 -*-
"""
RGBWYV-Light - parametric FreeCAD assembly (board + enclosure + thermal parts)

Run headless:   freecadcmd build_assembly.py
  (Flatpak:     flatpak run --command=freecadcmd org.freecad.FreeCAD build_assembly.py)
Or in the GUI:  Macro > Macros... > build_assembly.py  (adds colours/transparency)

Writes RGBWYV-Light_assembly.FCStd and RGBWYV-Light_assembly.step next to this file.
Key dimensions live in the "Params" spreadsheet; box/lid/standoffs/cone/LED sink are
bound to it by expressions, so edit a cell and hit Recompute.

Coordinate frame = KiCad STEP export with --user-origin at board centre
(124.715, 110.235 mm in the PCB):  X = pcb_x - 124.715,  Y = -(pcb_y - 110.235),
Z = 0 at the board bottom, +Z = component/LED side (up, towards the lid).
"""
import os, math
import FreeCAD as App
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_STEP = os.path.join(HERE, "RGBWYV-Light_PCB.step")
OUT_FCSTD = os.path.join(HERE, "RGBWYV-Light_assembly.FCStd")
OUT_STEP = os.path.join(HERE, "RGBWYV-Light_assembly.step")
IN = 25.4
V = App.Vector

# ---------------------------------------------------------------- parameters
P = dict(
    # Box measured by Doug (lid on): outer 95.5 wide x 87 front-to-back x 62 high; inner 81.5 x 70.0.
    BoxL=95.5,           # outer, along board Y (board long side)
    BoxW=87.0,           # outer, along board X (front-to-back)
    BoxH=62.0,           # outer, incl. lid
    WallSide=7.0,        # end walls (perpendicular to the board long axis) = (95.5 - 81.5)/2
    WallFB=8.5,          # front/back walls (the 95.5-wide faces) = (87 - 70)/2
    Floor=7.0,           # ASSUMED (not measured)
    LidT=7.0,            # ASSUMED lid top thickness (not measured)
    LidH=24.8,           # lid is a cap; seam ~40% down from the top (photo, estimated)
    Standoff=26.0,       # M3 x 26 standoffs, floor -> board bottom
    BoardT=1.6,
    BoardOrigL=82.69,    # board long side before the Edge.Cuts trim (KiCad); STEP is the trimmed board (0.85 mm off each end)
    LedTop=2.2,          # D2 placeholder emitter height (12-pad footprint, part number unknown): 1.2 base + 1.0 lens
    ConeD=48.0, ConeL=30.0, ConeHole=12.0, ConeWall=1.5,   # measured by Doug: 48 mm mouth OD, 30 mm long
    LedSinkW=20.0, LedSinkH=10.0, TapeT=0.25,   # 20x20x10 sink + 3M 8810 tape
    FanS=30.0, FanT=10.0, FanHoleC=24.0, FanBore=29.0,  # 3010 fan (Doug measured ~30 mm box hole)
    FanX=124.8 - 124.715, FanY=-(110.2 - 110.235),     # coaxial with LED heatsink centre
    FloorHoleD=30.0,                                   # intake hole through the floor
    GuardT=4.8, GuardWire=1.6, GuardHoleC=24.0, GuardRingOD=21.8, GuardRing2OD=11.0, GuardEyeID=3.2,  # Qualtek 08346
    # TO-220 sinks: Boyd/Aavid 577002B00000G (13.21 W x 6.35 D x 19.05 H, black), trimmed per regulator.
    # W along the tab, D away from the tab, H vertical (down from the board).
    ToSinkW=13.21, ToSinkFins=4, ToSinkBase=1.6,
    SinkW_U4=13.21, SinkD_U4=6.35, SinkH_U4=19.05,
    SinkW_U5=13.21, SinkD_U5=6.00, SinkH_U5=19.05,   # trimmed depth (tab faces the +Y wall)
    SinkW_U6=13.21, SinkD_U6=6.35, SinkH_U6=14.50,   # trimmed height (over the 3010 fan)
    SinkW_U7=13.21, SinkD_U7=6.00, SinkH_U7=19.05,   # trimmed depth (tab faces the +Y wall)
    SinkW_U8=13.21, SinkD_U8=6.35, SinkH_U8=14.50,   # trimmed height (over the 3010 fan)
    SinkW_U9=13.21, SinkD_U9=6.35, SinkH_U9=19.05,
    ToSinkRot=0.0,                              # extra rotation (deg) about the vertical axis through the tab-face centre
    ToSinkTopGap=1.5,                           # gap from board bottom to sink top (clears THT lead stubs)
    Stagger_U4=0.0, Stagger_U5=0.0, Stagger_U6=0.0, Stagger_U7=0.0, Stagger_U8=0.0, Stagger_U9=0.0,  # per-regulator extra drop (mm)
    # panel parts on the -Y end wall: (x, z) of each part's axis, world mm
    # -Y end wall layout from Doug's photo (scaled from the 79.4 mm wall width; estimated):
    # Connector face = the -X wall (a 95.5-wide FB wall). Positions are y along the face (+Y end = the end with the USB-C),
    # ESTIMATED from Doug's description (photos not readable by this build step): screw, USB-C, DC jack, 3.5 mm, screw.
    VentN=5, VentD=5.0, VentRingD=9.5, VentZ=-1.5,            # top row: 5 chrome-ringed vent openings, evenly spaced
    RowZ=-15.0,                                               # bottom row height
    ScrewLY=40.0, ScrewRY=-40.0,                              # small screws near the two ends
    JackY=0.0, JackZ=-15.0, JackHoleD=12.7, JackPanelT=6.0, JackCboreD=18.0,  # Adafruit 610 (max panel 8 mm -> counterbore)
    SwitchY=-25.0, SwitchZ=-14.0, SwitchHoleD=16.0,           # Adafruit 916 switch: NOT on the photo face; suggested on the +X wall
    # Amabro USB-C panel-mount breakout (Amazon B0H9S9C73Q). Listing: metal panel 20 x 6.6 mm (20.1 x 6.7 x 1.5),
    # PCB 11.9 mm wide, 2 mm screw holes. ESTIMATED: hole spacing, PCB depth/thickness, receptacle 8.94 x 3.26 x 7.35 (USB-C std).
    UsbY=18.0, UsbZ=-15.0, UsbRot=90.0,  # screws above/below the socket -> plate stood vertical
    UsbPlateL=20.0, UsbPlateH=6.6, UsbPlateT=1.5, UsbHoleC=16.0, UsbHoleD=2.0,
    UsbPcbW=11.9, UsbPcbD=10.0, UsbPcbT=1.6, UsbRecW=8.94, UsbRecH=3.26, UsbRecL=7.35,
    UsbSkinT=1.0, UsbCutW=9.4, UsbCutH=3.7, UsbPocketW=20.6, UsbPocketH=7.2,
    AudioY=-18.0, AudioZ=-15.0, AudioHoleD=6.35, AudioCboreD=12.0, AudioPanelT=1.5,   # Adafruit 3692 3.5 mm TRS
    # XIAO nRF52840 (U10) on 2x 1x7 female headers + the module's own male-header spacer
    XiaoX=144.272 - 124.715, XiaoY=-(134.62 - 110.235), XiaoRiserH=8.5, XiaoPinSpacerH=2.5,
    # AHT20 breakout on the existing 1x4 male header "AHT20" (plastic 2.54 mm)
    AhtHeaderX=145.552 - 124.715, AhtHeaderY=-(121.158 - 110.235), AhtSpacerH=2.54,
)
HOLES = [(-27.685, 37.845), (27.685, 37.845), (-27.685, -37.845), (27.685, -37.845)]

# LM317 TO-220 vertical (bottom side).  Values read from the KiCad STEP:
# (body xmin, xmax, ymin, ymax, tab direction) ; heatsink is clipped on the tab side.
LM317 = {   # real refs from the kicad_pcb
    "U6": (-10.89, -0.64, 24.17, 28.62, "-Y"),
    "U8": (4.61, 14.86, 24.17, 28.62, "-Y"),
    "U5": (-10.89, -0.64, 31.00, 35.46, "+Y"),
    "U7": (4.61, 14.86, 31.00, 35.46, "+Y"),
    "U9": (20.87, 25.33, 20.86, 31.11, "+X"),
    "U4": (-25.83, -21.38, 20.96, 31.21, "+X"),
}
SINK_TOP_Z = -1.5   # sink top sits 1.5 mm under the board to clear THT lead stubs

doc = App.newDocument("RGBWYV_Light")
ss = doc.addObject("Spreadsheet::Sheet", "Params")
for i, (k, v) in enumerate(P.items(), start=1):
    ss.set("A%d" % i, k); ss.set("B%d" % i, str(v)); ss.setAlias("B%d" % i, k)
doc.recompute()

def bind(obj, prop, expr):
    obj.setExpression(prop, expr)

FLOOR_TOP = -P["Standoff"]                 # inner floor surface
BOX_BOT = FLOOR_TOP - P["Floor"]

# ---------------------------------------------------------------- PCB (KiCad)
pcb = Part.read(PCB_STEP)
allb = App.BoundBox()
for _s in pcb.Solids: allb.add(_s.BoundBox)   # envelope of the as-exported PCB
sols = sorted(pcb.Solids, key=lambda s: -s.BoundBox.XLength * s.BoundBox.YLength)
board = sols[0]
comps = Part.makeCompound(sols[1:])
grp_pcb = doc.addObject("App::DocumentObjectGroup", "PCB")
o_board = doc.addObject("Part::Feature", "PCB_Board"); o_board.Shape = board
o_comp = doc.addObject("Part::Feature", "PCB_Components"); o_comp.Shape = comps
grp_pcb.addObjects([o_board, o_comp])

# ---------------------------------------------------------------- enclosure
grp_box = doc.addObject("App::DocumentObjectGroup", "Enclosure")
outer = doc.addObject("Part::Box", "BoxOuter")
bind(outer, "Length", "Params.BoxW"); bind(outer, "Width", "Params.BoxL")
outer.Height = P["BoxH"] - P["LidH"]; bind(outer, "Height", "Params.BoxH - Params.LidH")
bind(outer, ".Placement.Base.x", "-Params.BoxW/2"); bind(outer, ".Placement.Base.y", "-Params.BoxL/2")
bind(outer, ".Placement.Base.z", "-Params.Standoff - Params.Floor")
inner = doc.addObject("Part::Box", "BoxInner")
bind(inner, "Length", "Params.BoxW - 2*Params.WallFB"); bind(inner, "Width", "Params.BoxL - 2*Params.WallSide")
bind(inner, "Height", "Params.BoxH")
bind(inner, ".Placement.Base.x", "-Params.BoxW/2 + Params.WallFB")
bind(inner, ".Placement.Base.y", "-Params.BoxL/2 + Params.WallSide")
bind(inner, ".Placement.Base.z", "-Params.Standoff")
shell = doc.addObject("Part::Cut", "BoxShell"); shell.Base = outer; shell.Tool = inner

# cut-outs: fan screw holes (floor), exhaust slots (+X wall), jack/switch/USB/audio (-Y wall)
cutters = []
for sx in (-1, 1):       # fan / guard screw holes through the floor (M3 clearance)
    for sy in (-1, 1):
        cutters.append(Part.makeCylinder(1.7, P["Floor"] + 2,
                       V(P["FanX"] + sx * P["FanHoleC"]/2, P["FanY"] + sy * P["FanHoleC"]/2, BOX_BOT - 1)))
SEAM_Z = P["BoxH"] - P["LidH"] - P["Standoff"] - P["Floor"]
XN = -P["BoxW"]/2            # outer face of the -X connector wall
WF = P["WallFB"]
def xcyl(r, y, z, x0, L): return Part.makeCylinder(r, L, V(x0, y, z), V(1, 0, 0))
cutters.append(xcyl(P["JackHoleD"]/2, P["JackY"], P["JackZ"], XN - 1, WF + 2))
cutters.append(xcyl(P["JackCboreD"]/2, P["JackY"], P["JackZ"], XN + P["JackPanelT"], WF))          # inside counterbore
XO = P["BoxW"]/2            # outer face of the +X wall (suggested switch spot)
cutters.append(Part.makeCylinder(P["SwitchHoleD"]/2, WF + 2, V(XO + 1, P["SwitchY"], P["SwitchZ"]), V(-1, 0, 0)))
VENT_Y = [(-P["BoxL"]/2) + P["BoxL"] * (k + 1) / (P["VentN"] + 1) for k in range(int(P["VentN"]))]
for vy in VENT_Y:
    cutters.append(xcyl(P["VentD"]/2, vy, P["VentZ"], XN - 1, WF + 2))
for syp in (P["ScrewLY"], P["ScrewRY"]):
    cutters.append(xcyl(1.25, syp, P["RowZ"], XN - 1, WF + 2))     # small screws (pilot holes)
cutters.append(xcyl(P["AudioHoleD"]/2, P["AudioY"], P["AudioZ"], XN - 1, WF + 2))
cutters.append(xcyl(P["AudioCboreD"]/2, P["AudioY"], P["AudioZ"], XN + P["AudioPanelT"], WF))     # inside counterbore
# USB-C: plate stood vertical (UsbRot=90): cut-out/pocket dims swap W<->H
uw, uh = (P["UsbCutH"], P["UsbCutW"]) if abs(P["UsbRot"] - 90) < 1 else (P["UsbCutW"], P["UsbCutH"])
pw, ph = (P["UsbPocketH"], P["UsbPocketW"]) if abs(P["UsbRot"] - 90) < 1 else (P["UsbPocketW"], P["UsbPocketH"])
cutters.append(Part.makeBox(WF + 2, uw, uh, V(XN - 1, P["UsbY"] - uw/2, P["UsbZ"] - uh/2)))
cutters.append(Part.makeBox(WF, pw, ph, V(XN + P["UsbSkinT"], P["UsbY"] - pw/2, P["UsbZ"] - ph/2)))
for sk in (-1, 1):   # M2 screws through the 1 mm skin into the plate holes (above/below when vertical)
    if abs(P["UsbRot"] - 90) < 1:
        cutters.append(xcyl(P["UsbHoleD"]/2 + 0.1, P["UsbY"], P["UsbZ"] + sk * P["UsbHoleC"]/2, XN - 1, WF + 2))
    else:
        cutters.append(xcyl(P["UsbHoleD"]/2 + 0.1, P["UsbY"] + sk * P["UsbHoleC"]/2, P["UsbZ"], XN - 1, WF + 2))
for (hx, hy) in HOLES:   # countersunk screw holes in the floor
    cutters.append(Part.makeCylinder(1.7, P["Floor"] + 2, V(hx, hy, BOX_BOT - 1)))
o_cut = doc.addObject("Part::Feature", "WallCutouts"); o_cut.Shape = cutters[0].multiFuse(cutters[1:]).removeSplitter()  # fused: overlapping tools in a compound cut unreliably
box0 = doc.addObject("Part::Cut", "BoxWithCutouts"); box0.Base = shell; box0.Tool = o_cut
floor_hole = doc.addObject("Part::Cylinder", "FloorFanHole")
bind(floor_hole, "Radius", "Params.FloorHoleD/2"); bind(floor_hole, "Height", "Params.Floor + 2")
floor_hole.Placement.Base = V(P["FanX"], P["FanY"], BOX_BOT - 1)
bind(floor_hole, ".Placement.Base.x", "Params.FanX"); bind(floor_hole, ".Placement.Base.y", "Params.FanY")
bind(floor_hole, ".Placement.Base.z", "-Params.Standoff - Params.Floor - 1")
box = doc.addObject("Part::Cut", "WoodBox"); box.Base = box0; box.Tool = floor_hole

lid_o = doc.addObject("Part::Box", "LidOuter")
bind(lid_o, "Length", "Params.BoxW"); bind(lid_o, "Width", "Params.BoxL"); bind(lid_o, "Height", "Params.LidH")
bind(lid_o, ".Placement.Base.x", "-Params.BoxW/2"); bind(lid_o, ".Placement.Base.y", "-Params.BoxL/2")
bind(lid_o, ".Placement.Base.z", "Params.BoxH - Params.LidH - Params.Standoff - Params.Floor")
lid_i = doc.addObject("Part::Box", "LidInner")
bind(lid_i, "Length", "Params.BoxW - 2*Params.WallFB"); bind(lid_i, "Width", "Params.BoxL - 2*Params.WallSide")
bind(lid_i, "Height", "Params.LidH - Params.LidT")
bind(lid_i, ".Placement.Base.x", "-Params.BoxW/2 + Params.WallFB"); bind(lid_i, ".Placement.Base.y", "-Params.BoxL/2 + Params.WallSide")
bind(lid_i, ".Placement.Base.z", "Params.BoxH - Params.LidH - Params.Standoff - Params.Floor - 0.01")
lid = doc.addObject("Part::Cut", "LidCap"); lid.Base = lid_o; lid.Tool = lid_i
lid_hole = doc.addObject("Part::Cylinder", "LidConeHole")
bind(lid_hole, "Radius", "Params.ConeD/2 + 0.5"); lid_hole.Height = 100
lid_hole.Placement.Base = V(0, 0, 0)
woodlid = doc.addObject("Part::Cut", "WoodLid"); woodlid.Base = lid; woodlid.Tool = lid_hole
grp_box.addObjects([outer, inner, shell, o_cut, box0, floor_hole, box, lid_o, lid_i, lid, lid_hole, woodlid])

# ---------------------------------------------------------------- standoffs + screws
grp_hw = doc.addObject("App::DocumentObjectGroup", "Hardware")
for i, (hx, hy) in enumerate(HOLES, start=1):
    so = doc.addObject("Part::Prism", "Standoff_M3x26_%d" % i)
    so.Polygon = 6; so.Circumradius = 5.5 / math.sqrt(3)
    bind(so, "Height", "Params.Standoff")
    so.Placement.Base = V(hx, hy, FLOOR_TOP)
    bind(so, ".Placement.Base.z", "-Params.Standoff")
    hd = doc.addObject("Part::Cylinder", "Screw_M3_button_%d" % i)
    hd.Radius = 2.85; hd.Height = 1.65; hd.Placement.Base = V(hx, hy, P["BoardT"])
    cs = doc.addObject("Part::Cone", "Screw_M3_csk_%d" % i)
    cs.Radius1 = 3.0; cs.Radius2 = 1.5; cs.Height = 1.7; cs.Placement.Base = V(hx, hy, BOX_BOT)
    grp_hw.addObjects([so, hd, cs])

# ---------------------------------------------------------------- reflector cone
cone_z0 = P["BoardT"] + P["LedTop"]
co = doc.addObject("Part::Cone", "ReflectorOuter")
bind(co, "Radius1", "Params.ConeHole/2 + Params.ConeWall"); bind(co, "Radius2", "Params.ConeD/2")
bind(co, "Height", "Params.ConeL")
ci = doc.addObject("Part::Cone", "ReflectorInner")
bind(ci, "Radius1", "Params.ConeHole/2"); bind(ci, "Radius2", "Params.ConeD/2 - Params.ConeWall")
bind(ci, "Height", "Params.ConeL + 0.02")
LEDX, LEDY = 124.8 - 124.715, -(110.2 - 110.235)
co.Placement.Base = V(LEDX, LEDY, cone_z0); ci.Placement.Base = V(LEDX, LEDY, cone_z0 - 0.01)
bind(co, ".Placement.Base.z", "Params.BoardT + Params.LedTop")
bind(ci, ".Placement.Base.z", "Params.BoardT + Params.LedTop - 0.01")
cone = doc.addObject("Part::Cut", "ReflectorCone"); cone.Base = co; cone.Tool = ci
grp_hw.addObjects([co, ci, cone])

# D2: 12-pad multi-chip emitter. No part number in the BOM/schematic -> UNCONFIRMED placeholder dimensioned from the
# footprint (pads +/-6.5 x +/-3.75 mm, 7 mm round thermal pad): 12.0 x 9.0 x 1.2 ceramic body + 7 mm x 1.0 mm lens.
led_body = Part.makeBox(9.0, 12.0, 1.2, V(-4.5, -6.0, 0)).fuse(Part.makeCylinder(3.5, P["LedTop"] - 1.2, V(0, 0, 1.2)))
led = doc.addObject("Part::Feature", "LED_D2_placeholder")
led.Shape = led_body; led.Placement.Base = V(LEDX, LEDY, P["BoardT"])
# J1: Xinya XY308-2.54 2P terminal block (no KiCad model) - approximate 5.08 x 6.5 x 8.5 body
j1 = doc.addObject("Part::Feature", "J1_TerminalBlock_approx")
j1.Shape = Part.makeBox(5.08, 6.5, 8.5, V(-1.27, -3.25, 0))
j1.Placement.Base = V(96.266 - 124.715, -(105.664 - 110.235), P["BoardT"])
grp_hw.addObjects([led, j1])

# ---------------------------------------------------------------- heatsinks
grp_th = doc.addObject("App::DocumentObjectGroup", "Thermal")

def finned(w, d, h, nfin, base, fin_t=1.0, along="x"):
    """Finned sink: base plate (thickness 'base') on the z=h top face, fins hang down.
    Footprint w (x) by d (y), height h, returned with z from 0..h."""
    s = Part.makeBox(w, d, base, V(0, 0, h - base))
    pitch = (w - fin_t) / (nfin - 1)
    for k in range(nfin):
        s = s.fuse(Part.makeBox(fin_t, d, h - base, V(k * pitch, 0, 0)))
    return s.removeSplitter()

# LED pad sink: 20x20x10 on 3M 8810 tape under the exposed pad (board bottom)
tape = doc.addObject("Part::Box", "Tape_3M8810")
tape.Length = 25.0; tape.Width = 25.0; bind(tape, "Height", "Params.TapeT")
tape.Placement.Base = V(LEDX - 12.5, LEDY - 12.5, -P["TapeT"])
ledsink = doc.addObject("Part::Feature", "Heatsink_LED_20x20x10")
ledsink.Shape = finned(P["LedSinkW"], P["LedSinkW"], P["LedSinkH"], 7, 2.0)
ledsink.Placement.Base = V(LEDX - 10, LEDY - 10, -P["TapeT"] - P["LedSinkH"])
grp_th.addObjects([tape, ledsink])

def to220_sink(name, xmin, xmax, ymin, ymax, tab):
    """Finned clip-on sink on the tab side. Local frame: tab-face centre at origin, base plate y 0..Base,
    fins towards +y, z 0..H.  Size/fins from Params (re-run the script); stagger & rotation are expressions."""
    W, D, H, nf, tb = P["SinkW_" + name], P["SinkD_" + name], P["SinkH_" + name], int(P["ToSinkFins"]), P["ToSinkBase"]
    sh = Part.makeBox(W, tb, H, V(-W/2, 0, 0))
    for k in range(nf):
        sh = sh.fuse(Part.makeBox(1.2, D, H, V(-W/2 + k * (W - 1.2) / max(nf - 1, 1), 0, 0)))
    sh = sh.removeSplitter()
    base_rot = {"+Y": 0, "-Y": 180, "+X": -90, "-X": 90}[tab]
    if tab in ("-Y", "+Y"):
        org = V((xmin + xmax) / 2, ymax if tab == "+Y" else ymin, 0)
    else:
        org = V(xmax if tab == "+X" else xmin, (ymin + ymax) / 2, 0)
    o = doc.addObject("Part::Feature", "Heatsink_TO220_" + name)
    o.Shape = sh
    o.Placement = App.Placement(V(org.x, org.y, -P["ToSinkTopGap"] - H - P["Stagger_" + name]),
                                App.Rotation(V(0, 0, 1), base_rot + P["ToSinkRot"]))
    bind(o, ".Placement.Base.z", "-Params.ToSinkTopGap - Params.SinkH_%s - Params.Stagger_%s" % (name, name))
    return o

to_sinks = [to220_sink(n, *v) for n, v in LM317.items()]
grp_th.addObjects(to_sinks)

# 3010 fan lying flat on the floor, centred under the LED heatsink, blowing up.
# Built about its own centre (local z 0..FanT), then placed by expressions from Params.
S, T, HC = P["FanS"], P["FanT"], P["FanHoleC"]
frame = Part.makeBox(S, S, T, V(-S/2, -S/2, 0)).cut(Part.makeCylinder(P["FanBore"]/2, T + 2, V(0, 0, -1)))
for sx in (-1, 1):
    for sy in (-1, 1):
        frame = frame.cut(Part.makeCylinder(1.6, T + 2, V(sx * HC/2, sy * HC/2, -1)))
blades = Part.makeCylinder(6.0, T - 1.0, V(0, 0, 0.5))            # hub
for k in range(7):
    b = Part.makeBox(P["FanBore"]/2 - 6.5, 1.0, T - 3.0, V(5.5, -0.5, 1.5))
    b.rotate(V(0, 0, 0), V(1, 0, 0), 25)                            # blade pitch
    b.rotate(V(0, 0, 0), V(0, 0, 1), k * 360.0 / 7)
    blades = blades.fuse(b)
fan = doc.addObject("Part::Feature", "Fan_3010")
fan.Shape = Part.makeCompound([frame, blades.common(Part.makeCylinder(P["FanBore"]/2 - 0.3, T))])
fan.Placement.Base = V(P["FanX"], P["FanY"], FLOOR_TOP)
bind(fan, ".Placement.Base.x", "Params.FanX"); bind(fan, ".Placement.Base.y", "Params.FanY")
bind(fan, ".Placement.Base.z", "-Params.Standoff")
grp_th.addObject(fan)

# Fan guard on the underside of the floor: Qualtek 08346 (30 mm wire-form finger guard,
# 24 mm hole centres, 21.8 mm outer ring, 1.6 mm wire, 4.8 mm thick). Simplified wire model.
w, GT, GC = P["GuardWire"], P["GuardT"], P["GuardHoleC"]
zr = -(GT - w/2)                       # ring plane (furthest from the floor)
parts = []
for d in (P["GuardRingOD"], P["GuardRing2OD"]):
    parts.append(Part.makeTorus(d/2 - w/2, w/2, V(0, 0, zr)))
parts.append(Part.makeCylinder(2.0, w, V(0, 0, zr - w/2)))           # centre boss
for sx in (-1, 1):
    for sy in (-1, 1):
        eye = V(sx * GC/2, sy * GC/2, -w/2)
        parts.append(Part.makeTorus(P["GuardEyeID"]/2 + w/2, w/2, eye))   # mounting eye
        a = V(sx * GC/2, sy * GC/2, -w/2); b = V(0, 0, zr)
        d = b - a; L = d.Length
        parts.append(Part.makeCylinder(w/2, L, a, d))                 # diagonal rib
guard = doc.addObject("Part::Feature", "FanGuard_Qualtek_08346")
guard.Shape = Part.makeCompound(parts)
guard.Placement.Base = V(P["FanX"], P["FanY"], BOX_BOT)
bind(guard, ".Placement.Base.x", "Params.FanX"); bind(guard, ".Placement.Base.y", "Params.FanY")
bind(guard, ".Placement.Base.z", "-Params.Standoff - Params.Floor")
grp_th.addObject(guard)

# ---------------------------------------------------------------- panel parts
PARTS = os.path.join(HERE, "parts")
def load_part(fname, name, y, z, x_front, outward_is_plus_z=True, nut_shift=None):
    """Load a vendor STEP whose axis is model Z, for the -X connector wall. If outward_is_plus_z, model +Z points
    out of the box (-X world) and model z=0 lands on x_front; otherwise model +Z points into the box."""
    sh = Part.read(os.path.join(PARTS, fname))
    sols = list(sh.Solids)
    if nut_shift:   # move the panel nut/washer to where it sits on our thicker wall
        test, dz = nut_shift
        for i, so in enumerate(sols):
            if test(so.BoundBox):
                so2 = so.copy(); so2.translate(V(0, 0, dz)); sols[i] = so2
    sh = Part.makeCompound(sols)
    rot = App.Rotation(V(0, 1, 0), -90 if outward_is_plus_z else 90)
    o = doc.addObject("Part::Feature", name)
    o.Shape = sh
    o.Placement = App.Placement(V(x_front, y, z), rot)
    return o

jack = load_part("Adafruit_610_DC_Jack_2.1mm_panel.step", "DC_Jack_Adafruit610", P["JackY"], P["JackZ"], XN,
                 nut_shift=(lambda b: b.XLength > 15 and b.ZMax < -1.0, -(P["JackPanelT"] - 1.55)))
sw = load_part("Adafruit_916_16mm_metal_on-off_switch.step", "Switch_Adafruit916", 0, P["SwitchZ"], 0,
               nut_shift=(lambda b: b.XLength > 21 and b.ZMax < -1.0, -(P["WallFB"] - 1.68)))
sw.Placement = App.Placement(V(XO, P["SwitchY"], P["SwitchZ"]), App.Rotation(V(0, 1, 0), 90))   # model +Z -> +X (out)
def amabro_usbc():
    """Amabro USB-C panel breakout, local frame: receptacle front at y=0, axis +y into the box, centre x=z=0."""
    def rrect(w, h, L, r):
        b = Part.makeBox(w - 2*r, L, h, V(-w/2 + r, 0, -h/2)).fuse(Part.makeBox(w, L, h - 2*r, V(-w/2, 0, -h/2 + r)))
        for sx in (-1, 1):
            for sz in (-1, 1):
                b = b.fuse(Part.makeCylinder(r, L, V(sx*(w/2 - r), 0, sz*(h/2 - r)), V(0, 1, 0)))
        return b.removeSplitter()
    rec = rrect(P["UsbRecW"], P["UsbRecH"], P["UsbRecL"], P["UsbRecH"]/2 - 0.01)
    rec = rec.cut(rrect(P["UsbRecW"] - 0.8, P["UsbRecH"] - 0.8, 6.0, P["UsbRecH"]/2 - 0.41).translated(V(0, -0.01, 0)))
    plate = Part.makeBox(P["UsbPlateL"], P["UsbPlateT"], P["UsbPlateH"], V(-P["UsbPlateL"]/2, P["UsbSkinT"], -P["UsbPlateH"]/2))
    plate = plate.cut(rrect(P["UsbRecW"] + 0.2, P["UsbRecH"] + 0.2, 10, P["UsbRecH"]/2).translated(V(0, -1, 0)))
    for sx in (-1, 1):
        plate = plate.cut(Part.makeCylinder(P["UsbHoleD"]/2, 5, V(sx*P["UsbHoleC"]/2, -1, 0), V(0, 1, 0)))
    pcb_ = Part.makeBox(P["UsbPcbW"], P["UsbPcbD"], P["UsbPcbT"],
                        V(-P["UsbPcbW"]/2, P["UsbSkinT"] + P["UsbPlateT"], -P["UsbRecH"]/2 - P["UsbPcbT"]))
    return Part.makeCompound([rec, plate, pcb_])
usb = doc.addObject("Part::Feature", "USB_C_Amabro_B0H9S9C73Q")
usb.Shape = amabro_usbc()
# local +y (into box) -> world +X ; then spin about the socket axis by UsbRot
usb.Placement = App.Placement(V(XN, P["UsbY"], P["UsbZ"]),
                              App.Rotation(V(0, 0, 1), -90).multiply(App.Rotation(V(0, 1, 0), P["UsbRot"])))
audio = load_part("Adafruit_3692_TRS_3.5mm_panel_jack.step", "Audio_Adafruit3692", P["AudioY"], P["AudioZ"],
                  XN - 3.1, outward_is_plus_z=False)   # nut back face (model z=3.1) on the outer face
for o, ky, kz in ((jack, "JackY", "JackZ"), (usb, "UsbY", "UsbZ"), (audio, "AudioY", "AudioZ")):
    bind(o, ".Placement.Base.y", "Params." + ky); bind(o, ".Placement.Base.z", "Params." + kz)
# chrome vent eyelets and the two edge screws on the -X connector wall
rings = []
for vy in VENT_Y:
    r = xcyl(P["VentRingD"]/2, vy, P["VentZ"], XN - 1.0, 1.0).cut(xcyl(P["VentD"]/2, vy, P["VentZ"], XN - 2.0, 3.0))
    r = r.fuse(xcyl(P["VentD"]/2, vy, P["VentZ"], XN, WF).cut(xcyl(P["VentD"]/2 - 0.4, vy, P["VentZ"], XN - 1, WF + 2)))
    rings.append(r)
o_vents = doc.addObject("Part::Feature", "Vent_Eyelets_x5"); o_vents.Shape = Part.makeCompound(rings)
scr = []
for syp in (P["ScrewLY"], P["ScrewRY"]):
    scr.append(xcyl(2.5, syp, P["RowZ"], XN - 1.5, 1.5).fuse(xcyl(1.25, syp, P["RowZ"], XN, 10)))
o_scr = doc.addObject("Part::Feature", "FaceScrews_x2"); o_scr.Shape = Part.makeCompound(scr)
panel_parts = [jack, usb, audio]
grp_hw.addObjects(panel_parts + [sw, o_vents, o_scr])

# ---------------------------------------------------------------- XIAO nRF52840 (U10) on risers
grp_mod = doc.addObject("App::DocumentObjectGroup", "Modules")
BT = P["BoardT"]
xiao_bot = BT + P["XiaoRiserH"] + P["XiaoPinSpacerH"]
risers = []
for k, dy in enumerate((-7.62, 7.62)):          # pad rows 15.24 mm apart (pcb y 127.0 / 142.24)
    fh = Part.makeBox(17.78, 2.54, P["XiaoRiserH"], V(-8.89, -1.27, 0))
    for i in range(7):
        fh = fh.cut(Part.makeBox(1.0, 1.0, P["XiaoRiserH"] + 1, V(-7.62 + i * 2.54 - 0.5, -0.5, 0.5)))
    o = doc.addObject("Part::Feature", "XIAO_Riser_FemaleHdr_1x7_%d" % (k + 1)); o.Shape = fh
    o.Placement.Base = V(P["XiaoX"], P["XiaoY"] + dy, BT)
    sp = Part.makeBox(17.78, 2.54, P["XiaoPinSpacerH"], V(-8.89, -1.27, 0))
    for i in range(7):
        sp = sp.fuse(Part.makeBox(0.64, 0.64, P["XiaoPinSpacerH"] + 6.0, V(-7.62 + i * 2.54 - 0.32, -0.32, -5.5)))
    o2 = doc.addObject("Part::Feature", "XIAO_MaleHdr_1x7_%d" % (k + 1)); o2.Shape = sp
    o2.Placement.Base = V(P["XiaoX"], P["XiaoY"] + dy, BT + P["XiaoRiserH"])
    risers += [o, o2]
xs = Part.read(os.path.join(PARTS, "Seeed_XIAO_nRF52840_v15.step"))
# Seeed model: board in its X-Z plane, +Y up, PCB x -8.67..12.28, z -15.0..2.78, bottom y=-0.25, USB-C at +X.
xoff = App.Placement(V(-(-8.67 + 12.28) / 2, 0.25, -(-15.0 + 2.78) / 2), App.Rotation())
xiao = doc.addObject("Part::Feature", "XIAO_nRF52840_U10")
xiao.Shape = xs
# Rx(90): model +Y -> world +Z; Rz(180): USB-C towards -X (pins 1/14 end of the footprint)
xiao.Placement = App.Placement(V(P["XiaoX"], P["XiaoY"], xiao_bot),
                               App.Rotation(V(0, 0, 1), 180).multiply(App.Rotation(V(1, 0, 0), 90))).multiply(xoff)
grp_mod.addObjects(risers + [xiao])

# ---------------------------------------------------------------- AHT20 breakout on the "AHT20" 1x4 header
ah = Part.read(os.path.join(PARTS, "Adafruit_4566_AHT20_breakout.step"))
# Adafruit model: PCB 0..25.4 x 0..17.78, header holes at x 8.89..16.51, y 2.54. Board extends to +Y (away from the XIAO).
aht = doc.addObject("Part::Feature", "AHT20_Adafruit4566")
aht.Shape = ah
aht.Placement = App.Placement(V(P["AhtHeaderX"] + 3 * 2.54 / 2 - 12.7, P["AhtHeaderY"] - 2.54, BT + P["AhtSpacerH"]), App.Rotation())
grp_mod.addObject(aht)

doc.recompute()

# ---------------------------------------------------------------- fit report
def bb(o): return o.Shape.BoundBox
iw2 = P["BoxW"]/2 - P["WallFB"]; il2 = P["BoxL"]/2 - P["WallSide"]
report = []
report.append("Box inner: %.2f (X, front-back) x %.2f (Y, end-to-end) x %.2f (Z) mm  [walls: FB %.2f, side %.2f, floor %.1f (assumed), lid %.1f (assumed)]" % (
    2*iw2, 2*il2, P["BoxH"] - P["Floor"] - P["LidT"], P["WallFB"], P["WallSide"], P["Floor"], P["LidT"]))
b = board.BoundBox
report.append("*** BOARD LENGTH vs MEASURED INTERIOR: original board %.2f mm vs inner %.2f mm -> %s by %.2f mm (%.2f per end) ***" % (
    P["BoardOrigL"], 2*il2, "DOES NOT FIT" if P["BoardOrigL"] > 2*il2 else "fits", abs(P["BoardOrigL"] - 2*il2), abs(P["BoardOrigL"] - 2*il2)/2))
report.append("    (possible explanations: inner measured at a lip/rim, board edges meant to sit in a groove, or tape tolerance)")
report.append("Board as modelled (Edge.Cuts trimmed 0.85 mm per end) %.2f x %.2f: X clearance %.2f/side, Y clearance %.2f/side"
              % (b.XLength, b.YLength, iw2 - b.XMax, il2 - b.YMax))
report.append("Component envelope X %.2f..%.2f -> min wall gap %.2f" % (allb.XMin, allb.XMax, iw2 - max(-allb.XMin, allb.XMax)))
report.append("Lowest PCB part z=%.2f -> %.2f mm above floor" % (allb.ZMin, allb.ZMin - FLOOR_TOP))
report.append("Highest PCB part z=%.2f -> %.2f mm below lid underside" % (allb.ZMax, (P["BoxH"] - P["Floor"] - P["LidT"] - P["Standoff"]) - allb.ZMax))
cb = bb(cone)
lid_top = P["BoxH"] - P["Floor"] - P["Standoff"]
report.append("Cone top z=%.2f vs lid top z=%.2f -> sticks out %.2f mm" % (cb.ZMax, lid_top, cb.ZMax - lid_top))
inner_solid = Part.makeBox(2*iw2, 2*il2, P["BoxH"], V(-iw2, -il2, FLOOR_TOP))
movers = to_sinks + [ledsink, fan]
static = [o_comp, o_board] + [o for o in doc.Objects if o.Name.startswith("Standoff_")] + panel_parts + risers + [xiao, aht]
for o in movers:
    s = o.Shape
    sb = s.BoundBox
    out = s.cut(inner_solid).Volume
    hits = []
    for other in movers + static:
        if other is o: continue
        v = s.common(other.Shape).Volume
        if v > 0.5: hits.append("%s(%.0f mm3)" % (other.Name, v))
    report.append("%-28s z %.1f..%.1f  floor gap %.2f  outside-box %.0f mm3  %s" % (
        o.Name, sb.ZMin, sb.ZMax, sb.ZMin - FLOOR_TOP, out, ("INTERFERES " + ", ".join(hits)) if hits else ""))
    if out > 0.01:
        if sb.XMax > iw2: report.append("    -> into +X wall by %.2f mm" % (sb.XMax - iw2))
        if sb.XMin < -iw2: report.append("    -> into -X wall by %.2f mm" % (-iw2 - sb.XMin))
        if sb.YMax > il2: report.append("    -> into +Y wall by %.2f mm" % (sb.YMax - il2))
        if sb.YMin < -il2: report.append("    -> into -Y wall by %.2f mm" % (-il2 - sb.YMin))
fb, lb = fan.Shape.BoundBox, ledsink.Shape.BoundBox
report.append("Fan %gx%gx%g centre (%.3f, %.3f); LED sink centre (%.3f, %.3f) -> XY offset (%.3f, %.3f)" % (
    P["FanS"], P["FanS"], P["FanT"], fb.Center.x, fb.Center.y, lb.Center.x, lb.Center.y,
    fb.Center.x - lb.Center.x, fb.Center.y - lb.Center.y))
report.append("Fan z %.2f..%.2f: gap to LED sink bottom %.2f mm, to board bottom %.2f mm" % (
    fb.ZMin, fb.ZMax, lb.ZMin - fb.ZMax, 0.0 - fb.ZMax))
for o in to_sinks + [o for o in doc.Objects if o.Name.startswith("Standoff_")]:
    d = fan.Shape.distToShape(o.Shape)[0]
    report.append("  fan to %-24s %s" % (o.Name, ("%.2f mm" % d) if d > 1e-6 else "CLASH (touching/overlapping)"))
gb = guard.Shape.BoundBox
report.append("Guard (Qualtek 08346) z %.2f..%.2f -> hangs %.2f mm below the box bottom (z %.2f); needs feet >= that" % (
    gb.ZMin, gb.ZMax, BOX_BOT - gb.ZMin, BOX_BOT))
report.append("Floor hole %.1f mm dia under fan bore %.1f mm" % (P["FloorHoleD"], P["FanBore"]))
report.append("Cone: %.1f mm long, %.1f mm mouth OD, %.1f mm LED hole; lid hole %.1f mm" % (
    P["ConeL"], P["ConeD"], P["ConeHole"], P["ConeD"] + 1.0))
LID_UNDER = P["BoxH"] - P["Floor"] - P["LidT"] - P["Standoff"]
def gap(a, b):
    try:
        d = a.Shape.distToShape(b.Shape)[0]
    except Exception:
        return "?"
    if d > 1e-6: return "%.2f" % d
    v = a.Shape.common(b.Shape).Volume
    return "CLASH %.1f mm3" % v if v > 0.5 else "touch"
others = [o_comp, o_board, fan, ledsink, cone, xiao, aht, sw, led, j1] + to_sinks + panel_parts + risers + \
         [o for o in doc.Objects if o.Name.startswith("Standoff_")]
report.append("TO-220 sinks (Boyd 577002B00000G, trimmed), final sizes and clearances:")
for o in to_sinks:
    n = o.Name.replace("Heatsink_TO220_", "")
    b = o.Shape.BoundBox
    cand = [x for x in others if x is not o and x is not o_comp] + [o_comp]
    near = sorted(((o.Shape.distToShape(x.Shape)[0], x.Name) for x in cand))[:3]
    walls = min(iw2 - b.XMax, b.XMin + iw2, il2 - b.YMax, b.YMin + il2)
    report.append("  %-4s %.2f W x %.2f D x %.2f H  z %.2f..%.2f  floor %.2f  nearest wall %.2f  nearest: %s" % (
        n, P["SinkW_" + n], P["SinkD_" + n], P["SinkH_" + n], b.ZMin, b.ZMax, b.ZMin - FLOOR_TOP, walls,
        ", ".join("%s %.2f" % (nm, d) for d, nm in near)))
report.append("Panel parts on the -X connector wall (outer face x=%.2f, %.1f thick):" % (XN, WF))
for o in panel_parts:
    b = o.Shape.BoundBox
    near = sorted(((o.Shape.distToShape(x.Shape)[0], x.Name) for x in others if x is not o))[:3]
    wallv = o.Shape.common(box.Shape).Volume
    report.append("  %-22s axis y=%.1f z=%.1f  reaches x=%.1f inside (%.1f past the inner face)  nearest: %s  wall-overlap %.0f mm3" % (
        o.Name, {jack: P["JackY"], usb: P["UsbY"], audio: P["AudioY"]}[o], {jack: P["JackZ"], usb: P["UsbZ"], audio: P["AudioZ"]}[o],
        b.XMax, b.XMax - (XN + WF),
        ", ".join("%s %.2f" % (n, d) for d, n in near), wallv))
swb = sw.Shape.BoundBox
report.append("Switch (Adafruit 916) NOT on the photo face; suggested +X wall at y=%.1f z=%.1f, reaches x=%.1f; nearest: %s" % (
    P["SwitchY"], P["SwitchZ"], swb.XMin, ", ".join("%s %.2f" % (n, d) for d, n in sorted(
        ((sw.Shape.distToShape(x.Shape)[0], x.Name) for x in others if x is not sw))[:3])))
report.append("Vents: 5 x %.1f mm at z=%.1f, y=%s; seam z=%.2f; board top z=%.2f, board edge %.2f mm from the -X inner face" % (
    P["VentD"], P["VentZ"], ", ".join("%.1f" % v for v in VENT_Y), SEAM_Z, P["BoardT"], board.BoundBox.XMin - (XN + WF)))
lb2 = led.Shape.BoundBox
report.append("D2 LED placeholder (unconfirmed part): 9.0 x 12.0 x %.1f at (%.3f, %.3f), z %.2f..%.2f; cone %s" % (
    P["LedTop"], LEDX, LEDY, lb2.ZMin, lb2.ZMax, gap(led, cone)))
xb = xiao.Shape.BoundBox
report.append("XIAO U10: centre (%.2f, %.2f), USB-C to -X, PCB bottom z=%.2f (%.2f above board top), top z=%.2f (%.2f above board top), lid gap %.2f" % (
    P["XiaoX"], P["XiaoY"], xiao_bot, xiao_bot - BT, xb.ZMax, xb.ZMax - BT, LID_UNDER - xb.ZMax))
report.append("  XIAO extents x %.2f..%.2f y %.2f..%.2f; gaps: cone %s, PCB comps %s, AHT20 %s, lid %.2f" % (
    xb.XMin, xb.XMax, xb.YMin, xb.YMax, gap(xiao, cone), gap(xiao, o_comp), gap(xiao, aht), LID_UNDER - xb.ZMax))
ab = aht.Shape.BoundBox
report.append("AHT20 (Adafruit 4566): x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f; board edge x=%.2f (overhang %.2f), +X inner wall x=%.2f (%s)" % (
    ab.XMin, ab.XMax, ab.YMin, ab.YMax, ab.ZMin, ab.ZMax, board.BoundBox.XMax, ab.XMax - board.BoundBox.XMax, iw2,
    ("INTO WALL by %.2f mm" % (ab.XMax - iw2)) if ab.XMax > iw2 else "clear %.2f" % (iw2 - ab.XMax)))
report.append("  AHT20 gaps: XIAO risers %s, XIAO %s, cone %s, PCB comps %s" % (
    min(gap(aht, r) for r in risers[::2]), gap(aht, xiao), gap(aht, cone), gap(aht, o_comp)))
txt = doc.addObject("App::TextDocument", "FitReport"); txt.Text = "\n".join(report)
print("\n".join(report))

# ---------------------------------------------------------------- colours (GUI only)
if App.GuiUp:
    import FreeCADGui as Gui
    col = {
        "PCB_Board": (0.05, 0.40, 0.15), "PCB_Components": (0.15, 0.15, 0.17),
        "WoodBox": (0.72, 0.52, 0.30), "WoodLid": (0.78, 0.58, 0.36),
        "ReflectorCone": (0.85, 0.85, 0.88), "Heatsink_LED_20x20x10": (0.75, 0.75, 0.78),
        "Tape_3M8810": (0.95, 0.85, 0.30), "Fan_3010": (0.10, 0.10, 0.10), "FanGuard_Qualtek_08346": (0.85, 0.85, 0.88),
        "XIAO_nRF52840_U10": (0.15, 0.15, 0.6), "AHT20_Adafruit4566": (0.1, 0.1, 0.1),
    }
    for o in doc.Objects:
        vo = o.ViewObject
        if vo is None: continue
        if o.Name.startswith("Heatsink_TO220"): vo.ShapeColor = (0.80, 0.80, 0.83)
        elif o.Name.startswith("Standoff"): vo.ShapeColor = (0.85, 0.75, 0.40)
        elif o.Name.startswith("Screw"): vo.ShapeColor = (0.6, 0.6, 0.6)
        elif o.Name in col: vo.ShapeColor = col[o.Name]
    for n in ("WoodBox", "WoodLid"):
        doc.getObject(n).ViewObject.Transparency = 60

# ---------------------------------------------------------------- save + export
doc.saveAs(OUT_FCSTD)
visible = [o_board, o_comp, box, woodlid, cone, tape, ledsink, fan, guard, xiao, aht, sw, o_vents, o_scr, led, j1] + panel_parts + risers + to_sinks + \
          [o for o in doc.Objects if o.Name.startswith(("Standoff_", "Screw_M3_"))]
import Import
Import.export(visible, OUT_STEP)
print("saved", OUT_FCSTD, OUT_STEP)
