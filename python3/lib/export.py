import struct
import operator
from gltflib import (
    GLTF, GLTFModel, Asset, Scene, Node, Mesh, Primitive, Attributes, Buffer, BufferView, Accessor, AccessorType,
    BufferTarget, ComponentType, GLBResource, FileResource)

from lib.parse_3db import Model
from typing import List, Dict, Tuple

def transform_point(p: Tuple[float, float, float]):
    scale = 100
    result = ((p[0] - 0.5) * scale, (p[1] -0.5) * scale, (p[2] - 0.5) * scale)
    return result

def build_vertices_array(triangles: List[int], points: List[Tuple[float, float, float]]):
    vertices = [points[index] for index in triangles]
    return vertices

def export_to_gltf(model: Model):
    mesh = model.meshes[0]
    mesh_link = mesh.links[0]
    triangles = model.triangle_data[mesh_link.triangles]
    points = model.points_data[mesh_link.points]
    in_texture_coordinates = model.texture_coordinates_data[mesh_link.texture_coordinates]
    transformed_points = [transform_point(p) for p in points]
    vertices = build_vertices_array(triangles, transformed_points)
    texture_coordinates = [in_texture_coordinates[index] for index in triangles]
    assert(len(vertices) % 3 == 0)
    assert(len(texture_coordinates) % 3 == 0)

    vertex_bytearray = bytearray()
    for vertex in vertices:
        for value in vertex:
            vertex_bytearray.extend(struct.pack('f', value))
    bytelen = len(vertex_bytearray)
    mins = [min([operator.itemgetter(i)(vertex) for vertex in vertices]) for i in range(3)]
    maxs = [max([operator.itemgetter(i)(vertex) for vertex in vertices]) for i in range(3)]

    for t in texture_coordinates:
        for value in t:
            vertex_bytearray.extend(struct.pack('f', value))
    texture_coords_byte_len = len(vertex_bytearray) - bytelen
    total_len = len(vertex_bytearray)

    model = GLTFModel(
        asset=Asset(version='2.0'),
        scenes=[Scene(nodes=[0])],
        nodes=[Node(mesh=0)],
        meshes=[Mesh(primitives=[Primitive(attributes=Attributes(POSITION=0, TEXCOORD_0=1))])],
        buffers=[Buffer(byteLength=total_len, uri='vertices.bin')],
        bufferViews=[BufferView(buffer=0, byteOffset=0, byteLength=total_len, target=BufferTarget.ARRAY_BUFFER.value)],
        accessors=[Accessor(bufferView=0, byteOffset=0, componentType=ComponentType.FLOAT.value, count=len(vertices),
                            type=AccessorType.VEC3.value, min=mins, max=maxs),
                   Accessor(bufferView=0, byteOffset=bytelen, componentType=ComponentType.FLOAT.value, count=len(texture_coordinates),
                            type=AccessorType.VEC2.value)]
    )

    resource = FileResource('vertices.bin', data=vertex_bytearray)
    gltf = GLTF(model=model, resources=[resource])
    gltf.export('out.gltf')
    print('Wrote to out.gltf and vertices.bin files')
