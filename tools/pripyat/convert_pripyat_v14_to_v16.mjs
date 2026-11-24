import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const [sourceRootArg, outputRootArg] = process.argv.slice(2);
if (!sourceRootArg || !outputRootArg) {
  console.error('Usage: node convert_pripyat_v14_to_v16.mjs <native_v14_dir> <output_scene_dir>');
  process.exit(2);
}
const sourceRoot = path.resolve(sourceRootArg);
const outputRoot = path.resolve(outputRootArg);
const sceneFile = path.join(sourceRoot, 'scene_pripyat_central.js');
const seatHelper = path.join(sourceRoot, 'assets/pripyat/energetik_cinema_seat.js');
const objects = [];
const emit = (type, args) => objects.push({ type, args });
const api = {
  objects,
  box: (...args) => emit('box', args),
  roundBox: (...args) => emit('roundBox', args),
  capsule: (...args) => emit('capsule', args),
  ellipse: (...args) => emit('ellipse', args),
  ellipsoidMesh: (...args) => emit('ellipsoid', args),
};
const context = {
  objects, console, Math,
  box: api.box, roundBox: api.roundBox, capsule: api.capsule,
  ellipse: api.ellipse, ellipsoidMesh: api.ellipsoidMesh,
  buildEnergetikCinemaSeat: (await import(`file://${seatHelper}`)).default,
};
vm.createContext(context);
const source = fs.readFileSync(sceneFile, 'utf8');
vm.runInContext(source + '\nmakeScene(); globalThis.__sceneLights = M3D_SCENE_LIGHTS.slice();', context, { timeout: 120000 });

const materials = new Map();
const boxInstances = [];
const triangleMeshes = new Map();
const maxFaces = 60000;
const maxVertices = 180000;

function bucket(material) {
  if (!triangleMeshes.has(material)) triangleMeshes.set(material, []);
  let chunks = triangleMeshes.get(material);
  let chunk = chunks[chunks.length - 1];
  if (!chunk || chunk.faces.length >= maxFaces) {
    chunk = { vertices: [], uv: [], faces: [] };
    chunks.push(chunk);
  }
  return chunk;
}
function addTriangles(material, vertices, uv, faces) {
  materials.set(material, material);
  let chunk = bucket(material);
  if (chunk.vertices.length + vertices.length > maxVertices || chunk.faces.length + faces.length > maxFaces) {
    triangleMeshes.get(material).push(chunk = { vertices: [], uv: [], faces: [] });
  }
  const offset = chunk.vertices.length;
  chunk.vertices.push(...vertices);
  chunk.uv.push(...uv);
  for (const face of faces) chunk.faces.push(face.map(i => i + offset));
}

function ellipsoidTriangles(cx, cy, cz, rx, ry, rz, material) {
  const maxR = Math.max(rx, ry, rz);
  const segments = maxR > 0.7 ? 12 : (maxR > 0.12 ? 8 : 6);
  const rings = maxR > 0.7 ? 8 : (maxR > 0.12 ? 6 : 4);
  const vertices = [], uv = [], faces = [];
  for (let i = 0; i <= rings; i++) {
    const theta = Math.PI * i / rings;
    for (let j = 0; j <= segments; j++) {
      const phi = 2 * Math.PI * j / segments;
      const sn = Math.sin(theta);
      vertices.push([cx + rx * sn * Math.cos(phi), cy + ry * Math.cos(theta), cz + rz * sn * Math.sin(phi)]);
      uv.push([j / segments, i / rings]);
    }
  }
  for (let i = 0; i < rings; i++) for (let j = 0; j < segments; j++) {
    const a = i * (segments + 1) + j;
    const b = a + segments + 1;
    const c = b + 1;
    const d = a + 1;
    if (i > 0) faces.push([a, d, b]);
    if (i < rings - 1) faces.push([d, c, b]);
  }
  addTriangles(material, vertices, uv, faces);
}

