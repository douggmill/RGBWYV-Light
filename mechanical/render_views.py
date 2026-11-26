# Renders PNG views of the assembly. Needs the GUI (an X display):
#   xvfb-run -a freecad render_views.py        (Flatpak: flatpak run org.freecad.FreeCAD render_views.py)
# Rebuilds the model via build_assembly.py, applies colours, writes renders/*.png, saves the FCStd.
import FreeCAD as App, FreeCADGui as Gui, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
sys.argv=[]
App.ParamGet("User parameter:BaseApp/Preferences/View").SetBool("UseNavigationAnimations", False)
try:
    B=os.path.join(HERE,"build_assembly.py"); exec(open(B).read(), {"__file__":B,"__name__":"__main__"})
    doc=App.ActiveDocument
    Gui.ActiveDocument=Gui.getDocument(doc.Name)
    v=Gui.ActiveDocument.ActiveView
    for o in doc.Objects:
        try: o.ViewObject.Visibility=False
        except Exception: pass
    show=["PCB_Board","PCB_Components","WoodBox","WoodLid","ReflectorCone","Tape_3M8810","Heatsink_LED_20x20x10","Fan_3010","FanGuard_Qualtek_08346","DC_Jack_Adafruit610","Switch_Adafruit916","USB_C_Amabro_B0H9S9C73Q","Audio_Adafruit3692","XIAO_nRF52840_U10","AHT20_Adafruit4566","Vent_Eyelets_x5","FaceScrews_x2","LED_D2_placeholder","J1_TerminalBlock_approx"]
    show+=[o.Name for o in doc.Objects if o.Name.startswith(("Heatsink_TO220","Standoff_","Screw_M3_","XIAO_Riser","XIAO_MaleHdr"))]
    for n in show: doc.getObject(n).ViewObject.Visibility=True
    O=os.path.join(HERE,"renders")+os.sep; os.makedirs(O,exist_ok=True)
    def shot(name, view, setup=None):
        getattr(v,view)(); v.fitAll()
        v.saveImage(O+name,1600,1200,"White")
    doc.getObject("WoodBox").ViewObject.Transparency=0; doc.getObject("WoodLid").ViewObject.Transparency=0
    shot("assembly_iso_closed.png","viewIsometric")
    for nm, zv in (("assembly_connector_face.png", (-1, 0, 0)), ("assembly_connector_iso.png", (-1, -0.7, 0.6))):
        v.viewIsometric(); zl=App.Vector(*zv).normalize(); up=App.Vector(0,0,1); yl=(up-zl*(up.dot(zl))).normalize(); xl=yl.cross(zl)
        v.setCameraOrientation(App.Rotation(xl,yl,zl,"ZYX")); v.fitAll(); v.saveImage(O+nm,1600,1200,"White")
    shot("assembly_bottom_guard.png","viewBottom")
    v.viewIsometric(); zl=App.Vector(1,-1,-1).normalize(); up=App.Vector(0,0,1); yl=(up-zl*(up.dot(zl))).normalize(); xl=yl.cross(zl); v.setCameraOrientation(App.Rotation(xl,yl,zl,"ZYX")); v.fitAll(); v.saveImage(O+"assembly_underside_iso.png",1600,1200,"White")
    doc.getObject("WoodBox").ViewObject.Transparency=75; doc.getObject("WoodLid").ViewObject.Transparency=75
    shot("assembly_iso_transparent.png","viewIsometric")
    # rear/underside view
    import pivy
    v.viewIsometric(); 
    from FreeCAD import Rotation
    cam=v.getCameraNode()
    zl=App.Vector(-1,1,-1).normalize(); up=App.Vector(0,0,1); yl=(up-zl*(up.dot(zl))).normalize(); xl=yl.cross(zl); v.setCameraOrientation(App.Rotation(xl,yl,zl,'ZYX'))
    v.fitAll(); v.saveImage(O+"assembly_fan_side_transparent.png",1600,1200,"White")
    # exploded-ish: hide lid & box, show innards
    doc.getObject("WoodLid").ViewObject.Visibility=False
    doc.getObject("WoodBox").ViewObject.Transparency=0
    shot("assembly_iso_lid_off.png","viewIsometric")
    # cutaway: section through LED centre along X using a cut copy of the box
    import Part
    half=Part.makeBox(200,200,200,App.Vector(-100,-200+0.0,-100))  # keep y<0? keep front half removed
    for n in show:
        o=doc.getObject(n)
        o.ViewObject.Visibility=False
    cut_objs=[]
    for n in show:
        o=doc.getObject(n)
        try:
            s=o.Shape.cut(Part.makeBox(200,200,200,App.Vector(-100,-200.0,-100)))  # remove front (y<0) half
        except Exception: continue
        c=doc.addObject("Part::Feature","Cut_"+n); c.Shape=s
        c.ViewObject.ShapeColor=o.ViewObject.ShapeColor
        cut_objs.append(c)
    doc.recompute()
    v.viewFront(); v.fitAll(); v.saveImage(O+"assembly_section_front.png",1600,1200,"White")
    v.viewIsometric(); v.fitAll(); v.saveImage(O+"assembly_section_iso.png",1600,1200,"White")
    for c in cut_objs: doc.removeObject(c.Name)
    # PCB only views
    for n in show: doc.getObject(n).ViewObject.Visibility=False
    for n in ("PCB_Board","PCB_Components"): doc.getObject(n).ViewObject.Visibility=True
    shot("pcb_top.png","viewTop"); shot("pcb_bottom.png","viewBottom"); shot("pcb_iso.png","viewIsometric")
    for n in show: doc.getObject(n).ViewObject.Visibility=True
    doc.getObject("WoodBox").ViewObject.Transparency=60; doc.getObject("WoodLid").ViewObject.Transparency=60
    for n in [o.Name for o in doc.Objects if o.Name in ("BoxOuter","BoxInner","BoxShell","WallCutouts","BoxWithCutouts","FloorFanHole","LidOuter","LidInner","LidCap","LidConeHole","ReflectorOuter","ReflectorInner")]:
        doc.getObject(n).ViewObject.Visibility=False
    doc.save()
    print("RENDER_DONE")
    
except Exception:
    import traceback; traceback.print_exc()
finally:
    sys.stdout.flush(); os._exit(0)
