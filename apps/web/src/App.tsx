import { useEffect, useRef, useState } from "react";

import SpectralChart from "./SpectralChart";
import StudioScene from "./StudioScene";
import {
  buildScene, datasetForLayer, getCatalog, representativeValues, runSimulation
} from "./lib/api";
import type { MaterialCatalog, SimulationOutput } from "./lib/api";
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
  const [catalog, setCatalog] = useState<MaterialCatalog | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [result, setResult] = useState<SimulationOutput | null>(null);
  const [calculationError, setCalculationError] = useState<string | null>(null);
  const [computing, setComputing] = useState(false);
  const pendingSimulation = useRef<AbortController | null>(null);
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

  useEffect(() => {
    const abort = new AbortController();
    getCatalog(abort.signal)
      .then((data) => {
        if (abort.signal.aborted) return;
        setCatalog(data);
        setCatalogError(null);
      })
      .catch((error: unknown) => {
        if (abort.signal.aborted) return;
        setCatalogError(error instanceof Error ? error.message : "Impossible de charger le catalogue.");
      });
    return () => abort.abort();
  }, []);

  // Results must always refer to exactly the parameters shown to the user.
  useEffect(() => {
    pendingSimulation.current?.abort();
    setResult(null);
    setCalculationError(null);
    setComputing(false);
  }, [source, angleDeg, wavelengthNm, polarization, layers]);

  const calculate = async () => {
    if (!catalog) {
      setCalculationError(catalogError ?? "Charge d'abord la base de matériaux.");
      return;
    }
    const controller = new AbortController();
    pendingSimulation.current?.abort();
    pendingSimulation.current = controller;
    setComputing(true);
    setCalculationError(null);
    try {
      const scene = buildScene(layers, catalog, source, wavelengthNm, angleDeg, polarization);
      const output = await runSimulation(scene, controller.signal);
      if (!controller.signal.aborted) setResult(output);
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        setCalculationError(error instanceof Error ? error.message : "Simulation indisponible.");
      }
    } finally {
      if (!controller.signal.aborted) setComputing(false);
    }
  };

  const exportResult = () => {
    if (!result) return;
    const payload = {
      result,
      created_at: new Date().toISOString(),
      note: "Résultat TMM. Les sources exactes sont listées dans la base matériaux.",
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "optical-lab-simulation.json";
    link.click();
    URL.revokeObjectURL(url);
  };

  const summary = result ? representativeValues(result) : null;

  const addLayer = () => {
    setLayers((current) => [
      ...current,
      { id: `layer-${nextLayerId.current++}`, material: "SiO₂", thicknessNm: 100 }
    ]);
  };

  const changeMaterial = (id: string, material: PreviewMaterial) =>
    setLayers((current) => current.map((layer) =>
      layer.id === id ? { ...layer, material, datasetId: undefined } : layer
    ));

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">◈</span>
          <span className="brand-name">OPTICAL <strong>LAB</strong></span>
          <span className="brand-version">/ S5 INTEGRATED PROTOTYPE</span>
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
            <p>Configure la lumière, les références de matériaux et les couches. Les résultats proviennent du solveur TMM Python.</p>
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
              <div className="info-inline">{source === "solar" ? "ASTM G173 global (AM1.5) · approximation à angle fixe." : "Lampe incandescente idéale · Planck 2 856 K · visible."}</div>
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
                  <div className="layer-type">{index === layers.length - 1 ? "SUBSTRAT SEMI-INFINI" : "COUCHE FINIE"}</div>
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
                  {catalog && (
                    <label className="dataset-picker">
                      Référence scientifique
                      <select
                        aria-label={`Source de données couche ${index + 1}`}
                        value={layer.datasetId || catalog[layer.material].find((dataset) => dataset.has_n && dataset.has_k)?.id || ""}
                        onChange={(event) => setLayers((current) => current.map((item) =>
                          item.id === layer.id ? { ...item, datasetId: event.target.value } : item
                        ))}
                      >
                        {catalog[layer.material].map((dataset) => (
                          <option key={dataset.id} value={dataset.id}>
                            {dataset.page}{!dataset.has_k ? " (n seul, TMM indisponible)" : ""}
                          </option>
                        ))}
                      </select>
                      <span className="source-hint">
                        {(() => {
                          const selected = catalog[layer.material].find((dataset) =>
                            dataset.id === (layer.datasetId ||
                            catalog[layer.material].find((item) => item.has_n && item.has_k)?.id));
                          return selected
                            ? `${Math.round(selected.min_nm)}–${Math.round(selected.max_nm)} nm · ${selected.source_commit.slice(0, 8)}`
                            : "Référence non disponible";
                        })()}
                      </span>
                    </label>
                  )}
                  <div className="layer-foot">
                    {index === layers.length - 1 ? (
                      <span className="substrate-description">Épaisseur ∞ · flux entrant T</span>
                    ) : (
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
                    )}
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
            {catalogError && <p className="error-message" role="alert">{catalogError}</p>}
            {catalog && <p className="library-ready">Catalogue connecté · Cu, Al, SiO₂ · références originales.</p>}
          </section>
        </aside>

        <main className="stage">
          <div className="stage-top">
            <div><span className="eyebrow">OPTICAL STUDIO / SCENE 001</span><h1>La lumière, <em>modélisée.</em></h1></div>
            <span className="stage-tag">VUE D'ASSEMBLAGE</span>
          </div>
          <div className="canvas-container">
            <StudioScene layers={layers} source={source} response={summary ? { reflectance: summary[0], transmittance: summary[1] } : null} />
            <div className="canvas-top-note">{result ? "CALCUL TMM DISPONIBLE" : "3D PREVIEW"} <span>•</span> RENDU ILLUSTRATIF</div>
            <div className="canvas-bottom-note">Glisser pour tourner <span>·</span> Molette pour zoomer</div>
            <div className="scene-axis">AIR / {layers.map((layer) => layer.material).join(" / ")}</div>
          </div>
          <div className="stage-bottom">
            <div><span className="eyebrow">ACTIVE STACK</span><strong>{layers.length - 1} couche(s) + substrat</strong></div>
            <div><span className="eyebrow">WAVELENGTH</span><strong>{source === "laser" ? formatWavelength(wavelengthNm) : "Spectral"}</strong></div>
            <div><span className="eyebrow">INCIDENCE</span><strong>{angleDeg}° · {polarization.toUpperCase()}</strong></div>
          </div>
        </main>

        <aside className="side-panel right-panel" id="status" aria-label="Résultats scientifiques">
          <div className="panel-heading">
            <span className="eyebrow">02 / SCIENTIFIC OUTPUT</span>
            <h2>Résultats</h2>
            <p>Réflectance, transmission vers le substrat et absorption des couches, calculées par Python.</p>
          </div>
          <div className="awaiting">
            <span className="awaiting-ring">{result ? "✓" : computing ? "◌" : "◎"}</span>
            <h3>{result ? "Simulation calculée" : computing ? "Calcul en cours" : "Simulation disponible"}</h3>
            <p>{result ? `${result.points.length} valeur(s) TMM calculée(s) et vérifiées par le backend.` :
              "Sélectionne les références optiques puis lance le calcul."}</p>
            {calculationError && <p className="error-message" role="alert">{calculationError}</p>}
          </div>
          <div className="metric-list">
            {["RÉFLECTANCE · R", "TRANSMITTANCE · T", "ABSORPTANCE · A"].map((metric, index) => (
              <div className="metric-row" key={metric}>
                <span>{metric}</span>
                <strong>{summary ? `${(summary[index] * 100).toFixed(2)} %` : "—"}</strong>
              </div>
            ))}
          </div>
          <div className="planned-chart">
            <div className="chart-heading">SPECTRAL RESPONSE <span>{result ? "TMM" : "À CALCULER"}</span></div>
            <SpectralChart points={result?.points ?? []} />
            {result?.source_weighted && (
              <p className="source-hint">
                Couverture : {(result.source_weighted.reference_coverage * 100).toFixed(1)} %
                · {result.source_weighted.source_reference}
              </p>
            )}
          </div>
          <div className="disclaimer">
            <span className="disclaimer-icon">!</span>
            <p><strong>Modèle plan TMM.</strong> Les rayons Three.js sont illustratifs. T désigne le flux entrant dans le substrat semi-infini, pas la lumière sortant de sa face arrière. A concerne les couches finies.</p>
          </div>
          <button className="calculate-button" type="button"
            disabled={!catalog || computing || layers.length < 2}
            onClick={() => void calculate()}>
            {computing ? "Calcul en cours..." : "Calculer la réponse optique"} <span>↗</span>
          </button>
          {result && (
            <button className="add-layer export-button" type="button" onClick={exportResult}>
              ↓ Exporter le résultat JSON
            </button>
          )}
          {catalog && (
            <div className="references-preview">
              <span className="eyebrow">RÉFÉRENCES</span>
              {layers.map((layer) => {
                let sourceId = "";
                try { sourceId = datasetForLayer(layer, catalog).page; } catch { sourceId = "indisponible"; }
                return <p key={layer.id}>{layer.material} · {sourceId}</p>;
              })}
            </div>
          )}
        </aside>
      </div>
      <footer className="footer">
        <span>OPTICAL LAB © 2026</span><span>PHYSICAL CORE · TMM + DATA PROVENANCE · V1 IN PROGRESS</span>
        <a href="https://github.com/notmillions/Optical-lab" target="_blank" rel="noreferrer">GITHUB ↗</a>
      </footer>
    </div>
  );
}

export default App;
