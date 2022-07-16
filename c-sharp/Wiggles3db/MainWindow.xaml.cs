using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System.IO;
using System.Windows.Media.Media3D;
using System.Windows.Media.Animation;
using System.Windows.Threading;

namespace Wiggles3db
{
    /// <summary>
    /// Interaktionslogik für MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        private static string fileName = "C:\\Users\\Patrick\\Downloads\\3DB-master\\3DB-master\\baby.3db";
        private static string texturePath = "C:\\Users\\Patrick\\Downloads\\3DB-master\\3DB-master\\Wiggles3DB";
        private bool mDown;
        private Point mLastPos;
        private PerspectiveCamera cam;
        private List<MeshGeometry3D> meshes;
        private GeometryModel3D geom;
        private int animIdx;
        private int idx;
        private _3DDB db;
        private List<DiffuseMaterial> mats;
        private DispatcherTimer timer;

        public MainWindow()
        {
            InitializeComponent();

            cam = new PerspectiveCamera();
            cam.Position = new Point3D(0, 0, 500);
            cam.LookDirection = new Vector3D(0, 0, -10);
            cam.FieldOfView = 45;
            viewport.Camera = cam;

            db = read3DBFile();
            foreach (Animation a in db.animations)
            {
                cbxAnimations.Items.Add(a.name);
            }
            System.Diagnostics.Debug.Print("3db-file read.");

            // Define 3D mesh object
            meshes = new List<MeshGeometry3D>();

            timer = new DispatcherTimer();
            timer.Interval = TimeSpan.FromMilliseconds(100);
            timer.Tick += timer_Tick;

            mats = new List<DiffuseMaterial>();
            FileInfo fi;
            foreach (Material m in db.materials)
            {
                fi = new FileInfo(texturePath + m.name + ".png");
                if (fi.Exists)
                {
                    mats.Add(new DiffuseMaterial(new ImageBrush(new BitmapImage(new Uri(fi.FullName)))));
                }
                else
                {
                    System.Diagnostics.Debug.Print(texturePath + m.name + ".png not found");
                    mats.Add(new DiffuseMaterial(Brushes.Red));
                }
            }
            mats.Clear();
            mats.Add(new DiffuseMaterial(Brushes.Red));
            mats.Add(new DiffuseMaterial(Brushes.Blue));

            System.Diagnostics.Debug.Print("mats set.");

            for (int i = 0; i < db.triangles.Count; i++)
            {
                meshes.Add(new MeshGeometry3D());
                geom = new GeometryModel3D(meshes[i], mats[db.meshes[(int)db.animations[animIdx].meshes[idx]].links[i].material]);
                group.Children.Add(geom);
            }
            group.Transform = new Transform3DGroup();
            System.Diagnostics.Debug.Print("transformgroup done.");

            genMesh();
            System.Diagnostics.Debug.Print("mesh generated.");
        }

        void timer_Tick(object sender, EventArgs e)
        {
            if (++idx == db.animations[animIdx].meshes.Count)
            {
                timer.Stop();
            }
            else
            {
                genMesh();
            }
        }

        private void genMesh()
        {
            MeshGeometry3D mesh;
            int meshIdx;

            for (int i = 0; i < meshes.Count; i++)
            {
                mesh = meshes[i];
                mesh.Positions.Clear();
                mesh.TextureCoordinates.Clear();

                if (db.animations[animIdx].meshes.Count > 0)
                {
                    meshIdx = (int)db.animations[animIdx].meshes[idx];
                    //Link l = db.meshes[meshIdx].links[1];
                    foreach (Link l in db.meshes[meshIdx].links)
                    {
                        foreach (int tIdx in db.triangles[l.triangles])
                        {
                            mesh.Positions.Add(new Point3D((db.points[l.points][tIdx][0] - 0.5) * 10000,
                                (db.points[l.points][tIdx][1] - 0.5) * 10000, (db.points[l.points][tIdx][2] - 0.5) * 10000));
                            mesh.TextureCoordinates.Add(new Point(db.texture_coordinates[l.texture_coordinates][tIdx][0],
                                db.texture_coordinates[l.texture_coordinates][tIdx][1]));
                        }
                    }
                }
            }
        }

