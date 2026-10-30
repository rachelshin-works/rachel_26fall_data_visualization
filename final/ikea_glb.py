"""Shared GLB reading/writing for the IKEA model scripts.

- read_glb(path)  -> Model: the node tree with decoded geometry (Draco or plain), materials kept as-is.
- write_glb(path, model) -> writes an uncompressed GLB (no Draco), same materials/textures.

Only what IKEA web models use is supported: triangle meshes, POSITION/NORMAL/TANGENT/TEXCOORD_n
attributes, node translation/rotation/scale or matrix. Requires: numpy, pygltflib, DracoPy.
"""
from __future__ import annotations

import copy
import struct
from dataclasses import dataclass, field

import numpy as np
from pygltflib import GLTF2, Accessor, Asset, Buffer, BufferView, Mesh, Node, Primitive, Scene, Attributes

DRACO = "KHR_draco_mesh_compression"
COMPONENT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
TYPE_OF = {1: "SCALAR", 2: "VEC2", 3: "VEC3", 4: "VEC4"}


@dataclass
class Prim:
    attributes: dict[str, np.ndarray]      # name -> (n, k) float32
    indices: np.ndarray                    # (m, 3) uint32 triangles
    material: int | None = None


@dataclass
class TreeNode:
    name: str
    translation: list[float] | None = None
    rotation: list[float] | None = None
    scale: list[float] | None = None
    matrix: list[float] | None = None
    extras: dict = field(default_factory=dict)
    prims: list[Prim] = field(default_factory=list)
    children: list["TreeNode"] = field(default_factory=list)

    def local_matrix(self) -> np.ndarray:
        if self.matrix:
            return np.array(self.matrix, dtype=float).reshape(4, 4).T
        t = np.array(self.translation or [0, 0, 0], float)
        x, y, z, w = self.rotation or [0, 0, 0, 1]
        r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        s = np.array(self.scale or [1, 1, 1], float)
        m = np.eye(4); m[:3, :3] = r * s; m[:3, 3] = t
        return m

    def walk(self, parent=np.eye(4)):
        """Yield (node, world_matrix) for this node and all descendants."""
        world = parent @ self.local_matrix()
        yield self, world
        for c in self.children:
            yield from c.walk(world)


@dataclass
class Model:
    roots: list[TreeNode]
    gltf: GLTF2           # source document (materials, textures, images live here)
    blob: bytes

    def mesh_nodes(self):
        for r in self.roots:
            for n, w in r.walk():
                if n.prims:
                    yield n, w

    def world_points(self, node_filter=None) -> np.ndarray:
        pts = [apply(w, p.attributes["POSITION"]) for n, w in self.mesh_nodes()
               if node_filter is None or node_filter(n) for p in n.prims]
        return np.concatenate(pts) if pts else np.zeros((0, 3))


def apply(m: np.ndarray, pts: np.ndarray) -> np.ndarray:
    return pts @ m[:3, :3].T + m[:3, 3]


# ---------------------------------------------------------------------------- read
def _read_accessor(g: GLTF2, blob: bytes, idx: int) -> np.ndarray:
    a = g.accessors[idx]
    bv = g.bufferViews[a.bufferView]
    dt = np.dtype(COMPONENT[a.componentType])
    k = NCOMP[a.type]
    start = (bv.byteOffset or 0) + (a.byteOffset or 0)
    stride = bv.byteStride or dt.itemsize * k
    if stride == dt.itemsize * k:
        arr = np.frombuffer(blob, dt, a.count * k, start).reshape(a.count, k)
    else:
        raw = np.frombuffer(blob, np.uint8, stride * (a.count - 1) + dt.itemsize * k, start)
        arr = np.stack([np.frombuffer(raw[i * stride:i * stride + dt.itemsize * k].tobytes(), dt) for i in range(a.count)])
    return arr.copy()


