using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Wiggles3db
{
    class _3DDB
    {
        public string version;
        public string name;
        public List<Material> materials = new List<Material>();
        public List<Mesh> meshes = new List<Mesh>();
        public Dictionary<string, uint[]> objects = new Dictionary<string, uint[]>();
        public List<Animation> animations = new List<Animation>();
        public List<CMap> cMaps = new List<CMap>();

        public List<List<ushort>> triangles = new List<List<ushort>>();
        public List<List<float[]>> texture_coordinates = new List<List<float[]>>();
        public List<List<float[]>> points = new List<List<float[]>>();
        public List<List<byte>> brightness = new List<List<byte>>();
        public string[] unknown;
    }
}
