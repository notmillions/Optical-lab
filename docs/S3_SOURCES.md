# Sprint S3 — Sources lumineuses et pondération spectrale

## Livrables
Sources lumineuses permettant au solveur TMM de traiter des spectres d'énergie :

1. **Laser monochromatique idéal** : longueur d'onde, incidence et polarisation (disponibles depuis S2).
2. **Soleil ASTM G173-03** : composantes `global` ou `direct` depuis les données de référence NREL distribuées dans [pvlib](https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.spectrum.get_reference_spectra.html). La densité spectrale est en `W m⁻² nm⁻¹`.
3. **Lampe incandescente théorique** : loi de Planck, corps noir idéal à 2856 K, **visible seulement** (380–780 nm), intensité relative. Ce n'est ni une mesure d'une lampe réelle, ni une table certifiée CIE A, ni un spectre LED.

Le calcul utilise le moteur `tmm` et les constantes n,k issues de RefractiveIndex.INFO sélectionnées dans SQLite.

## Calcul
Pour une densité d'énergie spectrale S(λ), sur le domaine commun **effectivement disponible** :

```text
R_eff = integral S(lambda) R(lambda) dlambda / integral S(lambda) dlambda
T_eff = integral S(lambda) T(lambda) dlambda / integral S(lambda) dlambda
A_eff = integral S(lambda) A(lambda) dlambda / integral S(lambda) dlambda
```

Les mêmes équations servent pour l'énergie issue de la source ; **pas** pour le décompte de photons. L'intégration ne renvoie **pas** de watts absolus sans géométrie et normalisation explicites.

La réponse renvoie `reference_coverage` : fraction du flux intégré du spectre de référence dont les longueurs d'onde sont compatibles avec le matériau. Si elle est inférieure à 100 %, **ne pas** présenter le résultat comme global à la source entière.

Les résultats d'un spectre solaire `global` restent ceux d'une **approximation mono-angle** : les composantes diffuses ne sont pas intégrées angulairement. Cela doit être indiqué dans l'application.

## API
- `GET /api/v1/simulations/sources` catalogue sources et identifiants.
- `POST /api/v1/simulations` avec une scène `source.type=solar|lamp` et `source.spectrum_id`.
- L'API renvoie les points `points`, les moyennes `source_weighted.effective_R/T/A`, la couverture spectrale, les unités et la provenance.
- `POST /api/v1/simulations/spectral` reste destiné aux grilles utilisateur associées à un **laser** ; les sources broadband utilisent leur spectre natif ou un sous-échantillonnage contrôlé.

Exemple lampe :
```json
"source": {
  "type": "lamp",
  "spectrum_id": "incandescent-2856K-planck"
}
```

Exemple solaire :
```json
"source": {
  "type": "solar",
  "spectrum_id": "ASTM-G173-global"
}
```

## Vérifications
- Chargement de la référence ASTM via pvlib.
- Forme spectrale Planck positive et pondération normalisée.
- Limitation aux plages optiques n,k réellement disponibles.
- Conservation de l'énergie `R_eff + T_eff + A_eff ≈ 1`.
- Tests API et erreurs d'identifiant de spectre inconnu.
- Les tests utilisent des index optiques **synthétiques explicitement marqués**, distincts des matériaux publiés.

## Limites restantes
- Lampe réelle/LED : import d'un spectre mesuré et référence bibliographique à ajouter.
- Pour modéliser complètement le soleil global, tenir compte de la distribution des angles et non uniquement de la densité spectrale.
- Frontend 3D S0 non encore relié aux résultats ; cela relève du sprint interface.
- Validation Touloukian/EKHI à faire.
