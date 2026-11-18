import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";

import type { PreviewLayer, SourceType } from "./lib/scene";

const PALETTE: Record<PreviewLayer["material"], string> = {
  "SiO₂": "#78cbe0",
  Cu: "#c9764b",
  Al: "#b9c3c9"
};

function LayerStack({ layers, source }: {
  layers: PreviewLayer[];
  source: SourceType;
}) {
  const step = 0.34;
  const top = (layers.length - 1) * step / 2;

  return (
    <group rotation={[0.04, -0.48, 0]}>
      {layers.map((layer, index) => (
        <mesh key={layer.id} position={[0, top - index * step, 0]}>
          <boxGeometry args={[3.8, 0.24, 2.4]} />
          <meshPhysicalMaterial
            color={PALETTE[layer.material]}
            metalness={layer.material === "SiO₂" ? 0.12 : 0.75}
            roughness={0.25}
            transparent
            opacity={layer.material === "SiO₂" ? 0.72 : 0.96}
          />
        </mesh>
      ))}
      {source === "laser" && (
        <mesh position={[-0.85, top + 1.45, 0.2]} rotation={[0, 0, -0.22]}>
          <cylinderGeometry args={[0.025, 0.025, 2.4, 12]} />
          <meshBasicMaterial color="#b9ec67" />
        </mesh>
      )}
      <gridHelper args={[8, 16, "#3f5054", "#25353c"]} position={[0, -2, 0]} />
    </group>
  );
}

export default function StudioScene({
  layers,
  source
}: {
  layers: PreviewLayer[];
  source: SourceType;
}) {
  return (
    <Canvas
      camera={{ position: [5, 3.8, 6.5], fov: 45 }}
      gl={{ antialias: true, alpha: true }}
      dpr={[1, 1.75]}
      aria-label="Vue illustrative des couches optiques"
    >
      <ambientLight intensity={1.1} />
      <directionalLight position={[3, 8, 6]} intensity={2.0} />
      <LayerStack layers={layers} source={source} />
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
