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
    LidH=22.0,           # lid is a 22 mm deep cap (Doug: top surface to bottom edge)
    Standoff=23.4,       # measured by Doug: PCB top to inside floor 25.0 mm, minus the 1.6 mm board
    BoardT=1.6,
    BoardOrigL=82.69,    # board long side before the Edge.Cuts trim (KiCad); STEP is the trimmed board (0.85 mm off each end)
    LedTop=2.2,          # D2 placeholder emitter height (12-pad footprint, part number unknown): 1.2 base + 1.0 lens
    ConeD=48.0, ConeL=30.0, ConeHole=12.0, ConeWall=1.5,   # 48 mm mouth OD (Doug); ConeL is recomputed below from ConeTopGap
    ConeTopGap=0.0,      # cone top this far below the lid top surface; 0 = flush (Doug)
    # LED sink: uxcell 30x20x10 (Amazon B093V778LH, a21012600ux0719), blue anodised, 9 straight fins, pre-applied thermal pad
    LedSinkL=30.0, LedSinkW=20.0, LedSinkH=10.0, LedSinkFins=9, LedSinkFinT=1.0, LedSinkBase=2.0, LedSinkRot=0.0,  # Rot 0: channels along X (to the -X vent wall)
    TapeT=0.25,                                  # its pre-applied thermal adhesive pad
    FanS=30.0, FanT=10.0, FanHoleC=24.0, FanBore=29.0,  # 3010 fan (Doug measured ~30 mm box hole)
    FanX=124.8 - 124.715, FanY=-(110.2 - 110.235),     # coaxial with LED heatsink centre
    FloorHoleD=30.0,                                   # intake hole through the floor
    # Custom 3D-printed low-profile fan grill on the outside of the floor (replaces the Qualtek 08346 wire guard)
    GrillS=36.0, GrillR=3.0, GrillT=2.0,             # square plate, corner radius, thickness
    GrillHexAF=3.0, GrillRib=1.0, GrillOpenD=30.0, GrillRingW=2.0,   # honeycomb over the 30 mm opening, 2 mm solid ring
    GrillLocOD=29.6, GrillLocH=1.0, GrillLocW=1.2,   # locating ring that drops into the floor hole
    GrillHoleD=3.4, GrillCskD=6.9,                   # M3 flat head (ISO 10642 head 6.72) 90 deg countersink, on the 24 mm fan pattern
    GrillScrewL=22.0, GrillNutT=1.8,                 # M3 x 22 flat head: grill 2 + floor 7 + fan 10 = 19, + M3 thin nut (DIN 439, 1.8) on the fan top
    # TO-220 sinks: Adam Tech HSK-059-04 (Digi-Key 2057-HSK-059-04-ND), extruded, M3 tapped hole at mid-length (17.5 of 35).
    # Profile (datasheet dwg A): 10.00 wide x 5.50 deep (2.4 base + 3.1 fins), 4 fins + a centre screw channel; L = 35 along the tab.
    # W along the tab, D away from the tab, H = length, vertical (down from the board).
    ToSinkW=10.0, ToSinkFins=4, ToSinkBase=2.4, ToSinkFinT=1.2, ToSinkSlot=2.6, ToSinkHoleZ=-16.09,  # TO-220 tab hole centre (from the KiCad model)
    SinkW_U4=10.0, SinkD_U4=5.50, SinkH_U4=20.0,     # all six: 35 mm stock cut to 20.0 (2.9 off the top end, 12.1 off the bottom end)
    SinkW_U5=10.0, SinkD_U5=5.00, SinkH_U5=20.0,     # fin tips filed 0.5 mm (5.5 -> 5.0) to clear the 7.0 mm +Y end wall
    SinkW_U6=10.0, SinkD_U6=5.50, SinkH_U6=20.0,
    SinkW_U7=10.0, SinkD_U7=5.00, SinkH_U7=20.0,     # fin tips filed 0.5 mm (5.5 -> 5.0) to clear the 7.0 mm +Y end wall
    SinkW_U8=10.0, SinkD_U8=5.50, SinkH_U8=20.0,
    SinkW_U9=10.0, SinkD_U9=5.50, SinkH_U9=20.0,
    ToSinkRot=0.0,                              # extra rotation (deg) about the vertical axis through the tab-face centre
    ToSinkTopGap=1.5,                           # gap from board bottom to sink top (clears THT lead stubs)
    Stagger_U4=0.0, Stagger_U5=0.0, Stagger_U6=0.0, Stagger_U7=0.0, Stagger_U8=0.0, Stagger_U9=0.0,  # per-regulator extra drop (mm)
    # panel parts on the -Y end wall: (x, z) of each part's axis, world mm
    # -Y end wall layout from Doug's photo (scaled from the 79.4 mm wall width; estimated):
    # Connector face = the -X wall (a 95.5-wide FB wall). Positions are y along the face (+Y end = the end with the USB-C),
    # ESTIMATED from Doug's description (photos not readable by this build step): screw, USB-C, DC jack, 3.5 mm, screw.
    VentN=5, VentD=5.0, VentRingD=9.5, VentZ=-0.5,            # top row: 5 chrome-ringed vent openings, evenly spaced
    RowZ=-14.0,                                               # bottom row height
    # (face screws removed per Doug: no screws on the connector face)
    JackY=0.0, JackZ=-14.0, JackHoleD=12.7, JackPanelT=6.0, JackCboreD=18.0,  # Adafruit 610 (max panel 8 mm -> counterbore)
    # No power switch: Doug switches the supply inline on the cable.
    # Amabro USB-C panel-mount breakout (Amazon B0H9S9C73Q). Listing: metal panel 20 x 6.6 mm (20.1 x 6.7 x 1.5),
    # PCB 11.9 mm wide, 2 mm screw holes. ESTIMATED: hole spacing, PCB depth/thickness, receptacle 8.94 x 3.26 x 7.35 (USB-C std).
    UsbY=-22.0, UsbZ=-14.0, UsbRot=0.0,   # 0 = plate and slot horizontal (screws left/right); 90 = vertical
    UsbPlateL=20.0, UsbPlateH=6.6, UsbPlateT=1.5, UsbHoleC=16.0, UsbHoleD=2.0,
    UsbPcbW=11.9, UsbPcbD=10.0, UsbPcbT=1.6, UsbRecW=8.94, UsbRecH=3.26, UsbRecL=7.35,
    UsbSkinT=1.0, UsbCutW=9.4, UsbCutH=3.7, UsbPocketW=20.6, UsbPocketH=7.2,
    # 3.5 mm jack: CESS model 318 stereo TRS panel socket, solder lugs, no switch (Amazon B00ZYWILMS). Listing has no drawing:
    # dimensions ASSUMED for this common style: M6x0.5 bushing 6 long, hex nut 8 AF x 2, round body 10 dia x 13, 3 solder lugs.
    AudioY=14.5, AudioZ=-16.0,          # 2 mm below the row: body clears the horizontal TO-220 overhanging the -X board edge
    AudioHoleD=6.2, AudioCboreD=12.0, AudioPanelT=3.0,   # 3 mm skin left so the 6 mm thread takes the 2 mm nut
    AudioBushD=6.0, AudioBushL=6.0, AudioNutAF=8.0, AudioNutT=2.0, AudioBodyD=10.0, AudioBodyL=13.0, AudioLugL=4.0,
    # XIAO nRF52840 (U10) on 2x 1x7 female headers + the module's own male-header spacer
    XiaoX=144.272 - 124.715, XiaoY=-(134.62 - 110.235), 
    # AHT20 breakout on the existing 1x4 male header "AHT20" (plastic 2.54 mm)
    AhtHeaderX=145.552 - 124.715, AhtHeaderY=-(121.158 - 110.235), 
    # UMLIFE AHT20 module (Amazon B09B9ZWSDZ): 10.41 along the header row x 15.11, 1.6 PCB; parametric placeholder
    FootD=5.0, FootH=5.0, FootInset=6.0,   # enclosure feet (Doug), centres inset 6 mm from the outer corners
    TbH=8.5,             # ASSUMED screw terminal body height (KF128/XY308-2.54 style)
    LeadClip=1.5,        # LM317 lead protrusion past the solder (top) side after clipping
    HdrPlastic=2.54, HdrPinBelow=3.0, HdrPinAbove=6.0, HdrPin=0.64,   # shared 2.54 mm male pin header (AHT20 1x4, XIAO 2 x 1x7)
    AhtW=10.41, AhtL=15.11, AhtT=1.6, AhtPinInset=1.27, AhtDir=1,   # AhtDir +1: extends to world +Y (KiCad -Y), as before
)
# cone length so its top is ConeTopGap below the lid top: lid top z = BoxH - Standoff - Floor; cone base z = BoardT + LedTop
P["ConeL"] = round(P["BoxH"] - P["Standoff"] - P["Floor"] - P["ConeTopGap"] - (P["BoardT"] + P["LedTop"]), 3)
HOLES = [(-27.685, 37.845), (27.685, 37.845), (-27.685, -37.845), (27.685, -37.845)]

