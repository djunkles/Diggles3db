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
    nodes = []
    meshes = []
    accessors = []

    vertex_byte_array = bytearray()
    index_byte_array = bytearray()

    mesh = model.meshes[0]
    for mesh_link in mesh.links:
        triangles = model.triangle_data[mesh_link.triangles]
        points = model.points_data[mesh_link.points]
        texture_coordinates = model.texture_coordinates_data[mesh_link.texture_coordinates]
        vertices = [transform_point(p) for p in points]

        vertex_data_start = len(vertex_byte_array);
        for vertex in vertices:
            for value in vertex:
                vertex_byte_array.extend(struct.pack('f', value))

        mins = [min([operator.itemgetter(i)(vertex) for vertex in vertices]) for i in range(3)]
        maxs = [max([operator.itemgetter(i)(vertex) for vertex in vertices]) for i in range(3)]

        texture_coords_start = len(vertex_byte_array)
        for t in texture_coordinates:
            for value in t:
                vertex_byte_array.extend(struct.pack('f', value))

        indices_start = len(index_byte_array)
        for index in triangles:
            index_byte_array.extend(struct.pack('I', index))

        position_index = len(accessors)
        accessors.append(Accessor(bufferView=0, byteOffset=vertex_data_start, componentType=ComponentType.FLOAT.value, count=len(vertices),
                            type=AccessorType.VEC3.value, min=mins, max=maxs))

        texture_coords_index = len(accessors)
        accessors.append(Accessor(bufferView=0, byteOffset=texture_coords_start, componentType=ComponentType.FLOAT.value, count=len(texture_coordinates),
                            type=AccessorType.VEC2.value))

        indices_index = len(accessors)
        accessors.append(Accessor(bufferView=1, byteOffset=indices_start, componentType=ComponentType.UNSIGNED_INT.value, count=len(triangles),
                            type=AccessorType.SCALAR.value))

        mesh_index = len(meshes)
        meshes.append(Mesh(primitives=[Primitive(attributes=Attributes(POSITION=position_index, TEXCOORD_0=texture_coords_index), indices=indices_index)]))
        nodes.append(Node(mesh=mesh_index))

    model = GLTFModel(
        asset=Asset(version='2.0'),
        scenes=[Scene(nodes=[x for x in range(len(nodes))])],
        nodes=nodes,
        buffers=[Buffer(byteLength=len(vertex_byte_array), uri='vertices.bin'), Buffer(byteLength=len(index_byte_array), uri='indices.bin')],
        bufferViews=[BufferView(buffer=0, byteOffset=0, byteLength=len(vertex_byte_array), target=BufferTarget.ARRAY_BUFFER.value),
                     BufferView(buffer=1, byteOffset=0, byteLength=len(index_byte_array), target=BufferTarget.ELEMENT_ARRAY_BUFFER.value)],
        accessors=accessors,
        meshes=meshes
    )

    gltf = GLTF(model=model, resources=[FileResource('vertices.bin', data=vertex_byte_array),
                                        FileResource('indices.bin', data=index_byte_array)])
    gltf.export('out.gltf')
    print('Wrote to out.gltf, vertices.bin and indices.bin files')
