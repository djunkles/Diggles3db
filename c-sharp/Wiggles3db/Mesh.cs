using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Wiggles3db
{
    class Mesh
    {
        public List<Link> links = new List<Link>();
        public float[] unknown1;
        public float[] unknown2;
        public object unknown3;
        public ushort unknown4;
        public object unknown5;
        public ushort unknown6;
    }

    class Link
    {
        public ushort material;
        public ushort triangles;
        public ushort points;
        public ushort texture_coordinates;
        public ushort brightness;
        public ushort unknown;
    }
}