# LM317 TO-220 vertical (bottom side).  Values read from the KiCad STEP:
# (body xmin, xmax, ymin, ymax, tab direction) ; heatsink is bolted to the tab side.
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
# LM317 (U4-U9) leads: the KiCad TO-220 model leaves 8.07 mm sticking out of the solder (top) side; clip them to
# LeadClip (1.5 mm, standard trimmed length) above the board top. Pad centres from the kicad_pcb (world coords).
LM317_PADS = {"U4": [(-24.536, 23.541), (-24.536, 26.081), (-24.536, 28.621)], "U5": [(-3.223, 32.296), (-5.763, 32.296), (-8.303, 32.296)],
              "U6": [(-8.303, 27.328), (-5.763, 27.328), (-3.223, 27.328)], "U7": [(12.271, 32.296), (9.731, 32.296), (7.191, 32.296)],
              "U8": [(7.191, 27.328), (9.731, 27.328), (12.271, 27.328)], "U9": [(22.168, 23.447), (22.168, 25.987), (22.168, 28.527)]}
_clipz = P["BoardT"] + P["LeadClip"]
_cols = [Part.makeBox(1.6, 1.6, 40, App.Vector(x - 0.8, y - 0.8, _clipz)) for pl in LM317_PADS.values() for (x, y) in pl]
_colf = _cols[0].multiFuse(_cols[1:])
LEAD_OLD = LEAD_NEW = None
_new = []
for _s in sols[1:]:
    if _s.BoundBox.intersect(_colf.BoundBox) and _s.common(_colf).Volume > 1e-6:
        LEAD_OLD = max(LEAD_OLD or 0, _s.BoundBox.ZMax - P["BoardT"])
        _s = _s.cut(_colf); LEAD_NEW = max(LEAD_NEW or 0, _s.BoundBox.ZMax - P["BoardT"])
    _new.append(_s)
