#!/usr/bin/env python2
import itertools
import string
import struct
import sys
from PIL import Image

class Data(object):
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def byte(self, num):
        self.pos += num
        return self.data[self.pos - num:self.pos+1]

    def u8(self):
        return struct.unpack("B", self.byte(1))[0]

    def u16(self):
        return struct.unpack("H", self.byte(2))[0]

    def u32(self):
        return struct.unpack("I", self.byte(4))[0]

    def s8(self):
        return struct.unpack("b", self.byte(1))[0]

    def s16(self):
        return struct.unpack("h", self.byte(2))[0]

    def s32(self):
        return struct.unpack("i", self.byte(4))[0]

    def f(self):
        return struct.unpack("f", self.byte(4))[0]

    def d(self):
        return struct.unpack("d", self.byte(8))[0]

    def str(self):
        return self.byte(self.u32())

    def hexdump(self, num, sz = 16):
        printables = string.uppercase + string.lowercase + string.digits + ",-_;:#'~+*\\}][{/()=?/&%$\"!|<>`^"
        s = self.data[self.pos:self.pos+num]
        num = len(s)
        for l in xrange((num + sz - 1) // sz):
            line = ""
            for c in s[l*sz:l*sz + sz]:
                line += "%02x " % ord(c)
            line += " "
            for c in s[l*sz:l*sz + sz]:
                line += c if c in printables else "."
            print line

class dot(dict):
    def __setattr__(self, name, value):
        self[name] = value
    def __getattr__(self, name):
        return self[name]

texture_path = (sys.argv[2] + "/" if len(sys.argv) > 2 else "../Texture/")
texture_dirs = [texture_path + subdir for subdir in "m256,m128,m064,m032,Gray,Misc,ClassIcons".split(",")]
import visual
def draw_visual(material, triangles, points, _, brightness):
    for d in texture_dirs:
        try:
            material = visual.materials.loadTGA("%s/%s.tga" % (d, material))
        except:
            pass
        else:
            break
    f = visual.frame()
    mins = [min(c[i] for c in points) for i in xrange(3)]
    maxs = [max(c[i] for c in points) for i in xrange(3)]
    centers = [(mins[i] + maxs[i]) / 2.0 for i in xrange(3)]
    mins = [mins[i] - centers[i] for i in xrange(3)]
    maxs = [maxs[i] - centers[i] for i in xrange(3)]
    factor = 0.5 / max(max(maxs), -min(mins))
    offsets = [centers[c] * (1.0 - factor) for c in xrange(3)]
    tri = visual.faces(
        pos = [[(points[i][c] * factor) + offsets[c] for c in xrange(3)] for i in triangles],
        color = [(brightness[triangles[i]] / 255.0, 0, 0) for i in xrange(len(triangles))],
        #material = visual.materials.texture(material),
        frame = f
    )

    ev = visual.scene.mouse.getclick()
    f.visible = False
    del f
    del tri

def draw_matplotlib(_1, triangles, points, _2, brightness):
    from mpl_toolkits.mplot3d import Axes3D
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = Axes3D(fig)
    verts = [[points[i] for i in triangles[j:j+3]] for j in xrange(0, len(triangles), 3)]
    colors = [(i / len(triangles), 0.0, 0.0, 0.5) for i in triangles]
    ax.add_collection3d(Poly3DCollection(verts, edgecolors = colors))
    plt.show()

class _3DDB(object):
    def __init__(self, filename):
        d = Data(file(filename).read())

        assert(d.str() == "3DDB 1.0")
        self.db_name = d.str()

        self.materials = []
        for _ in xrange(d.u16()):
            name = d.str()
            fname = d.str()
            assert(d.u32() == 1)
            self.materials.append(name)

        n = d.u32()
        self.meshes = []
        for i in xrange(n):
            mesh = dot()
            #material, ?, triangles, texture_coordinates, points, brightness
            mesh.links = []
            for mat, unk, triangles, texture_coordinates, points, brightness in [[d.u16() for _ in xrange(6)] for _ in xrange(d.u16())]:
                link = dot()
                link.material = mat
                link.triangles = triangles
                link.points = points
                link.texture_coordinates = texture_coordinates
                link.brightness = brightness
                link.unk = unk
                mesh.links.append(link)
            mesh.unk1 = [d.f() for _ in xrange(3)]
            mesh.unk2 = [d.f() for _ in xrange(3)]
            mesh.unk3 = d.byte(0x80)
            mesh.unk4 = d.u16()
            mesh.unk5 = d.byte(0x30)
            mesh.unk6 = d.u16()
            self.meshes.append(mesh)

        n = d.u16()
        self.objects = {}
        for _ in xrange(n):
            name = d.str()
            self.objects[name] = [d.u32() for _ in xrange(d.u16())]

        n = d.u16()
        self.animations = []
        for _ in xrange(n):
            anim = dot()
            anim.name = d.str()
            anim.meshes = [d.u32() for _ in xrange(d.u16())]
            anim.unk1 = d.u16()
            anim.unk2 = d.f()
            d.str()
            anim.unk3 = [d.f() for _ in xrange(3)]
            anim.unk4 = [d.f() for _ in xrange(3)]
            self.animations.append(anim)

        n = d.u16()
        for i in xrange(n):
            tmp = d.byte(32*32)
            img = Image.new("RGB", (32, 32), "white")
            for x,y in itertools.product(range(32),range(32)):
                c = ord(tmp[x+y*32])
                img.putpixel((x,y), (c,c,c))
            #img.save("shadow_%s_%d.bmp" % (self.db_name, i))

        n = d.u16()
        self.cmaps = []
        for i in xrange(n):
            cmap = dot()
            cmap.width = d.u16()
            cmap.height = d.u16()
            cmap.unk1 = d.u16()
            cmap.unk2 = d.u16()
            tmp = d.byte(cmap.width * cmap.height)
            cmap.data = dict(((x,y), ord(tmp[x+y*cmap.width])) for (x,y) in itertools.product(range(cmap.width), range(cmap.height)))
            self.cmaps.append(cmap)

        self.triangles = d.u16()
        self.texture_coordinates = d.u16()
        self.points = d.u16()
        self.brightness = d.u16()
        self.unk2 = d.u32()

        self.triangles = [d.u16() for _ in xrange(self.triangles)]
        self.texture_coordinates = [d.u16() for _ in xrange(self.texture_coordinates)]
        self.points = [d.u16() for _ in xrange(self.points)]
        self.brightness = [d.u16() for _ in xrange(self.brightness)]
        self.unk2 = [d.byte(20) for _ in xrange(self.unk2)]

        self.triangles = [[d.u16() for _ in xrange(n)] for n in self.triangles]
        self.texture_coordinates = [[(d.f(),d.f()) for _ in xrange(n)] for n in self.texture_coordinates]
        self.points = [[(d.u16()/float(0xffff),d.u16()/float(0xffff),d.u16()/float(0xffff)) for _ in xrange(n)] for n in self.points]
        self.brightness = [[d.u8() for _ in xrange(n)] for n in self.brightness]
        assert(d.pos == len(d.data))

    def _print(self):
        for object_name, animations in self.objects.iteritems():
            for anim in [self.animations[i] for i in animations]:
                for mesh_index, mesh in enumerate([self.meshes[i] for i in anim.meshes]):
                    for link_index, link in enumerate(mesh.links):
                        print "%s.%s.%s.%d.%d" % (self.db_name, object_name, anim.name, mesh_index, link_index)
                        triangles = self.triangles[link.triangles]
                        points = self.points[link.points]
                        texture_coordinates = self.texture_coordinates[link.texture_coordinates]
                        brightness = self.brightness[link.brightness]
                        if sum(len(i) for i in [triangles, points, texture_coordinates, brightness]) == 0:
                            print "  no data"
                            continue
                        draw_opengl(self.materials[link.material], triangles, points, texture_coordinates, brightness)
import pyglet
import pyglet.gl as gl

class camera(object):
    """ A camera.
    """
    mode = 3
    x, y, z = 0, 0, 512
    rx, ry, rz = 30, -45, 0
    w, h = 640, 480
    far = 8192
    fov = 60

    def view(self, width, height):
        """ Adjust window size.
        """
        self.w, self.h = width, height
        gl.glViewport(0, 0, width, height)
        print "Viewport " + str(width) + "x" + str(height)
        if self.mode == 2:
            self.isometric()
        elif self.mode == 3:
            self.perspective()
        else:
            self.default()

    def default(self):
        """ Default pyglet projection.
        """
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, self.w, 0, self.h, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def isometric(self):
        """ Isometric projection.
        """
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(-self.w/2., self.w/2., -self.h/2., self.h/2., 0, self.far)
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def perspective(self):
        """ Perspective projection.
        """
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluPerspective(self.fov, float(self.w)/self.h, 0.1, self.far)
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def key(self, symbol, modifiers):
        """ Key pressed event handler.
        """
        if symbol == pyglet.window.key.F1:
            self.mode = 1
            self.default()
            print "Projection: Pyglet default"
        elif symbol == pyglet.window.key.F2:
            print "Projection: 3D Isometric"
            self.mode = 2
            self.isometric()
        elif symbol == pyglet.window.key.F3:
            print "Projection: 3D Perspective"
            self.mode = 3
            self.perspective()
        elif self.mode == 3 and symbol == pyglet.window.key.NUM_SUBTRACT:
            self.fov -= 1
            self.perspective()
        elif self.mode == 3 and symbol == pyglet.window.key.NUM_ADD:
            self.fov += 1
            self.perspective()
        else: print "KEY " + pyglet.window.key.symbol_string(symbol)

    def drag(self, x, y, dx, dy, button, modifiers):
        """ Mouse drag event handler.
        """
        if button == 1:
            self.x -= dx*2
            self.y -= dy*2
        elif button == 2:
            self.x -= dx*2
            self.z -= dy*2
        elif button == 4:
            self.ry += dx/4.
            self.rx -= dy/4.
        else:
            print "BTN " + str(button)

    def apply(self):
        """ Apply camera transformation.
        """
        gl.glLoadIdentity()
        if self.mode == 1: return
        gl.glTranslatef(-self.x, -self.y, -self.z)
        gl.glRotatef(self.rx, 1, 0, 0)
        gl.glRotatef(self.ry, 0, 1, 0)
        gl.glRotatef(self.rz, 0, 0, 1)

def draw_opengl(material, triangles, points, texture_coordinates, brightness):
    for d in texture_dirs:
        try:
            texture = pyglet.image.load("%s/%s.tga" % (d, material)).get_texture()
        except IOError:
            pass
        else:
            break
    win = pyglet.window.Window(resizable = True)
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glDepthFunc(gl.GL_LEQUAL)

    cam = camera()
    win.on_resize = cam.view
    win.on_mouse_drag = cam.drag

    factors = [1.0,1.0,1.0]
    offsets = [0.0,0.0,0.0]

    @win.event
    def on_draw():
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        cam.apply()
        gl.glEnable(texture.target)
        gl.glBindTexture(texture.target,texture.id)
        gl.glBegin(gl.GL_TRIANGLES)
        for i in triangles:
            tmp = [(p-0.5) * 10000.0 for p in points[i]]
            gl.glTexCoord2f(*texture_coordinates[i])
            gl.glColor3f(brightness[i] / 255.0, brightness[i] / 255.0, brightness[i] / 255.0)
            gl.glVertex3f(*tmp)
        gl.glEnd()

    @win.event
    def on_key_press(symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()
        else:
            cam.key(symbol, modifiers)

    @win.event
    def on_close():
        pyglet.app.exit()

    pyglet.app.run()

if __name__ == '__main__':
    db = _3DDB(sys.argv[1])
    db._print()