function capsuleTriangles(a, b, radius, material) {
  const dx = b[0] - a[0], dy = b[1] - a[1], dz = b[2] - a[2];
  const len = Math.hypot(dx, dy, dz);
  if (!(len > 1e-6) || !(radius > 0)) {
    ellipsoidTriangles(a[0], a[1], a[2], radius, radius, radius, material);
    return;
  }
  const axis = [dx / len, dy / len, dz / len];
  const ref = Math.abs(axis[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
  const cross = (u, v) => [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
  const norm = v => { const n = Math.hypot(...v) || 1; return v.map(x => x / n); };
  const u = norm(cross(axis, ref));
  const v = norm(cross(axis, u));
  const sides = 8;
  const vertices = [], uv = [], faces = [];
  const rings = [
    [-radius, 0], [-radius * 0.5, radius * Math.sqrt(3) / 2],
    [0, radius], [len, radius],
    [len + radius * 0.5, radius * Math.sqrt(3) / 2], [len + radius, 0],
  ];
  const pointAt = (along, r, j) => {
    const angle = 2 * Math.PI * j / sides;
    const center = [a[0] + axis[0] * along, a[1] + axis[1] * along, a[2] + axis[2] * along];
    return center.map((p, k) => p + r * (u[k] * Math.cos(angle) + v[k] * Math.sin(angle)));
  };
  for (let ri = 0; ri < rings.length; ri++) {
    for (let j = 0; j < sides; j++) {
      vertices.push(pointAt(rings[ri][0], rings[ri][1], j));
      uv.push([j / sides, ri / (rings.length - 1)]);
    }
  }
  for (let ri = 0; ri < rings.length - 1; ri++) for (let j = 0; j < sides; j++) {
    const a0 = ri * sides + j, a1 = ri * sides + (j + 1) % sides;
    const b0 = (ri + 1) * sides + j, b1 = (ri + 1) * sides + (j + 1) % sides;
    faces.push([a0, a1, b0], [a1, b1, b0]);
  }
  addTriangles(material, vertices, uv, faces);
}

for (const [index, item] of objects.entries()) {
  const a = item.args;
  if (item.type === 'box' || item.type === 'roundBox') {
    const [x0, y0, z0, x1, y1, z1] = a;
    const mat = a[item.type === 'box' ? 6 : 7];
    materials.set(mat, mat);
    boxInstances.push({
      id: `block_${index}`, parent: 'Pripiat/Geometry', geometry: 'unit_box', material: mat,
      position: [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2],
      size: [Math.max(.001, x1 - x0), Math.max(.001, y1 - y0), Math.max(.001, z1 - z0)], rotationY: 0,
    });
  } else if (item.type === 'ellipse' || item.type === 'ellipsoid') {
    const [cx, cy, cz, rx, ry, rz, mat] = a;
    ellipsoidTriangles(cx, cy, cz, Math.max(.001, rx), Math.max(.001, ry), Math.max(.001, rz), mat);
  } else if (item.type === 'capsule') {
    const [p0, p1, r, mat] = a;
    capsuleTriangles(p0, p1, r, mat);
  } else {
    throw new Error(`Unsupported V14 primitive ${item.type}`);
  }
}

const out = p => path.join(outputRoot, p);
fs.mkdirSync(outputRoot, { recursive: true });
for (const p of ['geometry', 'instances', 'materials', 'pbr', 'lighting', 'cameras']) fs.mkdirSync(out(p), { recursive: true });
const geometryMeshes = [{ id: 'unit_box', type: 'box', size: [1, 1, 1], uv: 'planar_per_face' }];
const meshInstances = [];
for (const [material, chunks] of [...triangleMeshes.entries()].sort(([a], [b]) => a.localeCompare(b))) {
  for (let i = 0; i < chunks.length; i++) {
    const id = `tri_${material}_${String(i + 1).padStart(2, '0')}`;
    const chunk = chunks[i];
    geometryMeshes.push({ id, type: 'triangle_mesh', vertices: chunk.vertices, uv: chunk.uv, faces: chunk.faces });
    meshInstances.push({ id: `mesh_${id}`, parent: 'Pripiat/Geometry', geometry: id, material,
      position: [0, 0, 0], size: [1, 1, 1], rotationY: 0 });
  }
}
fs.writeFileSync(out('geometry/pripyat.json'), JSON.stringify({ format: 'm3d-geometry-v1', units: 'm', meshes: geometryMeshes }));
fs.writeFileSync(out('instances/pripyat.json'), JSON.stringify({ format: 'm3d-instances-v1',
  instances: [...boxInstances, ...meshInstances] }));

const color = {
  asphalt: ['#353430', .94, 0, 'concrete'], concrete: ['#73716a', .88, 0, 'concrete'], stone: ['#827b70', .84, 0, 'stone'],
  glass: ['#33474b', .13, .03, 'glass'], brick: ['#704d3e', .88, 0, 'brick'], rust: ['#75452f', .84, .04, 'metal'],
  plaster: ['#827b6d', .9, 0, 'plaster'], metal: ['#555650', .42, .62, 'metal'], windowdark: ['#111719', .48, .05, 'metal'],
  debris: ['#686359', .93, 0, 'stone'], volcanicTuff: ['#766a58', .89, 0, 'stone'], wood: ['#574433', .7, 0, 'wood'],
  cinemaScreen: ['#201b1b', .28, 0, 'smooth_plaster'], curtain: ['#403039', .93, 0, 'fabric'], seatFabric: ['#553d39', .93, 0, 'fabric'],
  seatSteel: ['#383c3b', .48, .48, 'metal'], seatVinylBrown: ['#49372e', .8, 0, 'fabric'], seatSupportPaint: ['#53615a', .68, .08, 'metal'],
  seatWood: ['#533e2f', .77, 0, 'wood'], lamp: ['#e9c474', .35, .08, 'metal'], mural: ['#8c7656', .82, 0, 'plaster'],
  sea: ['#46595a', .31, .08, 'water'], sportsViolet: ['#745679', .58, .02, 'plaster'], sportsPaint: ['#777058', .7, .02, 'plaster'],
  sportsRed: ['#8a3027', .58, .02, 'brick'], taxi: ['#c7a63e', .55, .01, 'metal'], windowlit: ['#c2ac7a', .3, .01, 'glass'],
  grass: ['#555343', .95, 0, 'foliage'], bark: ['#4e4034', .94, 0, 'wood'], leaves: ['#48513a', .92, 0, 'foliage'], puddle: ['#373c3b', .14, .12, 'water'],
};
const rgb = hex => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255);
const matDefs = [...materials.keys()].sort().map(id => {
  const [hex, roughness, metallic, pattern] = color[id] || ['#77716a', .82, 0, 'stone'];
  const transmission = id === 'glass' ? .62 : 0;
  return { id, baseColor: rgb(hex), roughness, metallic, transmission, ior: id === 'glass' ? 1.48 : 1.5, textureSet: `tex_${id}` };
});
fs.writeFileSync(out('materials/pripyat.json'), JSON.stringify({ format: 'm3d-materials-v1', materials: matDefs }));
fs.writeFileSync(out('pbr/pripyat.json'), JSON.stringify({ format: 'm3d-pbr-v1', mipmaps: 'auto', sets: [...materials.keys()].sort().map(id => ({
  id: `tex_${id}`, material: id, pattern: (color[id] || [,,, 'stone'])[3], resolution: 256,
})) }));
const lights = (context.__sceneLights || []).map(([x, y, z, radius, intensity, r, g, b], i) => ({
  id: `energetik_light_${String(i + 1).padStart(2, '0')}`, position: [x, y, z], radius, intensity,
  color: [r, g, b], group: 'interior',
}));
fs.writeFileSync(out('lighting/day.json'), JSON.stringify({ format: 'm3d-lighting-v1', hour: 9,
  sun: { direction: [-.68, .65, -.35], intensity: 2.5 },
  ambient: { color: [.61, .70, .84], intensity: .34 }, lights,
}));
const sourceViews = JSON.parse(fs.readFileSync(path.join(sourceRoot, 'scene_pripyat_views.json'), 'utf8'));
const cameras = sourceViews.views.map((v, i) => {
  const [x, y, z] = v.target;
  const angle = v.angle * Math.PI / 180, elevation = v.elevation * Math.PI / 180, d = v.distance;
  const ce = Math.cos(elevation);
  return { id: `view_${String(i + 1).padStart(2, '0')}`, name: v.name,
    position: [x + d * Math.sin(angle) * ce, y + d * Math.sin(elevation), z + d * Math.cos(angle) * ce],
    target: [x, y, z], fovDegrees: v.fov };
});
fs.writeFileSync(out('cameras/views.json'), JSON.stringify({ format: 'm3d-cameras-v1', cameras }));
fs.writeFileSync(out('scene.json'), JSON.stringify({ format: 'm3d-scene-v16', name: 'Pripiat — place centrale, Energetik et Polissya',
  revision: 'PRIPYAT-V16-2026.11.24.1', version: 1, units: 'm', sectors: [{ id: 'pripyat-central',
    geometry: ['geometry/pripyat.json'], instances: ['instances/pripyat.json'], materials: ['materials/pripyat.json'],
    pbr: ['pbr/pripyat.json'], lighting: ['lighting/day.json'], cameras: ['cameras/views.json'], environment: [] }] }));
fs.writeFileSync(out('conversion-stats.json'), JSON.stringify({ sourcePrimitiveCount: objects.length,
  boxInstances: boxInstances.length, triangleMeshInstances: meshInstances.length,
  triangleMeshCount: geometryMeshes.length - 1,
  triangleFaces: geometryMeshes.slice(1).reduce((n, m) => n + m.faces.length, 0) + boxInstances.length * 12,
  materials: matDefs.length, lights: lights.length, cameras: cameras.length,
}, null, 2));
console.log(fs.readFileSync(out('conversion-stats.json'), 'utf8'));