comps = Part.makeCompound(_new)
allb = App.BoundBox()
for _s in [board] + _new: allb.add(_s.BoundBox)   # envelope after lead clipping
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

# cut-outs: fan screw holes (floor); vents, screws, DC jack, USB-C, 3.5 mm jack (-X connector wall)
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
VENT_Y = [(-P["BoxL"]/2) + P["BoxL"] * (k + 1) / (P["VentN"] + 1) for k in range(int(P["VentN"]))]
for vy in VENT_Y:
    cutters.append(xcyl(P["VentD"]/2, vy, P["VentZ"], XN - 1, WF + 2))
cutters.append(xcyl(P["AudioHoleD"]/2, P["AudioY"], P["AudioZ"], XN - 1, WF + 2))
cutters.append(xcyl(P["AudioCboreD"]/2, P["AudioY"], P["AudioZ"], XN + P["AudioPanelT"], WF))     # inside counterbore
# USB-C: plate stood vertical (UsbRot=90): cut-out/pocket dims swap W<->H
uw, uh = (P["UsbCutH"], P["UsbCutW"]) if abs(P["UsbRot"] - 90) < 1 else (P["UsbCutW"], P["UsbCutH"])
pw, ph = (P["UsbPocketH"], P["UsbPocketW"]) if abs(P["UsbRot"] - 90) < 1 else (P["UsbPocketW"], P["UsbPocketH"])
cutters.append(Part.makeBox(WF + 2, uw, uh, V(XN - 1, P["UsbY"] - uw/2, P["UsbZ"] - uh/2)))
cutters.append(Part.makeBox(WF, pw, ph, V(XN + P["UsbSkinT"], P["UsbY"] - pw/2, P["UsbZ"] - ph/2)))
# no screw holes for the USB-C plate (face screws removed per Doug); the plate is held in its inside pocket (glue/epoxy)
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
    so = doc.addObject("Part::Prism", "Standoff_M3_%d" % i)
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
# J1-J3: 2.54 mm pitch PCB screw terminals (KF128/DG308-2.54 style, footprint Xinya XY308-2.54-nP). No STEP in the KiCad
# library, and the JSZAAHZ kit listing (B0FCXV6GT3) gives no dimensions -> body ASSUMED from the XY308 footprint fab outline:
# (n-1)*2.54 + 3.04 long x 6.5 deep (pins 3.1 from the back, 3.4 from the wire side) x TbH tall; wire entries on the KiCad +y side.
TBLOCKS = {"J1": (2, 96.266, 105.664), "J2": (3, 102.108, 114.3), "J3": (4, 145.542, 102.616)}   # pin count, pad 1 (PCB mm), rotation 0
def tblock_shape(n):
    L = (n - 1) * 2.54 + 3.04
    b = Part.makeBox(L, 6.5, P["TbH"], V(-1.52, -3.4, 0))           # world y = -KiCad y: wire side faces world -Y
    for i in range(n):
        b = b.cut(Part.makeBox(1.8, 3.0, 2.0, V(i * 2.54 - 0.9, -3.41, 1.2)))                   # wire entry
        b = b.cut(Part.makeCylinder(1.0, 1.5, V(i * 2.54, 0.4, P["TbH"] - 1.5)))               # screw access
    return b
tbs = []
for ref, (n, px, py) in TBLOCKS.items():
    o = doc.addObject("Part::Feature", "%s_ScrewTerminal_2p54_%dP" % (ref, n))
    o.Shape = tblock_shape(n); o.Placement.Base = V(px - 124.715, -(py - 110.235), P["BoardT"])
    tbs.append(o)
j1 = tbs[0]
grp_hw.addObjects([led] + tbs)

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