        private _3DDB read3DBFile()
        {
            string val;
            uint count;
            uint count32;
            uint strlen;
            int pos = 0;

            StringBuilder sb = new StringBuilder();
            Byte[] data = File.ReadAllBytes(fileName);

            _3DDB db = new _3DDB();

            // DB Version
            strlen = BitConverter.ToUInt32(data, pos); pos += 4;
            db.version = Encoding.Default.GetString(data, pos, (int)strlen); pos += (int)strlen;
            System.Diagnostics.Debug.Assert(db.version == "3DDB 1.0", "Falsche DB-Version (" + db.version + ") - 3DDB 1.0 erwartet.");
            sb.AppendLine("Version: " + db.version);

            // Name
            strlen = BitConverter.ToUInt32(data, pos); pos += 4;
            db.name = Encoding.Default.GetString(data, pos, (int)strlen); pos += (int)strlen;
            sb.AppendLine("Name: " + db.name);

            // Materialien
            count = BitConverter.ToUInt16(data, pos); pos += 2;
            sb.AppendLine("Materialien: " + count);
            Material mat;
            for (int i = 0; i < count; i++)
            {
                mat = new Material();
                strlen = BitConverter.ToUInt32(data, pos); pos += 4;
                mat.name = Encoding.Default.GetString(data, pos, (int)strlen); pos += (int)strlen;
                sb.AppendLine("    Texturname: " + mat.name);
                strlen = BitConverter.ToUInt32(data, pos); pos += 4;
                mat.path = Encoding.Default.GetString(data, pos, (int)strlen); pos += (int)strlen;
                sb.AppendLine("    Datei: " + mat.path);
                strlen = BitConverter.ToUInt32(data, pos); pos += 4;
                System.Diagnostics.Debug.Assert(strlen == 1, "Strukturfehler");

                db.materials.Add(mat);
            }

            // Meshes
            count32 = BitConverter.ToUInt32(data, pos); pos += 4;
            sb.AppendLine("Gitter: " + count32);
            Mesh mesh; Link link;
            ushort shortCnt;
            for (int i = 0; i < count32; i++)
            {
                mesh = new Mesh();
                shortCnt = BitConverter.ToUInt16(data, pos); pos += 2;
                // material, ?, triangles, texture_coordinates, points, brightness
                for (int j = 0; j < shortCnt; j++ )
                {
                    link = new Link();
                    link.material = BitConverter.ToUInt16(data, pos); pos += 2;
                    link.unknown = BitConverter.ToUInt16(data, pos); pos += 2;
                    link.triangles = BitConverter.ToUInt16(data, pos); pos += 2;
                    link.texture_coordinates = BitConverter.ToUInt16(data, pos); pos += 2;
                    link.points = BitConverter.ToUInt16(data, pos); pos += 2;
                    link.brightness = BitConverter.ToUInt16(data, pos); pos += 2;

                    mesh.links.Add(link);
                }

                mesh.unknown1 = new float[]{
                    BitConverter.ToSingle(data, pos),
                    BitConverter.ToSingle(data, pos + 4),
                    BitConverter.ToSingle(data, pos + 8)}; pos += 12;
                mesh.unknown2 = new float[]{
                    BitConverter.ToSingle(data, pos),
                    BitConverter.ToSingle(data, pos + 4),
                    BitConverter.ToSingle(data, pos + 8)}; pos += 12;
                mesh.unknown3 = Encoding.Default.GetString(data, pos, 0x80); pos += 0x80;
                mesh.unknown4 = BitConverter.ToUInt16(data, pos); pos += 2;
                mesh.unknown5 = Encoding.Default.GetString(data, pos, 0x30); pos += 0x30;
                mesh.unknown6 = BitConverter.ToUInt16(data, pos); pos += 2;

                db.meshes.Add(mesh);
            }

            // Objects
            count = BitConverter.ToUInt16(data, pos); pos += 2;
            ushort objCnt;
            sb.AppendLine("Objekte: " + count);
            for (int i = 0; i < count; i++)
            {
                strlen = BitConverter.ToUInt32(data, pos); pos += 4;
                val = Encoding.Default.GetString(data, pos, (int)strlen); pos += (int)strlen;
                objCnt = BitConverter.ToUInt16(data, pos); pos += 2;
                db.objects.Add(val, new uint[objCnt]);

                sb.Append("    " + val + " hat " + objCnt.ToString() + " Felder:" + Environment.NewLine + "      ");
                for (int j = 0; j < objCnt; j++)
                {
                    db.objects[val][j] = BitConverter.ToUInt32(data, pos); pos += 4;
                    sb.Append(db.objects[val][j].ToString() + ",");
                }
                sb.AppendLine();
            }

            // Animations
            count = BitConverter.ToUInt16(data, pos); pos += 2;
            Animation anim;
            sb.AppendLine("Animationen: " + count);
            for (int i = 0; i < count; i++)
            {
                anim = new Animation();
                strlen = BitConverter.ToUInt32(data, pos); pos += 4;
                anim.name = Encoding.Default.GetString(data, pos, (int)strlen); pos += (int)strlen;

                shortCnt = BitConverter.ToUInt16(data, pos); pos += 2;
                for (int j = 0; j < shortCnt; j++)
                {
                    anim.meshes.Add(BitConverter.ToUInt32(data, pos)); pos += 4;
                }

                anim.unknown1 = BitConverter.ToUInt16(data, pos); pos += 2;
                anim.unknown2 = BitConverter.ToSingle(data, pos); pos += 4;
                strlen = BitConverter.ToUInt32(data, pos); pos += 4;
                anim.unknown = Encoding.Default.GetString(data, pos, (int)strlen); pos += (int)strlen;
                anim.unknown3 = new float[]{
                    BitConverter.ToSingle(data, pos),
                    BitConverter.ToSingle(data, pos + 4),
                    BitConverter.ToSingle(data, pos + 8)}; pos += 12;
                anim.unknown4 = new float[]{
                    BitConverter.ToSingle(data, pos),
                    BitConverter.ToSingle(data, pos + 4),
                    BitConverter.ToSingle(data, pos + 8)}; pos += 12;

                db.animations.Add(anim);
            }

            // Shadows
            count = BitConverter.ToUInt16(data, pos); pos += 2;
            sb.AppendLine("Schatten: " + count);
            for (int i = 0; i < count; i++)
            {
                pos += 32 * 32;
                //tmp = d.byte(32*32)
                //img = Image.new("RGB", (32, 32), "white")
                //for x,y in itertools.product(range(32),range(32)):
                //    c = ord(tmp[x+y*32])
                //    img.putpixel((x,y), (c,c,c))
                //#img.save("shadow_%s_%d.bmp" % (self.db_name, i))
            }

            // cmaps?
            count = BitConverter.ToUInt16(data, pos); pos += 2;
            CMap cmap;
            sb.AppendLine("cmaps?: " + count);
            for (int i = 0; i < count; i++)
            {
                cmap = new CMap();
                cmap.width = BitConverter.ToUInt16(data, pos); pos += 2;
                cmap.height = BitConverter.ToUInt16(data, pos); pos += 2;
                cmap.unknown1 = BitConverter.ToUInt16(data, pos); pos += 2;
                cmap.unknown2 = BitConverter.ToUInt16(data, pos); pos += 2;
                cmap.data = new byte[cmap.width,cmap.height];
                for (int j = 0; j < cmap.width; j++)
                {
                    for (int k = 0; k < cmap.height; k++)
                    {
                        cmap.data[j, k] = data[pos];
                        pos++;
                    }
                }

                db.cMaps.Add(cmap);
            }

            // Dreiecke
            count = BitConverter.ToUInt16(data, pos); pos += 2;
            sb.AppendLine("Dreiecke: " + count);
            for (ushort i = 0; i < count; i++)
                db.triangles.Add(new List<ushort>());

            // Texturkoordinaten
            count = BitConverter.ToUInt16(data, pos); pos += 2;
            sb.AppendLine("Texturkoordinaten: " + count);
            for (ushort i = 0; i < count; i++)
                db.texture_coordinates.Add(new List<float[]>());

            // Punkte
            count = BitConverter.ToUInt16(data, pos); pos += 2;
            sb.AppendLine("Punkte: " + count);
            for (ushort i = 0; i < count; i++)
                db.points.Add(new List<float[]>());

            // Helligkeit
            count = BitConverter.ToUInt16(data, pos); pos += 2;
            sb.AppendLine("Helligkeiten: " + count);
            for (ushort i = 0; i < count; i++)
                db.brightness.Add(new List<byte>());

            // Unknown
            db.unknown = new string[BitConverter.ToUInt32(data, pos)]; pos += 4;
            sb.AppendLine("Unknown: " + db.unknown.Length);


            // Dreiecke
            for (ushort i = 0; i < db.triangles.Count; i++)
            {
                count = BitConverter.ToUInt16(data, pos); pos += 2;
                for (ushort j = 0; j < count; j++) db.triangles[i].Add(0); 
            }

            // Texturkoordinaten
            for (ushort i = 0; i < db.texture_coordinates.Count; i++)
            {
                count = BitConverter.ToUInt16(data, pos); pos += 2;
                for (ushort j = 0; j < count; j++) db.texture_coordinates[i].Add(new float[2]);
            }

            // Punkte
            for (ushort i = 0; i < db.points.Count; i++)
            {
                count = BitConverter.ToUInt16(data, pos); pos += 2;
                for (ushort j = 0; j < count; j++) db.points[i].Add(new float[3]);
            }

            // Helligkeit
            for (ushort i = 0; i < db.brightness.Count; i++)
            {
                count = BitConverter.ToUInt16(data, pos); pos += 2;
                for (ushort j = 0; j < count; j++) db.brightness[i].Add(0);
            }

            // Unbekannt
            for (uint i = 0; i < db.unknown.Length; i++)
            {
                db.unknown[i] = Encoding.Default.GetString(data, pos, 20); pos += 20;
            }


            // Dreiecke
            for (ushort i = 0; i < db.triangles.Count; i++)
            {
                for (ushort j = 0; j < db.triangles[i].Count; j++)
                {
                    db.triangles[i][j] = BitConverter.ToUInt16(data, pos); pos += 2;
                }
            }

            // Texturkoordinaten
            for (ushort i = 0; i < db.texture_coordinates.Count; i++)
            {
                for (ushort j = 0; j < db.texture_coordinates[i].Count; j++)
                {
                    db.texture_coordinates[i][j][0] = BitConverter.ToSingle(data, pos); pos += 4;
                    db.texture_coordinates[i][j][1] = BitConverter.ToSingle(data, pos); pos += 4;
                }
            }

            // Punkte
            for (ushort i = 0; i < db.points.Count; i++)
            {
                for (ushort j = 0; j < db.points[i].Count; j++)
                {
                    db.points[i][j][0] = ((float)(BitConverter.ToUInt16(data, pos)) / 0xffff); pos += 2;
                    db.points[i][j][1] = ((float)(BitConverter.ToUInt16(data, pos)) / 0xffff); pos += 2;
                    db.points[i][j][2] = ((float)(BitConverter.ToUInt16(data, pos)) / 0xffff); pos += 2;
                    //db.points[i][j][0] = BitConverter.ToUInt16(data, pos); pos += 2;
                    //db.points[i][j][1] = BitConverter.ToUInt16(data, pos); pos += 2;
                    //db.points[i][j][2] = BitConverter.ToUInt16(data, pos); pos += 2;
                }
            }

            // Helligkeit
            for (ushort i = 0; i < db.brightness.Count; i++)
            {
                for (ushort j = 0; j < db.brightness[i].Count; j++)
                {
                    db.brightness[i][j] = data[pos]; pos += 1;
                }
            }

            tbInfo.Text = sb.ToString();

            if (pos != data.Length)
                tbInfo.AppendText(Environment.NewLine + "Es wurden nur " + pos.ToString() + "/" + data.Length.ToString() + " Bytes verarbeitet.");

            return db;
        }

