import { useEffect, useRef, useState } from "react";

import StudioScene from "./StudioScene";
import {
  INITIAL_LAYERS,
  SOURCE_LABEL,
  formatWavelength,
  moveLayer,
  updateLayerThickness
} from "./lib/scene";
import type { Polarization, PreviewLayer, PreviewMaterial, SourceType } from "./lib/scene";

type ApiState = "checking" | "online" | "offline";
const MATERIAL_CHOICES: PreviewMaterial[] = ["SiO₂", "Cu", "Al"];

function App() {
  const [source, setSource] = useState<SourceType>("laser");
  const [angleDeg, setAngleDeg] = useState(30);
  const [wavelengthNm, setWavelengthNm] = useState(532);
  const [polarization, setPolarization] = useState<Polarization>("s");
  const [layers, setLayers] = useState<PreviewLayer[]>(INITIAL_LAYERS);
  const [apiState, setApiState] = useState<ApiState>("checking");
  const nextLayerId = useRef(3);

  useEffect(() => {
    const abort = new AbortController();
    fetch("/api/v1/capabilities", { signal: abort.signal })
      .then((response) => {
        if (!response.ok) throw new Error("API unavailable");
        return response.json() as Promise<{ stage: string; optical_solver: boolean }>;
      })
      .then((capabilities) => {
        if (capabilities.stage === "S0" && !capabilities.optical_solver) {
          setApiState("online");
        } else {
          setApiState("online");
        }
      })
      .catch(() => {
        if (!abort.signal.aborted) setApiState("offline");
      });
    return () => abort.abort();
  }, []);

  const addLayer = () => {
    setLayers((current) => [
      ...current,
      { id: `layer-${nextLayerId.current++}`, material: "SiO₂", thicknessNm: 100 }
    ]);
  };

  const changeMaterial = (id: string, material: PreviewMaterial) =>
    setLayers((current) => current.map((layer) =>
      layer.id === id ? { ...layer, material } : layer
    ));

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">◈</span>
          <span className="brand-name">OPTICAL <strong>LAB</strong></span>
          <span className="brand-version">/ S0 LAB PREVIEW</span>
        </div>
        <nav className="top-nav" aria-label="Navigation de l'application">
          <a className="nav-active" href="#studio">Studio</a>
          <a href="#material-library">Matériaux</a>
          <a href="#status">Analyse</a>
        </nav>
        <span className={`api-status ${apiState}`} role="status">
          <span className="status-dot" />
          {apiState === "online" ? "API CONNECTÉE" :
            apiState === "checking" ? "CONNEXION..." : "API HORS LIGNE"}
        </span>
      </header>

      <div className="workbench" id="studio">
        <aside className="side-panel left-panel" aria-label="Configuration optique">
          <div className="panel-heading">
            <span className="eyebrow">01 / SETUP</span>
            <h2>Configuration</h2>
            <p>Définis une source et un empilement. Les données scientifiques seront disponibles au Sprint S1.</p>
          </div>

          <section className="control-section">
            <div className="section-line"><h3>Source lumineuse</h3><span>01</span></div>
            <div className="source-grid" role="group" aria-label="Type de source">
              {(["laser", "solar", "lamp"] as SourceType[]).map((value) => (
                <button
                  key={value}
                  className={source === value ? "source-btn selected" : "source-btn"}
                  onClick={() => setSource(value)}
                  type="button"
                  aria-pressed={source === value}
                >
                  <span className="source-symbol">{value === "laser" ? "⌁" : value === "solar" ? "☼" : "✳"}</span>
                  {SOURCE_LABEL[value]}
                </button>
              ))}
            </div>
            {source === "laser" ? (
              <label className="field-label" htmlFor="wavelength">
                Longueur d'onde <span>{formatWavelength(wavelengthNm)}</span>
                <input
                  id="wavelength"
                  type="range"
                  min="380"
                  max="780"
                  step="1"
                  value={wavelengthNm}
                  onChange={(event) => setWavelengthNm(Number(event.target.value))}
                />
              </label>
            ) : (
              <div className="info-inline">Spectre de référence : intégration prévue au Sprint S3.</div>
            )}
          </section>

          <section className="control-section">
            <div className="section-line"><h3>Conditions d'incidence</h3><span>02</span></div>
            <label className="field-label" htmlFor="angle">
              Angle d'incidence <span>{angleDeg}°</span>
              <input
                id="angle"
                type="range"
                min="0"
                max="80"
                step="1"
                value={angleDeg}
                onChange={(event) => setAngleDeg(Number(event.target.value))}
              />
            </label>
            <div className="field-caption">Polarisation</div>
            <div className="segmented" role="group" aria-label="Polarisation">
              {(["s", "p", "unpolarized"] as Polarization[]).map((value) => (
                <button
                  type="button"
                  key={value}
                  onClick={() => setPolarization(value)}
                  aria-pressed={polarization === value}
                  className={polarization === value ? "active" : ""}
                >
                  {value === "unpolarized" ? "Non pol." : value.toUpperCase()}
                </button>
              ))}
            </div>
          </section>

          <section className="control-section" id="material-library">
            <div className="section-line"><h3>Couches optiques</h3><span>{String(layers.length).padStart(2, "0")}</span></div>
            <div className="layer-list">
              {layers.map((layer, index) => (
                <div className="layer-card" key={layer.id}>
                  <div className="layer-head">
                    <span className="layer-index">{String(index + 1).padStart(2, "0")}</span>
                    <select
                      aria-label={`Matériau couche ${index + 1}`}
                      value={layer.material}
                      onChange={(event) =>
                        changeMaterial(layer.id, event.target.value as PreviewMaterial)
                      }
                    >
                      {MATERIAL_CHOICES.map((material) => (
                        <option key={material} value={material}>{material}</option>
                      ))}
                    </select>
                    <button
                      className="icon-btn"
                      aria-label={`Supprimer couche ${index + 1}`}
                      disabled={layers.length <= 1}
                      type="button"
                      onClick={() => setLayers((current) => current.filter((item) => item.id !== layer.id))}
                    >×</button>
                  </div>
                  <div className="layer-foot">
                    <label>
                      Épaisseur (nm)
                      <input
                        aria-label={`Épaisseur couche ${index + 1}`}
                        type="number"
                        min="1"
                        step="10"
                        value={layer.thicknessNm}
                        onChange={(event) => setLayers((current) =>
                          updateLayerThickness(current, layer.id, Number(event.target.value))
                        )}
                      />
                    </label>
                    <div className="layer-actions">
                      <button type="button" disabled={index === 0} onClick={() =>
                        setLayers((current) => moveLayer(current, index, -1))
                      } aria-label={`Monter couche ${index + 1}`}>↑</button>
                      <button type="button" disabled={index === layers.length - 1} onClick={() =>
                        setLayers((current) => moveLayer(current, index, 1))
                      } aria-label={`Descendre couche ${index + 1}`}>↓</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <button className="add-layer" type="button" onClick={addLayer}>
              + Ajouter une couche
            </button>
          </section>
        </aside>

        <main className="stage">
          <div className="stage-top">
            <div><span className="eyebrow">OPTICAL STUDIO / SCENE 001</span><h1>La lumière, <em>modélisée.</em></h1></div>
            <span className="stage-tag">VUE D'ASSEMBLAGE</span>
          </div>
          <div className="canvas-container">
            <StudioScene layers={layers} source={source} />
            <div className="canvas-top-note">3D PREVIEW <span>•</span> NON PHYSIQUE</div>
            <div className="canvas-bottom-note">Glisser pour tourner <span>·</span> Molette pour zoomer</div>
            <div className="scene-axis">AIR / {layers.map((layer) => layer.material).join(" / ")}</div>
          </div>
          <div className="stage-bottom">
            <div><span className="eyebrow">ACTIVE STACK</span><strong>{layers.length} couches</strong></div>
            <div><span className="eyebrow">WAVELENGTH</span><strong>{source === "laser" ? formatWavelength(wavelengthNm) : "Spectral"}</strong></div>
            <div><span className="eyebrow">INCIDENCE</span><strong>{angleDeg}° · {polarization.toUpperCase()}</strong></div>
          </div>
        </main>

        <aside className="side-panel right-panel" id="status" aria-label="Résultats scientifiques">
          <div className="panel-heading">
            <span className="eyebrow">02 / SCIENTIFIC OUTPUT</span>
            <h2>Résultats</h2>
            <p>La physique sera calculée par le backend TMM, indépendamment de Three.js.</p>
          </div>
          <div className="awaiting">
            <span className="awaiting-ring">◎</span>
            <h3>En attente du solveur</h3>
            <p>Aucune réflectance, transmission ou absorption n'a encore été calculée.</p>
          </div>
          <div className="metric-list">
            {["RÉFLECTANCE · R", "TRANSMITTANCE · T", "ABSORPTANCE · A"].map((metric) => (
              <div className="metric-row" key={metric}><span>{metric}</span><strong>—</strong></div>
            ))}
          </div>
          <div className="planned-chart">
            <div className="chart-heading">SPECTRAL RESPONSE <span>À VENIR</span></div>
            <div className="chart-grid"><span>R(λ) · T(λ) · A(λ)</span></div>
          </div>
          <div className="disclaimer">
            <span className="disclaimer-icon">!</span>
            <p><strong>Prototype S0.</strong> Les couleurs et les trajectoires affichées sont des illustrations. Aucune propriété optique n'est déduite de Three.js.</p>
          </div>
          <button className="calculate-button" type="button" disabled title="Le moteur TMM sera installé au Sprint S2">
            Calculer la réponse optique <span>↗</span>
          </button>
        </aside>
      </div>
      <footer className="footer">
        <span>OPTICAL LAB © 2026</span><span>REPRODUCIBLE SCIENCE · V1 UNDER CONSTRUCTION</span>
        <a href="https://github.com/notmillions/Optical-lab" target="_blank" rel="noreferrer">GITHUB ↗</a>
      </footer>
    </div>
  );
}

export default App;