# LED pad sink: uxcell 30x20x10 with its pre-applied thermal pad under the exposed pad (board bottom), centred on the LED.
tape = doc.addObject("Part::Feature", "ThermalPad_uxcell")
tape.Shape = Part.makeBox(P["LedSinkL"], P["LedSinkW"], P["TapeT"], V(-P["LedSinkL"]/2, -P["LedSinkW"]/2, 0))
tape.Placement = App.Placement(V(LEDX, LEDY, -P["TapeT"]), App.Rotation(V(0, 0, 1), P["LedSinkRot"]))
def led_sink_shape(P):
    L, W, H, n, t, b = P["LedSinkL"], P["LedSinkW"], P["LedSinkH"], int(P["LedSinkFins"]), P["LedSinkFinT"], P["LedSinkBase"]
    sh = Part.makeBox(L, W, b, V(-L/2, -W/2, H - b))
    pitch = (W - t) / (n - 1)
    for k in range(n):                       # fins run along L (local x): channels along x
        sh = sh.fuse(Part.makeBox(L, t, H - b, V(-L/2, -W/2 + k * pitch, 0)))
    return sh.removeSplitter()
ledsink = doc.addObject("Part::Feature", "Heatsink_LED_uxcell_30x20x10")
ledsink.Shape = led_sink_shape(P)
ledsink.Placement = App.Placement(V(LEDX, LEDY, -P["TapeT"] - P["LedSinkH"]), App.Rotation(V(0, 0, 1), P["LedSinkRot"]))
grp_th.addObjects([tape, ledsink])

def to220_sink(name, xmin, xmax, ymin, ymax, tab):
    """Finned bolt-on sink on the tab side (screwed to the TO-220 tab). Local frame: tab-face centre at origin, base plate y 0..Base,
    fins towards +y, z 0..H.  Size/fins from Params (re-run the script); stagger & rotation are expressions."""
    W, D, H, tb = P["SinkW_" + name], P["SinkD_" + name], P["SinkH_" + name], P["ToSinkBase"]
    ft, slot = P["ToSinkFinT"], P["ToSinkSlot"]
    sh = Part.makeBox(W, tb, H, V(-W/2, 0, 0))
    # 4 fins: two at the edges, two flanking the centre screw channel (HSK-059 profile)
    for x0 in (-W/2, -slot/2 - ft, slot/2, W/2 - ft):
        sh = sh.fuse(Part.makeBox(ft, D, H, V(x0, 0, 0)))
    zh = P["ToSinkHoleZ"] - (-P["ToSinkTopGap"] - H - P["Stagger_" + name])     # tapped M3 hole height in local z
    sh = sh.cut(Part.makeCylinder(1.25, tb + 0.2, V(0, -0.1, zh), V(0, 1, 0)))
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

# Custom 3D-printable fan grill on the outside of the floor. Built in PRINT orientation (outer face on z=0,
# locating ring up), exported as STL/STEP; installed the same way up (outer face down, ring up into the floor hole).
def make_grill(P):
    S, R_, T = P["GrillS"], P["GrillR"], P["GrillT"]
    plate = Part.makeBox(S - 2*R_, S, T, V(-S/2 + R_, -S/2, 0)).fuse(Part.makeBox(S, S - 2*R_, T, V(-S/2, -S/2 + R_, 0)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            plate = plate.fuse(Part.makeCylinder(R_, T, V(sx*(S/2 - R_), sy*(S/2 - R_), 0)))
    plate = plate.removeSplitter()
    rin = P["GrillOpenD"]/2 - P["GrillRingW"]            # honeycomb zone
    af, rib = P["GrillHexAF"], P["GrillRib"]
    pitch = af + rib; rc = af / math.sqrt(3)              # hex circumradius
    hexes = []
    n = int(rin / pitch) + 2
    for j in range(-n, n + 1):
        for i in range(-n, n + 1):
            cx = i * pitch + (pitch/2 if j % 2 else 0); cy = j * pitch * math.sqrt(3)/2
            if math.hypot(cx, cy) > rin + rc: continue
            pts = [V(cx + rc*math.cos(math.radians(30 + 60*k)), cy + rc*math.sin(math.radians(30 + 60*k)), -1) for k in range(7)]
            hexes.append(Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, T + 2)))
    holes = hexes[0].multiFuse(hexes[1:]).common(Part.makeCylinder(rin, T + 2, V(0, 0, -1)))
    g = plate.cut(holes)
    lo = P["GrillLocOD"]/2
    g = g.fuse(Part.makeCylinder(lo, P["GrillLocH"], V(0, 0, T)).cut(Part.makeCylinder(lo - P["GrillLocW"], P["GrillLocH"] + 2, V(0, 0, T - 1))))
    HC = P["FanHoleC"]; cd = (P["GrillCskD"] - P["GrillHoleD"]) / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = V(sx*HC/2, sy*HC/2, 0)
            g = g.cut(Part.makeCylinder(P["GrillHoleD"]/2, T + 2, c + V(0, 0, -1)))
            g = g.cut(Part.makeCone(P["GrillCskD"]/2 + 0.5, P["GrillHoleD"]/2, cd + 0.5, c + V(0, 0, -0.5)))  # 90 deg csk from the outer face
    return g.removeSplitter()