def _decode_prim(g: GLTF2, blob: bytes, p: Primitive) -> Prim:
    ext = (p.extensions or {}).get(DRACO)
    if ext:
        import DracoPy
        bv = g.bufferViews[ext["bufferView"]]
        off = bv.byteOffset or 0
        mesh = DracoPy.decode(blob[off:off + bv.byteLength])
        attrs = {}
        for name, uid in ext["attributes"].items():
            a = mesh.get_attribute_by_unique_id(uid)
            if a is not None:
                attrs[name] = np.asarray(a["data"], np.float32).reshape(-1, a["num_components"])
        idx = np.asarray(mesh.faces, np.uint32).reshape(-1, 3)
    else:
        attrs = {name: _read_accessor(g, blob, i).astype(np.float32)
                 for name, i in p.attributes.__dict__.items() if i is not None}
        idx = (_read_accessor(g, blob, p.indices).reshape(-1, 3).astype(np.uint32) if p.indices is not None
               else np.arange(len(attrs["POSITION"]), dtype=np.uint32).reshape(-1, 3))
    return Prim(attrs, idx, p.material)


def read_glb(path: str) -> Model:
    g = GLTF2().load(path)
    blob = g.binary_blob() or b""

    def build(i: int) -> TreeNode:
        n = g.nodes[i]
        t = TreeNode(n.name or f"node_{i}", n.translation, n.rotation, n.scale, n.matrix, dict(n.extras or {}))
        if n.mesh is not None:
            t.prims = [_decode_prim(g, blob, p) for p in g.meshes[n.mesh].primitives]
        t.children = [build(c) for c in (n.children or [])]
        return t

    scene = g.scenes[g.scene or 0]
    return Model([build(i) for i in scene.nodes], g, blob)


# ---------------------------------------------------------------------------- write
def write_glb(path: str, model: Model, roots: list[TreeNode] | None = None) -> None:
    src, sblob = model.gltf, model.blob
    roots = roots if roots is not None else model.roots
    out = GLTF2(asset=Asset(version="2.0", generator="ikea-glb-tools"))
    data = bytearray()

    def add_view(raw: bytes, target: int | None = None) -> int:
        while len(data) % 4:
            data.append(0)
        out.bufferViews.append(BufferView(buffer=0, byteOffset=len(data), byteLength=len(raw), target=target))
        data.extend(raw)
        return len(out.bufferViews) - 1

    def add_accessor(arr: np.ndarray, is_index=False, minmax=False) -> int:
        arr = np.ascontiguousarray(arr.astype(np.uint32 if is_index else np.float32))
        view = add_view(arr.tobytes(), 34963 if is_index else 34962)
        k = 1 if is_index else arr.shape[1]
        acc = Accessor(bufferView=view, componentType=5125 if is_index else 5126,
                       count=arr.size if is_index else len(arr), type="SCALAR" if is_index else TYPE_OF[k])
        if minmax:
            acc.min = arr.min(0).tolist(); acc.max = arr.max(0).tolist()
        out.accessors.append(acc)
        return len(out.accessors) - 1

    # copy images (re-pack their bytes), then textures/samplers/materials unchanged (indices preserved)
    for im in src.images or []:
        im2 = copy.deepcopy(im)
        if im.bufferView is not None:
            bv = src.bufferViews[im.bufferView]
            o = bv.byteOffset or 0
            im2.bufferView = add_view(sblob[o:o + bv.byteLength])
        out.images.append(im2)
    out.samplers = copy.deepcopy(src.samplers or [])
    out.textures = copy.deepcopy(src.textures or [])
    out.materials = copy.deepcopy(src.materials or [])
    used = [e for e in (src.extensionsUsed or []) if e != DRACO]
    out.extensionsUsed = used
    out.extensionsRequired = [e for e in (src.extensionsRequired or []) if e != DRACO]

    def emit(t: TreeNode) -> int:
        n = Node(name=t.name, translation=t.translation, rotation=t.rotation, scale=t.scale,
                 matrix=t.matrix, extras=t.extras or {})
        if t.prims:
            prims = []
            for p in t.prims:
                attrs = Attributes()
                for name, arr in p.attributes.items():
                    setattr(attrs, name, add_accessor(arr, minmax=(name == "POSITION")))
                prims.append(Primitive(attributes=attrs, indices=add_accessor(p.indices, is_index=True), material=p.material))
            out.meshes.append(Mesh(name=t.name, primitives=prims))
            n.mesh = len(out.meshes) - 1
        out.nodes.append(n)
        me = len(out.nodes) - 1
        n.children = [emit(c) for c in t.children] or None
        return me

    out.scenes = [Scene(nodes=[emit(r) for r in roots])]
    out.scene = 0
    while len(data) % 4:
        data.append(0)
    out.buffers = [Buffer(byteLength=len(data))]
    out.set_binary_blob(bytes(data))
    out.save_binary(path)
