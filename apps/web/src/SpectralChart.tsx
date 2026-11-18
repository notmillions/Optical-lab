import type { SimulationPoint } from "./lib/api";

const COLORS = {
  reflectance: "#c2e78c",
  transmittance: "#83b6ee",
  absorptance: "#e6a37b"
};

function linePath(points: SimulationPoint[], key: "reflectance" | "transmittance" | "absorptance") {
  if (points.length < 2) return "";
  const left = points[0].wavelength_nm;
  const width = points[points.length - 1].wavelength_nm - left;
  if (width <= 0) return "";
  return points.map((point, index) => {
    const x = 20 + (point.wavelength_nm - left) / width * 280;
    const y = 112 - Math.max(0, Math.min(1, point[key])) * 94;
    return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
  }).join(" ");
}

export default function SpectralChart({ points }: { points: SimulationPoint[] }) {
  if (points.length === 0) {
    return <div className="chart-grid"><span>En attente de simulation</span></div>;
  }
  if (points.length === 1) {
    return (
      <div className="chart-grid">
        <span>Laser monochromatique · {points[0].wavelength_nm.toFixed(1)} nm</span>
      </div>
    );
  }
  return (
    <div className="scientific-chart">
      <svg
        role="img"
        aria-label="Courbes de réflectance, transmittance et absorptance calculées par TMM"
        viewBox="0 0 320 137"
        preserveAspectRatio="none"
      >
        {[0, 0.25, 0.5, 0.75, 1].map((value) => (
          <line key={value} x1="20" x2="300" y1={112 - value * 94}
            y2={112 - value * 94} stroke="#354a4e" strokeWidth="0.65" />
        ))}
        {(["reflectance", "transmittance", "absorptance"] as const).map((key) => (
          <path key={key} d={linePath(points, key)} fill="none"
            stroke={COLORS[key]} strokeWidth="2" />
        ))}
        <text x="3" y="20" fill="#93a9ac" fontSize="9">1</text>
        <text x="3" y="114" fill="#93a9ac" fontSize="9">0</text>
        <text x="20" y="129" fill="#93a9ac" fontSize="8">
          {Math.round(points[0].wavelength_nm)} nm
        </text>
        <text x="300" y="129" textAnchor="end" fill="#93a9ac" fontSize="8">
          {Math.round(points[points.length - 1].wavelength_nm)} nm
        </text>
      </svg>
      <div className="chart-legend">
        <span className="legend-r">R</span><span className="legend-t">T</span><span className="legend-a">A</span>
      </div>
    </div>
  );
}