grill_print = make_grill(P)
grill_print.exportStl(os.path.join(HERE, "parts", "fan_grill_30mm.stl"))
grill_print.exportStep(os.path.join(HERE, "parts", "fan_grill_30mm.step"))
guard = doc.addObject("Part::Feature", "FanGrill_3Dprinted_36mm")
guard.Shape = grill_print
# flip: print z=0 (outer face) -> world BOX_BOT - GrillT, locating ring up into the floor hole
guard.Placement = App.Placement(V(P["FanX"], P["FanY"], BOX_BOT - P["GrillT"]), App.Rotation())   # print orientation = installed orientation (outer face down)
grp_th.addObject(guard)
# 4 x M3 x GrillScrewL flat-head screws + nuts on the fan top (for the clearance check)
scr_parts = []
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = P["FanX"] + sx*P["FanHoleC"]/2, P["FanY"] + sy*P["FanHoleC"]/2
        z0 = BOX_BOT - P["GrillT"]
        scr_parts.append(Part.makeCone(3.36, 1.5, 1.86, V(x, y, z0)).fuse(Part.makeCylinder(1.5, P["GrillScrewL"], V(x, y, z0))))
        nut = Part.makePolygon([V(x + 3.175*math.cos(math.radians(60*k)), y + 3.175*math.sin(math.radians(60*k)), FLOOR_TOP + P["FanT"]) for k in range(7)])
        scr_parts.append(Part.Face(nut).extrude(V(0, 0, P["GrillNutT"])).cut(Part.makeCylinder(1.5, 3, V(x, y, FLOOR_TOP + P["FanT"] - 0.2))))
grill_screws = doc.addObject("Part::Feature", "GrillScrews_M3_FH_x4"); grill_screws.Shape = Part.makeCompound(scr_parts)
grp_th.addObject(grill_screws)
# enclosure feet (Doug: 5 mm tall x 5 mm dia), inset FootInset from the outer corners
FEET_XY = [(sx * (P["BoxW"]/2 - P["FootInset"]), sy * (P["BoxL"]/2 - P["FootInset"])) for sx in (-1, 1) for sy in (-1, 1)]
feet = doc.addObject("Part::Feature", "Feet_5x5_x4")
feet.Shape = Part.makeCompound([Part.makeCylinder(P["FootD"]/2, P["FootH"], V(x, y, BOX_BOT - P["FootH"])) for (x, y) in FEET_XY])
grp_th.addObject(feet)

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
def cess_jack(P):
    """CESS 318-style 3.5 mm stereo TRS panel jack, ASSUMED dims. Local x = 0 at the outer wall face, +x into the box."""
    t = P["AudioPanelT"]
    body = Part.makeCylinder(P["AudioBodyD"]/2, P["AudioBodyL"], V(t, 0, 0), V(1, 0, 0))
    bush = Part.makeCylinder(P["AudioBushD"]/2, P["AudioBushL"], V(t - P["AudioBushL"], 0, 0), V(1, 0, 0))
    bush = bush.cut(Part.makeCylinder(1.8, P["AudioBushL"] + P["AudioBodyL"], V(t - P["AudioBushL"] - 0.1, 0, 0), V(1, 0, 0)))  # 3.5 mm plug bore
    rc = P["AudioNutAF"] / math.sqrt(3)
    nut = Part.Face(Part.makePolygon([V(-P["AudioNutT"], rc*math.cos(math.radians(60*k)), rc*math.sin(math.radians(60*k))) for k in range(7)])).extrude(V(P["AudioNutT"], 0, 0))
    nut = nut.cut(Part.makeCylinder(P["AudioBushD"]/2, 5, V(-3, 0, 0), V(1, 0, 0)))
    parts = [body, bush, nut]
    for k in range(3):                      # tip, ring, sleeve solder lugs off the back
        lug = Part.makeBox(P["AudioLugL"], 0.5, 2.5, V(t + P["AudioBodyL"], -0.25, 1.5))
        lug.rotate(V(0, 0, 0), V(1, 0, 0), 90 + 120 * k)
        parts.append(lug)
    return Part.makeCompound(parts)
audio = doc.addObject("Part::Feature", "Audio_CESS318_3p5mm_TRS")
audio.Shape = cess_jack(P)
audio.Placement.Base = V(XN, P["AudioY"], P["AudioZ"])
for o, ky, kz in ((jack, "JackY", "JackZ"), (usb, "UsbY", "UsbZ"), (audio, "AudioY", "AudioZ")):
    bind(o, ".Placement.Base.y", "Params." + ky); bind(o, ".Placement.Base.z", "Params." + kz)
