# Démarche scientifique — acquisition, modélisation, validation

## 1. Acquisition
RefractiveIndex.INFO : conserver la version du dépôt, les fichiers YAML originaux (ou hash), les noms des auteurs, DOI, domaines spectraux et les différents jeux de données par matériau. Étudier aussi les prescriptions de scraping HTML du TP ; l'import YAML est plus robuste mais ne remplace pas un exercice de scraping explicitement imposé.

## 2. Convention
Indice complexe `N(λ)=n(λ)+i k(λ)` avec la convention temporelle/propagative cohérente avec le solveur. `k` est un coefficient d'extinction sans dimension, **pas** le coefficient d'absorption `α`. `α(λ)=4πk(λ)/λ` avec λ en mètres donne α en m⁻¹. Intensité `I(z)=I(0)exp(-αz)` dans un milieu homogène sous les hypothèses de Beer-Lambert.

## 3. Cas analytique
Interface air–matériau à incidence normale :
`R = ((n-1)^2+k^2)/((n+1)^2+k^2)`.
Pour n=1.5 et k=0 : R=0.04 ; T=0.96 à l'interface sans pertes. Pour une couche finie, les réflexions multiples et interférences changent T. À incidence normale les polarisations s et p ont même réflectance.

## 4. Multicouches
TMM cohérente pour films où les phases interfèrent ; modèle incohérent/mixte selon épaisseur et propriétés de la source. Échantillons linéaires, isotropes, plans, non diffusants. Signaler substrats semi-infinis et couches finies. Vérifier l'absorption couche par couche lorsque le solveur le permet.

## 5. Sources
Laser monochromatique idéal ; soleil avec spectre normalisé et provenance ; lampe avec spectre documenté ; spectres importés (unités validées). La réponse spectrale `R(λ)` peut être moyennée par une puissance spectrale S : `R_eff = ∫S(λ)R(λ)dλ / ∫S(λ)dλ` sur le domaine commun de validité. Ne déduire des W absolus que si l'entrée et la géométrie définissent cette grandeur.

## 6. Validation
Contrôles : n=1.5/k=0/R=4 %, s/p à incidence normale, α=0 si k=0, `R+T+A≈1` pour milieux passifs et définitions cohérentes, convergence numérique et domaine λ. Comparer à un second calcul indépendant. Touloukian : privilégier volumes 7, 8 et éventuellement 9. Ne comparer que des mesures équivalentes (spectrale ou hémisphérique, angle, T, polarisation, surface). EKHI éventuel : vérifier métadonnées, licence et origine. Si les données ne sont pas comparables, le documenter et choisir un autre matériau.

## 7. Présentation
Chaque graphique et export doit indiquer matériaux, datasets, références, unités, longueur d'onde, angles, température si connue, hypothèses et version solveur. Les rendus Three.js sont des illustrations pilotées par des résultats calculés, pas des rayons 3D physiquement tracés.
