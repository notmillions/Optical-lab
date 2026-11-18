import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";

import type { PreviewLayer, SourceType } from "./lib/scene";

type MaterialStyle = { color: string; metalness: number; opacity: number };

function materialStyle(material: PreviewLayer["material"]): MaterialStyle {
  if (material === "SiO₂" || material === "SiO2") {
    return { color: "#78cbe0", metalness: 0.12, opacity: 0.72 };
  }
  if (material === "Cu") {
    return { color: "#c9764b", metalness: 0.75, opacity: 0.96 };
  }
  if (material === "Al") {
    return { color: "#b9c3c9", metalness: 0.75, opacity: 0.96 };
  }
  // Unknown catalog materials get a neutral presentation style; this is not optical data.
  return { color: "#8ea6aa", metalness: 0.35, opacity: 0.9 };
}

type PowerPreview = { reflectance: number; transmittance: number } | null;

function LayerStack({
  layers,
  source,
  response,
}: {
  layers: PreviewLayer[];
  source: SourceType;
  response: PowerPreview;
}) {
  // Finite layer thickness changes the illustration; the final substrate is semi-infinite.
  const heights = layers.map((layer, index) => index === layers.length - 1
    ? 0.38
    : Math.min(0.7, Math.max(0.12, layer.thicknessNm / 400)));
  const total = heights.reduce((sum, height) => sum + height, 0);
  let used = 0;
  const positions = heights.map((height) => {
    const y = total / 2 - used - height / 2;
    used += height;
    return y;
  });
  const topSurface = total / 2;
  const rayColor = source === "laser" ? "#b9ec67"
    : source === "solar" ? "#f7cb79" : "#ffe4b8";

  return (
    <group rotation={[0.04, -0.48, 0]}>
      {layers.map((layer, index) => {
        const style = materialStyle(layer.material);
        return (
        <mesh key={layer.id} position={[0, positions[index], 0]}>
          <boxGeometry args={[3.8, heights[index], 2.4]} />
          <meshPhysicalMaterial
            color={style.color}
            metalness={style.metalness}
            roughness={0.25}
            transparent
            opacity={style.opacity}
          />
        </mesh>
        );
      })}
      <mesh position={[-0.75, topSurface + 0.75, 0.2]} rotation={[0, 0, -0.22]}>
        <cylinderGeometry args={[0.025, 0.025, 1.4, 12]} />
        <meshBasicMaterial color={rayColor} transparent opacity={0.8} />
      </mesh>
      {response && (
        <>
          {/* These indicators encode computed fractions by opacity only.
              They are NOT geometrical ray tracing or modeled angular paths. */}
          <mesh position={[0.4, topSurface + 0.6, 0.2]} rotation={[0, 0, -0.65]}>
            <cylinderGeometry args={[0.025, 0.025, 1.3, 12]} />
            <meshBasicMaterial
              color="#ecb47f"
              transparent opacity={Math.max(0.08, response.reflectance)}
            />
          </mesh>
          <mesh position={[0, total / 2 - 0.25, 0.1]} rotation={[0, 0, 0.05]}>
            <cylinderGeometry args={[0.025, 0.025, 0.45, 12]} />
            <meshBasicMaterial
              color="#82b9f2"
              transparent opacity={Math.max(0.08, response.transmittance)}
            />
          </mesh>
        </>
      )}
      <gridHelper args={[8, 16, "#3f5054", "#25353c"]} position={[0, -2, 0]} />
    </group>
  );
}

export default function StudioScene({
  layers,
  source,
  response,
}: {
  layers: PreviewLayer[];
  source: SourceType;
  response?: PowerPreview;
}) {
  return (
    <Canvas
      camera={{ position: [5, 3.8, 6.5], fov: 45 }}
      gl={{ antialias: true, alpha: true }}
      dpr={[1, 1.75]}
      aria-label="Coupe 3D illustrative de l'empilement optique"
    >
      <ambientLight intensity={1.1} />
      <directionalLight position={[3, 8, 6]} intensity={2.0} />
      <LayerStack layers={layers} source={source} response={response ?? null} />
      <OrbitControls
        enablePan={false}
        enableDamping
        minDistance={4}
        maxDistance={15}
        maxPolarAngle={Math.PI * 0.85}
      />
    </Canvas>
  );
}