# chrome vent eyelets and the two edge screws on the -X connector wall
rings = []
for vy in VENT_Y:
    r = xcyl(P["VentRingD"]/2, vy, P["VentZ"], XN - 1.0, 1.0).cut(xcyl(P["VentD"]/2, vy, P["VentZ"], XN - 2.0, 3.0))
    r = r.fuse(xcyl(P["VentD"]/2, vy, P["VentZ"], XN, WF).cut(xcyl(P["VentD"]/2 - 0.4, vy, P["VentZ"], XN - 1, WF + 2)))
    rings.append(r)
o_vents = doc.addObject("Part::Feature", "Vent_Eyelets_x5"); o_vents.Shape = Part.makeCompound(rings)
panel_parts = [jack, usb, audio]
grp_hw.addObjects(panel_parts + [o_vents])

# ---------------------------------------------------------------- XIAO nRF52840 (U10) on risers
grp_mod = doc.addObject("App::DocumentObjectGroup", "Modules")
BT = P["BoardT"]
def pin_header(name, n, x1, y, along=(1, 0)):
    """Shared 2.54 mm male pin header, 1 x n, plastic HdrPlastic tall sitting on the board top; square pins run from
    HdrPinBelow under the plastic (through the main board) to HdrPinAbove over it (through the module). x1/y = pin 1."""
    ax, ay = along
    pl = HdrPlastic = P["HdrPlastic"]
    sh = None
    for i in range(n):
        cx, cy = x1 + ax * i * 2.54, y + ay * i * 2.54
        b = Part.makeBox(2.54, 2.54, pl, V(cx - 1.27, cy - 1.27, BT))
        pin = Part.makeBox(P["HdrPin"], P["HdrPin"], P["HdrPinBelow"] + pl + P["HdrPinAbove"],
                           V(cx - P["HdrPin"]/2, cy - P["HdrPin"]/2, BT - P["HdrPinBelow"]))
        b = b.fuse(pin)
        sh = b if sh is None else sh.fuse(b)
    o = doc.addObject("Part::Feature", name); o.Shape = sh.removeSplitter()
    return o
xiao_bot = BT + P["HdrPlastic"]                   # XIAO sits on the header plastic, same as the AHT20
risers = []
for k, dy in enumerate((-7.62, 7.62)):          # pad rows 15.24 mm apart (pcb y 127.0 / 142.24)
    risers.append(pin_header("PinHeader_1x7_XIAO_%d" % (k + 1), 7, P["XiaoX"] - 7.62, P["XiaoY"] + dy))
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
def aht_shape(P, d):
    cx = P["AhtHeaderX"] + 3 * 2.54 / 2; yh = P["AhtHeaderY"]; z0 = BT + P["HdrPlastic"]
    y0 = yh - d * P["AhtPinInset"]; y1 = y0 + d * P["AhtL"]
    pcb_ = Part.makeBox(P["AhtW"], P["AhtL"], P["AhtT"], V(cx - P["AhtW"]/2, min(y0, y1), z0))
    ym = (y0 + y1) / 2 + d * 2.0
    sens = Part.makeBox(3.0, 3.0, 1.0, V(cx - 1.5, ym - 1.5, z0 + P["AhtT"]))
    return Part.makeCompound([pcb_, sens])
aht_hdr = pin_header("PinHeader_1x4_AHT20", 4, P["AhtHeaderX"], P["AhtHeaderY"])
aht = doc.addObject("Part::Feature", "AHT20_UMLIFE_module")
aht.Shape = aht_shape(P, P["AhtDir"])
aht_alt = aht_shape(P, -P["AhtDir"])   # opposite direction, for the report only
grp_mod.addObjects([aht_hdr, aht])

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
report.append("LM317 leads (U4-U9) clipped: %.2f -> %.2f mm past the solder (top) side (LeadClip %.1f)" % (LEAD_OLD, LEAD_NEW, P["LeadClip"]))
for _t in tbs:
    _b = _t.Shape.BoundBox
    report.append("%s: x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f, wire side y=%.2f (faces -Y); lid gap %.2f; gaps: cone %s, AHT20 %s, XIAO %s, PCB comps %s, walls X %.2f/%.2f" % (
        _t.Name, _b.XMin, _b.XMax, _b.YMin, _b.YMax, _b.ZMin, _b.ZMax, _b.YMin, (P["BoxH"] - P["Floor"] - P["LidT"] - P["Standoff"]) - _b.ZMax,
        "%.2f" % _t.Shape.distToShape(cone.Shape)[0], "%.2f" % _t.Shape.distToShape(aht.Shape)[0], "%.2f" % _t.Shape.distToShape(xiao.Shape)[0],
        ("CLASH %.1f mm3" % _t.Shape.common(o_comp.Shape).Volume) if _t.Shape.common(o_comp.Shape).Volume > 0.05 else "%.2f" % _t.Shape.distToShape(o_comp.Shape)[0],
        _b.XMin + P["BoxW"]/2 - P["WallFB"], P["BoxW"]/2 - P["WallFB"] - _b.XMax))
