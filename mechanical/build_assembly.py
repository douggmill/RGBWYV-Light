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
    BoxL=3.75 * IN,      # outer, along board Y (long side)
    BoxW=3.125 * IN,     # outer, along board X
    BoxH=2.5 * IN,       # outer, incl. lid
    Wall=6.0,            # ASSUMED wall / floor / lid thickness
    Standoff=26.0,       # M3 x 26 standoffs, floor -> board bottom
    BoardT=1.6,
    LedTop=2.0,          # ASSUMED LED package height above board (D2 has no 3D model)
    ConeD=2.0 * IN, ConeL=1.25 * IN, ConeHole=12.0, ConeWall=1.5,
    LedSinkW=20.0, LedSinkH=10.0, TapeT=0.25,   # 20x20x10 sink + 3M 8810 tape
    FanS=20.0, FanT=10.0,                       # WINSINN 2010
    ToSinkW=15.0, ToSinkD=10.0, ToSinkH=20.0,   # Easycargo 20x15x10 TO-220 sinks
)
HOLES = [(-27.685, 37.845), (27.685, 37.845), (-27.685, -37.845), (27.685, -37.845)]

# LM317 TO-220 vertical (bottom side).  Values read from the KiCad STEP:
# (body xmin, xmax, ymin, ymax, tab direction) ; heatsink is clipped on the tab side.
LM317 = {
    "U_A": (-10.89, -0.64, 24.17, 28.62, "-Y"),
    "U_C": (4.61, 14.86, 24.17, 28.62, "-Y"),
    "U_D": (-10.89, -0.64, 31.00, 35.46, "+Y"),
    "U_E": (4.61, 14.86, 31.00, 35.46, "+Y"),
    "U_B": (20.87, 25.33, 20.86, 31.11, "+X"),
    "U_F": (-25.83, -21.38, 20.96, 31.21, "+X"),
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
BOX_BOT = FLOOR_TOP - P["Wall"]
BODY_H = P["BoxH"] - P["Wall"]             # open box; lid is a separate body

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
outer.Height = BODY_H; bind(outer, "Height", "Params.BoxH - Params.Wall")
bind(outer, ".Placement.Base.x", "-Params.BoxW/2"); bind(outer, ".Placement.Base.y", "-Params.BoxL/2")
bind(outer, ".Placement.Base.z", "-Params.Standoff - Params.Wall")
inner = doc.addObject("Part::Box", "BoxInner")
bind(inner, "Length", "Params.BoxW - 2*Params.Wall"); bind(inner, "Width", "Params.BoxL - 2*Params.Wall")
bind(inner, "Height", "Params.BoxH")
bind(inner, ".Placement.Base.x", "-Params.BoxW/2 + Params.Wall")
bind(inner, ".Placement.Base.y", "-Params.BoxL/2 + Params.Wall")
bind(inner, ".Placement.Base.z", "-Params.Standoff")
shell = doc.addObject("Part::Cut", "BoxShell"); shell.Base = outer; shell.Tool = inner

# side-wall cut-outs: fan opening (-X wall), exhaust slots (+X wall), jack + switch (-Y wall)
FAN_Y0, FAN_Z0 = -15.0, FLOOR_TOP + 0.5
cutters = []
fan_hole = Part.makeCylinder(9.0, P["Wall"] + 2, V(-P["BoxW"]/2 - 1, FAN_Y0 + 10, FAN_Z0 + 10), V(1, 0, 0))
cutters.append(fan_hole)
for k in range(5):
    cutters.append(Part.makeBox(P["Wall"] + 2, 3.0, 16.0,
                                V(P["BoxW"]/2 - P["Wall"] - 1, -15 + k * 6.5, FLOOR_TOP + 3)))
JACK = (14.0, -13.0); SWITCH = (-2.0, -13.0)   # (x, z) on the -Y wall
cutters.append(Part.makeCylinder(5.6, P["Wall"] + 2, V(JACK[0], -P["BoxL"]/2 - 1, JACK[1]), V(0, 1, 0)))
cutters.append(Part.makeCylinder(6.3, P["Wall"] + 2, V(SWITCH[0], -P["BoxL"]/2 - 1, SWITCH[1]), V(0, 1, 0)))
for (hx, hy) in HOLES:   # countersunk screw holes in the floor
    cutters.append(Part.makeCylinder(1.7, P["Wall"] + 2, V(hx, hy, BOX_BOT - 1)))
o_cut = doc.addObject("Part::Feature", "WallCutouts"); o_cut.Shape = Part.makeCompound(cutters)
box = doc.addObject("Part::Cut", "WoodBox"); box.Base = shell; box.Tool = o_cut

lid = doc.addObject("Part::Box", "LidPlate")
bind(lid, "Length", "Params.BoxW"); bind(lid, "Width", "Params.BoxL"); bind(lid, "Height", "Params.Wall")
bind(lid, ".Placement.Base.x", "-Params.BoxW/2"); bind(lid, ".Placement.Base.y", "-Params.BoxL/2")
bind(lid, ".Placement.Base.z", "Params.BoxH - 2*Params.Wall - Params.Standoff")
lid_hole = doc.addObject("Part::Cylinder", "LidConeHole")
bind(lid_hole, "Radius", "Params.ConeD/2 + 0.5"); lid_hole.Height = 100
lid_hole.Placement.Base = V(0, 0, 0)
woodlid = doc.addObject("Part::Cut", "WoodLid"); woodlid.Base = lid; woodlid.Tool = lid_hole
grp_box.addObjects([outer, inner, shell, o_cut, box, lid, lid_hole, woodlid])

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
    W, D, H = P["ToSinkW"], P["ToSinkD"], P["ToSinkH"]
    # build with base plate against the tab: plate in local x-z plane at y=0, fins towards +y
    s = Part.makeBox(W, 2.0, H)
    for k in range(5):
        s = s.fuse(Part.makeBox(1.0, D, H, V(k * (W - 1.0) / 4, 0, 0)))
    s = s.removeSplitter()
    z0 = SINK_TOP_Z - H
    if tab in ("-Y", "+Y"):
        cx = (xmin + xmax) / 2
        if tab == "+Y":
            pl = App.Placement(V(cx - W/2, ymax, z0), App.Rotation())
        else:
            pl = App.Placement(V(cx + W/2, ymin, z0), App.Rotation(V(0, 0, 1), 180))
    else:
        cy = (ymin + ymax) / 2
        if tab == "+X":
            pl = App.Placement(V(xmax, cy + W/2, z0), App.Rotation(V(0, 0, 1), -90))
        else:
            pl = App.Placement(V(xmin, cy - W/2, z0), App.Rotation(V(0, 0, 1), 90))
    o = doc.addObject("Part::Feature", "Heatsink_TO220_" + name)
    o.Shape = s; o.Placement = pl
    return o

to_sinks = [to220_sink(n, *v) for n, v in LM317.items()]
grp_th.addObjects(to_sinks)

# fan on the -X wall, blowing in across the bottom side
fan_body = Part.makeBox(P["FanT"], P["FanS"], P["FanS"])
fan_body = fan_body.cut(Part.makeCylinder(9.0, P["FanT"] + 2, V(-1, 10, 10), V(1, 0, 0)))
hub = Part.makeCylinder(3.5, P["FanT"] - 1, V(0.5, 10, 10), V(1, 0, 0))
blades = hub
for k in range(5):
    b = Part.makeBox(1.0, 5.5, 2.2, V(P["FanT"]/2 - 0.5, 10 + 3.0, 10 - 1.1))
    b.rotate(V(0, 10, 10), V(1, 0, 0), k * 72)
    blades = blades.fuse(b)
fan = doc.addObject("Part::Feature", "Fan_WINSINN_2010")
fan.Shape = Part.makeCompound([fan_body, blades])
fan.Placement.Base = V(-P["BoxW"]/2 + P["Wall"], FAN_Y0, FAN_Z0)
grp_th.addObject(fan)

# ---------------------------------------------------------------- panel parts
jack = doc.addObject("Part::Feature", "DC_Jack_2p1mm")
jack.Shape = Part.makeCylinder(5.5, 14.0, V(JACK[0], -P["BoxL"]/2 + P["Wall"], JACK[1]), V(0, 1, 0)).fuse(
    Part.makeCylinder(7.0, 2.0, V(JACK[0], -P["BoxL"]/2 - 2.0, JACK[1]), V(0, 1, 0)))
sw = doc.addObject("Part::Feature", "Power_Switch")
sw.Shape = Part.makeCylinder(6.2, 16.0, V(SWITCH[0], -P["BoxL"]/2 + P["Wall"], SWITCH[1]), V(0, 1, 0)).fuse(
    Part.makeCylinder(7.5, 3.0, V(SWITCH[0], -P["BoxL"]/2 - 3.0, SWITCH[1]), V(0, 1, 0)))
grp_hw.addObjects([jack, sw])

doc.recompute()

# ---------------------------------------------------------------- fit report
def bb(o): return o.Shape.BoundBox
iw2 = P["BoxW"]/2 - P["Wall"]; il2 = P["BoxL"]/2 - P["Wall"]
report = []
report.append("Box inner: %.2f (X) x %.2f (Y) x %.2f (Z) mm" % (2*iw2, 2*il2, P["BoxH"] - 2*P["Wall"]))
b = board.BoundBox
report.append("Board %.2f x %.2f: X clearance %.2f/side, Y clearance %.2f/side"
              % (b.XLength, b.YLength, iw2 - b.XMax, il2 - b.YMax))
report.append("Component envelope X %.2f..%.2f -> min wall gap %.2f" % (allb.XMin, allb.XMax, iw2 - max(-allb.XMin, allb.XMax)))
report.append("Lowest PCB part z=%.2f -> %.2f mm above floor" % (allb.ZMin, allb.ZMin - FLOOR_TOP))
report.append("Highest PCB part z=%.2f -> %.2f mm below lid underside" % (allb.ZMax, (P["BoxH"] - 2*P["Wall"] - P["Standoff"]) - allb.ZMax))
cb = bb(cone)
lid_top = P["BoxH"] - P["Wall"] - P["Standoff"]
report.append("Cone top z=%.2f vs lid top z=%.2f -> sticks out %.2f mm" % (cb.ZMax, lid_top, cb.ZMax - lid_top))
inner_solid = Part.makeBox(2*iw2, 2*il2, P["BoxH"], V(-iw2, -il2, FLOOR_TOP))
movers = to_sinks + [ledsink, fan]
for o in movers:
    s = o.Shape
    sb = s.BoundBox
    out = s.cut(inner_solid).Volume
    hits = []
    for other in movers + [o_comp]:
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
txt = doc.addObject("App::TextDocument", "FitReport"); txt.Text = "\n".join(report)
print("\n".join(report))

# ---------------------------------------------------------------- colours (GUI only)
if App.GuiUp:
    import FreeCADGui as Gui
    col = {
        "PCB_Board": (0.05, 0.40, 0.15), "PCB_Components": (0.15, 0.15, 0.17),
        "WoodBox": (0.72, 0.52, 0.30), "WoodLid": (0.78, 0.58, 0.36),
        "ReflectorCone": (0.85, 0.85, 0.88), "Heatsink_LED_20x20x10": (0.75, 0.75, 0.78),
        "Tape_3M8810": (0.95, 0.85, 0.30), "Fan_WINSINN_2010": (0.10, 0.10, 0.10),
        "DC_Jack_2p1mm": (0.2, 0.2, 0.2), "Power_Switch": (0.6, 0.1, 0.1),
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
visible = [o_board, o_comp, box, woodlid, cone, tape, ledsink, fan, jack, sw] + to_sinks + \
          [o for o in doc.Objects if o.Name.startswith(("Standoff_", "Screw_M3_"))]
import Import
Import.export(visible, OUT_STEP)
print("saved", OUT_FCSTD, OUT_STEP)