        private void overlay_MouseMove(object sender, MouseEventArgs e)
        {
            if (!mDown) return;
            Point pos = Mouse.GetPosition(viewport);
            Point actualPos = new Point(
                    pos.X - viewport.ActualWidth / 2,
                    viewport.ActualHeight / 2 - pos.Y);
            double dx = actualPos.X - mLastPos.X;
            double dy = actualPos.Y - mLastPos.Y;
            double mouseAngle = 0;

            if (dx != 0 && dy != 0)
            {
                mouseAngle = Math.Asin(Math.Abs(dy) /
                    Math.Sqrt(Math.Pow(dx, 2) + Math.Pow(dy, 2)));
                if (dx < 0 && dy > 0) mouseAngle += Math.PI / 2;
                else if (dx < 0 && dy < 0) mouseAngle += Math.PI;
                else if (dx > 0 && dy < 0) mouseAngle += Math.PI * 1.5;
            }
            else if (dx == 0 && dy != 0)
            {
                mouseAngle = Math.Sign(dy) > 0 ? Math.PI / 2 : Math.PI * 1.5;
            }
            else if (dx != 0 && dy == 0)
            {
                mouseAngle = Math.Sign(dx) > 0 ? 0 : Math.PI;
            }

            double axisAngle = mouseAngle + Math.PI / 2;

            Vector3D axis = new Vector3D(
                    Math.Cos(axisAngle) * 4,
                    Math.Sin(axisAngle) * 4, 0);

            double rotation = 0.02 *
                    Math.Sqrt(Math.Pow(dx, 2) + Math.Pow(dy, 2));

            Transform3DGroup tGroup = group.Transform as Transform3DGroup;
            QuaternionRotation3D r = new QuaternionRotation3D(new Quaternion(axis, rotation * 180 / Math.PI));
            tGroup.Children.Add(new RotateTransform3D(r));

            mLastPos = actualPos;
        }

        private void overlay_MouseUp(object sender, MouseButtonEventArgs e)
        {
            mDown = false;
        }

        private void overlay_MouseWheel(object sender, MouseWheelEventArgs e)
        {
            cam.Position = new Point3D(
            cam.Position.X,
            cam.Position.Y,
            cam.Position.Z - e.Delta / 25D);
            System.Diagnostics.Debug.Print("zoom: " + cam.Position.Z.ToString());
        }

        private void overlay_MouseDown(object sender, MouseButtonEventArgs e)
        {
            System.Diagnostics.Debug.Print("down");
            if (e.LeftButton != MouseButtonState.Pressed) return;

            mDown = true;
            Point pos = Mouse.GetPosition(viewport);
            mLastPos = new Point(
                    pos.X - viewport.ActualWidth / 2,
                    viewport.ActualHeight / 2 - pos.Y);
        }

        private void cbxAnimations_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (cbxAnimations.SelectedIndex < 0) return;

            if (timer.IsEnabled) timer.Stop();
            animIdx = cbxAnimations.SelectedIndex;
            idx = 0;
            timer.Start();

            //System.Diagnostics.Debug.Print(db.animations[idx].meshes.Count.ToString());
        }

    }
}