report.append("Lowest PCB part z=%.2f -> %.2f mm above floor" % (allb.ZMin, allb.ZMin - FLOOR_TOP))
report.append("Highest PCB part z=%.2f -> %.2f mm below lid underside" % (allb.ZMax, (P["BoxH"] - P["Floor"] - P["LidT"] - P["Standoff"]) - allb.ZMax))
cb = bb(cone)
lid_top = P["BoxH"] - P["Floor"] - P["Standoff"]
_d = cb.ZMax - lid_top
report.append("Cone top z=%.2f vs lid top z=%.2f -> %s; mouth OD %.1f in the %.1f lid hole (%.2f radial gap), cone vs lid overlap %.1f mm3" % (
    cb.ZMax, lid_top, "FLUSH (0.00)" if abs(_d) < 0.005 else ("sticks out %.2f mm" % _d if _d > 0 else "%.2f mm below the lid top" % -_d),
    P["ConeD"], P["ConeD"] + 1.0, 0.5, cone.Shape.common(woodlid.Shape).Volume))
inner_solid = Part.makeBox(2*iw2, 2*il2, P["BoxH"], V(-iw2, -il2, FLOOR_TOP))
movers = to_sinks + [ledsink, fan]
static = [o_comp, o_board] + [o for o in doc.Objects if o.Name.startswith("Standoff_")] + panel_parts + risers + [xiao, aht, aht_hdr]
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
_lsb = ledsink.Shape.BoundBox
report.append("LED sink uxcell 30x20x10: x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f, channels along %s; gaps: fan %.2f, %s" % (
    _lsb.XMin, _lsb.XMax, _lsb.YMin, _lsb.YMax, _lsb.ZMin, _lsb.ZMax, "X (toward the -X vent wall)" if abs(P["LedSinkRot"]) < 1 else "Y",
    ledsink.Shape.distToShape(fan.Shape)[0], ", ".join("%s %.2f" % (n, d) for d, n in sorted(
        ((ledsink.Shape.distToShape(x.Shape)[0], x.Name) for x in to_sinks + [o for o in doc.Objects if o.Name.startswith("Standoff_")] + [o_comp]))[:5])))
for o in to_sinks + [o for o in doc.Objects if o.Name.startswith("Standoff_")]:
    d = fan.Shape.distToShape(o.Shape)[0]
    report.append("  fan to %-24s %s" % (o.Name, ("%.2f mm" % d) if d > 1e-6 else "CLASH (touching/overlapping)"))
gb = guard.Shape.BoundBox
report.append("Fan grill (3D printed, %.0fx%.0f, %.1f thick, hex %.1f AF / %.1f ribs): z %.2f..%.2f -> sits %.2f mm proud of the floor underside (z %.2f)" % (
    P["GrillS"], P["GrillS"], P["GrillT"], P["GrillHexAF"], P["GrillRib"], gb.ZMin, gb.ZMax, BOX_BOT - gb.ZMin, BOX_BOT))
report.append("Feet: 4 x %.1f dia x %.1f tall at x +/-%.2f, y +/-%.2f (inset %.1f from the outer corners), table at z %.2f -> grill-to-table clearance %.2f mm; feet to grill %.2f mm (overlap %.1f mm3)" % (
    P["FootD"], P["FootH"], P["BoxW"]/2 - P["FootInset"], P["BoxL"]/2 - P["FootInset"], P["FootInset"], BOX_BOT - P["FootH"], gb.ZMin - (BOX_BOT - P["FootH"]),
    feet.Shape.distToShape(guard.Shape)[0], feet.Shape.common(guard.Shape).Volume))
report.append("  locating ring OD %.1f x %.1f tall in the %.1f floor hole (%.2f radial gap); grill vs floor overlap %.1f mm3, vs fan %.2f mm" % (
    P["GrillLocOD"], P["GrillLocH"], P["FloorHoleD"], (P["FloorHoleD"] - P["GrillLocOD"])/2, guard.Shape.common(box.Shape).Volume, guard.Shape.distToShape(fan.Shape)[0]))
sbb = grill_screws.Shape.BoundBox
report.append("  screws: 4 x M3 x %.0f flat head + thin nut, grill %.0f + floor %.0f + fan %.0f = %.0f mm grip; tips at z %.2f; nearest: %s" % (
    P["GrillScrewL"], P["GrillT"], P["Floor"], P["FanT"], P["GrillT"] + P["Floor"] + P["FanT"], sbb.ZMax, ", ".join("%s %.2f" % (n, d) for d, n in sorted(
        ((grill_screws.Shape.distToShape(x.Shape)[0], x.Name) for x in to_sinks + [ledsink, o_comp]))[:3])))
