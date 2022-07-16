import struct
from dataclasses import dataclass
from typing import List, Dict, Tuple

# FIXME: Surely theres a nice python library already for this
class Deserializer:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def advance(self, count: int):
        self.offset += count

    def read_u8(self):
        value = struct.unpack_from('B', self.data, self.offset)[0]
        self.advance(struct.calcsize('B'))
        return value

    def read_u16(self) -> int:
        value = struct.unpack_from('h', self.data, self.offset)[0]
        self.advance(struct.calcsize('h'))
        return value

    def read_u32(self) -> int:
        value = struct.unpack_from('l', self.data, self.offset)[0]
        self.advance(struct.calcsize('l'))
        return value

    def read_string(self) -> str:
        length = self.read_u32() 
        string = struct.unpack_from(f'{length}s', self.data, self.offset)[0]
        self.advance(length)
        return string

    def read_f32(self) -> float:
        value = struct.unpack_from('f', self.data, self.offset)[0]
        self.advance(struct.calcsize('f'))
        return value

    def read_vec3(self) -> (float, float, float):
        x = self.read_f32()
        y = self.read_f32()
        z = self.read_f32()
        return (x, y, z)

@dataclass
class MeshLink:
    material: int
    unknown: int
    triangles: int
    texture_coordinates: int
    points: int
    brighness: int

@dataclass
class Mesh:
    links: List[MeshLink]

@dataclass
class Material:
    name: str
    path: str
    _unknown: int = 0

@dataclass
class Animation:
    name: str
    meshes: List[int]

@dataclass
class Model:
    db_version: str
    name: str
    materials: List[Material]
    meshes: List[Mesh]
    objects: Dict[str, int]
    animations: List[Animation]
    triangle_data: List[List[int]]
    texture_coordinates_data: List[List[Tuple[float, float]]]
    points_data: List[List[Tuple[float, float, float]]]
    brightness_data: List[List[int]]

    
def parse_3db_file(raw_data):

    deserializer = Deserializer(raw_data)

    # Read DB version
    db_version = deserializer.read_string()

    # Read name
    name = deserializer.read_string()

    # Read material count
    material_count = deserializer.read_u16()

    # Read materials
    materials = []
    for _ in range(material_count):
        material_name = deserializer.read_string()
        material_path = deserializer.read_string()
        material_unknown = deserializer.read_u32()

        material = Material(material_name, material_path, material_unknown)
        materials.append(material)

    # Read mesh count
    mesh_count = deserializer.read_u32()

    # Read meshes
    meshes = []
    for _ in range(mesh_count):
        mesh_link_count = deserializer.read_u16()

        # Read mesh links
        mesh_links = []
        for _ in range(mesh_link_count):
            link_material = deserializer.read_u16()
            link_unknown = deserializer.read_u16()
            link_triangles = deserializer.read_u16()
            link_texture_coordinates = deserializer.read_u16()
            link_points = deserializer.read_u16()
            link_brightness = deserializer.read_u16()

            link = MeshLink(link_material, link_unknown, link_triangles,
                            link_texture_coordinates, link_points,
                            link_brightness)

            mesh_links.append(link)

        unknown1 = deserializer.read_vec3()
        unknown2 = deserializer.read_vec3()
        deserializer.advance(0x80)
        deserializer.advance(2)
        deserializer.advance(0x30)
        deserializer.advance(2)

        mesh = Mesh(mesh_links)
        meshes.append(mesh)

    # Read object data
    key_value_pair_count = deserializer.read_u16()
    objects = {}
    for _ in range(key_value_pair_count):
        key = deserializer.read_string()
        object_count = deserializer.read_u16()
        objects[key] = []
        for _ in range(object_count):
            objects[key].append(deserializer.read_u32())

    # Read animation data
    animations = []
    animation_count = deserializer.read_u16()
    for _ in range(animation_count):
        animation_name = deserializer.read_string()

        some_count = deserializer.read_u16()
        mesh_indices = []
        for _ in range(some_count):
            mesh_indices.append(deserializer.read_u32())

        # Read and ignore unknown values
        deserializer.read_u16()
        deserializer.read_f32()
        deserializer.read_string()
        deserializer.read_vec3()
        deserializer.read_vec3()

        animation = Animation(animation_name, mesh_indices)
        animations.append(animation)

    # Skip shadows
    shadow_count = deserializer.read_u16()
    for _ in range(shadow_count):
        deserializer.advance(32 * 32)

    # Read Cube maps?
    cube_map_count = deserializer.read_u16()
    for _ in range(cube_map_count):
        width = deserializer.read_u16()
        height = deserializer.read_u16()
        deserializer.read_u16()
        deserializer.read_u16()
        # Skip pixel data
        deserializer.advance(width * height)

    # Read triangles
    triangle_count = deserializer.read_u16()

    # Read texture coordinates?
    texture_coordinate_count = deserializer.read_u16()

    # Read points
    point_count = deserializer.read_u16()

    # Read brightness
    brightness_count = deserializer.read_u16()

    unknown_count = deserializer.read_u32()

    # Read triangle counts
    triangle_counts = []
    for _ in range(triangle_count):
        count = deserializer.read_u16()
        triangle_counts.append(count)

    texture_coordinate_counts = []
    for _ in range(texture_coordinate_count):
        texture_coordinate_counts.append(deserializer.read_u16())

    point_counts = []
    for _ in range(point_count):
        point_counts.append(deserializer.read_u16())

    brightness_counts = []
    for _ in range(brightness_count):
        brightness_counts.append(deserializer.read_u16())

    for _ in range(unknown_count):
        deserializer.advance(20)

    # Read actual triangle data
    triangle_data = []
    for i in range(triangle_count):
        count = triangle_counts[i]
        triangles = []
        for _ in range(count):
            triangles.append(deserializer.read_u16())
        triangle_data.append(triangles)

    # Read texture coordinates data
    texture_coordinates_data = []
    for i in range(texture_coordinate_count):
        count = texture_coordinate_counts[i]
        texture_coordinates = []
        for _ in range(count):
            u = deserializer.read_f32()
            v = deserializer.read_f32()
            texture_coordinates.append((u, v))
        texture_coordinates_data.append(texture_coordinates)

    # Read points data
    points_data = []
    for i in range(point_count):
        count = point_counts[i]
        points = []
        for _ in range(count):
            x = deserializer.read_u16() / float(0xffff)
            y = deserializer.read_u16() / float(0xffff)
            z = deserializer.read_u16() / float(0xffff)
            points.append((x, y, z))
        points_data.append(points)

    # TODO: Read brightness data
    brightness_data = []
    for i in range(brightness_count):
        count = brightness_counts[i]
        brightness = []
        for _ in range(count):
            brightness.append(deserializer.read_u8())
        brightness_data.append(brightness)


    result = Model(db_version, name, materials, meshes, objects, animations,
            triangle_data, texture_coordinates_data, points_data, brightness_data)
    return result