report.append("Floor hole %.1f mm dia under fan bore %.1f mm" % (P["FloorHoleD"], P["FanBore"]))
report.append("Cone: %.2f mm long, %.1f mm mouth OD, %.1f mm LED hole; lid hole %.1f mm" % (
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
others = [o_comp, o_board, fan, ledsink, cone, xiao, aht, led] + tbs + to_sinks + panel_parts + risers + \
         [o for o in doc.Objects if o.Name.startswith("Standoff_")]
report.append("TO-220 sinks (Adam Tech HSK-059-04, 10 W x 5.5 D, 35 mm stock cut to %.1f; M3 hole at z %.2f, %.2f below the sink top): U5/U7 fin tips filed to 5.0 deep for the +Y end wall:" % (P["SinkH_U4"], P["ToSinkHoleZ"], -(P["ToSinkHoleZ"] + P["ToSinkTopGap"])))
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
report.append("Power switch: none (switched inline on the supply cable)")
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
report.append("Shared header part pin_header(): 2.54 mm male header, plastic %.2f, pins %.2f sq x %.2f total (%.1f below the plastic, %.1f above); AHT20 1x4, XIAO 2 x 1x7" % (
    P["HdrPlastic"], P["HdrPin"], P["HdrPinBelow"] + P["HdrPlastic"] + P["HdrPinAbove"], P["HdrPinBelow"], P["HdrPinAbove"]))
_xc = xiao.Shape.common(o_comp.Shape).Volume
report.append("XIAO underside z=%.2f (%.2f above the board top, same as the AHT20 at %.2f); XIAO vs board parts: %s (overlap %.1f mm3); pin tips z=%.2f" % (
    xiao_bot, xiao_bot - BT, aht.Shape.BoundBox.ZMin - BT, gap(xiao, o_comp), _xc, BT + P["HdrPlastic"] + P["HdrPinAbove"]))
ab = aht.Shape.BoundBox
report.append("AHT20 (UMLIFE B09B9ZWSDZ placeholder): x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f; board edge x=%.2f (overhang %.2f), +X inner wall x=%.2f (%s)" % (
    ab.XMin, ab.XMax, ab.YMin, ab.YMax, ab.ZMin, ab.ZMax, board.BoundBox.XMax, ab.XMax - board.BoundBox.XMax, iw2,
    ("INTO WALL by %.2f mm" % (ab.XMax - iw2)) if ab.XMax > iw2 else "clear %.2f" % (iw2 - ab.XMax)))
report.append("  AHT20 gaps: XIAO risers %s, XIAO %s, cone %s, PCB comps %s" % (
    min(gap(aht, r) for r in risers), gap(aht, xiao), gap(aht, cone), gap(aht, o_comp)))
_alt = doc.addObject("Part::Feature", "_aht_alt"); _alt.Shape = aht_alt
abx = aht_alt.BoundBox
report.append("  (alternative, flipped direction: y %.2f..%.2f; +X wall %.2f; gaps: XIAO risers %s, XIAO %s, cone %s, PCB comps %s)" % (
    abx.YMin, abx.YMax, iw2 - abx.XMax, min(gap(_alt, r) for r in risers), gap(_alt, xiao), gap(_alt, cone), gap(_alt, o_comp)))
doc.removeObject("_aht_alt")
txt = doc.addObject("App::TextDocument", "FitReport"); txt.Text = "\n".join(report)
print("\n".join(report))

# ---------------------------------------------------------------- colours (GUI only)
if App.GuiUp:
    import FreeCADGui as Gui
    col = {
        "PCB_Board": (0.05, 0.40, 0.15), "PCB_Components": (0.15, 0.15, 0.17),
        "WoodBox": (0.72, 0.52, 0.30), "WoodLid": (0.78, 0.58, 0.36),
        "ReflectorCone": (0.85, 0.85, 0.88), "Heatsink_LED_uxcell_30x20x10": (0.15, 0.35, 0.85),
        "ThermalPad_uxcell": (0.95, 0.85, 0.30), "Fan_3010": (0.10, 0.10, 0.10), "FanGrill_3Dprinted_36mm": (0.15, 0.15, 0.17), "GrillScrews_M3_FH_x4": (0.8, 0.8, 0.82),
        "XIAO_nRF52840_U10": (0.15, 0.15, 0.6), "AHT20_UMLIFE_module": (0.1, 0.45, 0.15), "Feet_5x5_x4": (0.1, 0.1, 0.1),
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
visible = [o_board, o_comp, box, woodlid, cone, tape, ledsink, fan, guard, grill_screws, xiao, aht, aht_hdr, o_vents, led, feet] + tbs + panel_parts + risers + to_sinks + \
          [o for o in doc.Objects if o.Name.startswith(("Standoff_", "Screw_M3_"))]
import Import
Import.export(visible, OUT_STEP)
print("saved", OUT_FCSTD, OUT_STEP)
