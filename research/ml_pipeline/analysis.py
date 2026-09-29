"""
Unsupervised Analysis: Composite Indices & Farmer Clustering
=============================================================
PCA-based composite scoring and K-Means clustering for farmer surveys.

These are defensible, unsupervised techniques that:
- Discover structure in the data without imposed targets
- Create continuous indices (more informative than binary classification)
- Identify natural farmer archetypes via clustering
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import json

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


# Thematic feature groups for composite index construction.
# Each index combines related features via standardization + averaging,
# with direction set so higher = MORE of the named concept.
INDEX_DEFINITIONS = {
    'water_vulnerability': {
        'features': ['water_sufficiency_score', 'water_scarcity_months'],
        'directions': [-1, 1],  # invert sufficiency: low sufficiency → high vulnerability
        'description': 'Water stress level (higher = more vulnerable)',
    },
    'agricultural_capacity': {
        'features': ['production_level_score', 'crop_diversity', 'farm_size_score', 'has_animals'],
        'directions': [1, 1, 1, 1],
        'description': 'Agricultural production capacity (higher = more productive)',
    },
    'chemical_dependency': {
        'features': ['fertilizer_reliance_score', 'pesticide_reliance_score'],
        'directions': [1, 1],
        'description': 'Reliance on chemical inputs (higher = more dependent)',
    },
    'sustainability_practices': {
        'features': ['uses_organic_enhancer', 'uses_bio_pest_control',
                     'soil_enhancer_diversity', 'regen_technique_count'],
        'directions': [1, 1, 1, 1],
        'description': 'Adoption of sustainable/regenerative practices (higher = more sustainable)',
    },
}


class FarmAnalysis:
    """Unsupervised analysis of farmer survey data."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.pca = None
        self.kmeans = None
        self.index_stats = {}
        self.cluster_profiles = {}

    def compute_composite_indices(self, df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
        """Create composite indices from thematic feature groups.

        Each index: standardize features → apply direction → average.
        Result is z-scored (mean=0, std=1), then rescaled to 0-100 for display.
        """
        print("\n=== Composite Index Construction ===")

        for idx_name, defn in INDEX_DEFINITIONS.items():
            available = [f for f in defn['features'] if f in feature_cols]
            if len(available) < 2:
                print(f"  ⚠️  {idx_name}: only {len(available)} features available, skipping")
                continue

            # Standardize each feature
            sub = df[available].copy()
            for col in available:
                mean, std = sub[col].mean(), sub[col].std()
                if std > 0:
                    sub[col] = (sub[col] - mean) / std
                else:
                    sub[col] = 0

            # Apply direction (invert where needed)
            dirs = defn['directions'][:len(available)]
            for col, d in zip(available, dirs):
                sub[col] = sub[col] * d

            # Average to create composite
            raw_index = sub.mean(axis=1)

            # Rescale to 0-100 for interpretability
            rmin, rmax = raw_index.min(), raw_index.max()
            if rmax > rmin:
                scaled = ((raw_index - rmin) / (rmax - rmin) * 100).round(1)
            else:
                scaled = pd.Series(50.0, index=df.index)

            col_name = f'idx_{idx_name}'
            df[col_name] = scaled

            self.index_stats[idx_name] = {
                'features_used': available,
                'mean': float(scaled.mean()),
                'std': float(scaled.std()),
                'min': float(scaled.min()),
                'max': float(scaled.max()),
                'description': defn['description'],
            }
            print(f"  ✓ {col_name}: mean={scaled.mean():.1f}, std={scaled.std():.1f} "
                  f"({len(available)} features)")

        return df

    def run_pca(self, df: pd.DataFrame, feature_cols: List[str],
                n_components: int = 4) -> pd.DataFrame:
        """Run PCA on all features to discover main axes of variation.

        The first principal component serves as an overall 'farm resilience'
        score; subsequent components capture secondary structure.
        """
        print("\n=== PCA Analysis ===")

        available = [f for f in feature_cols if f in df.columns]
        X = df[available].fillna(df[available].median())

        # Standardize
        X_scaled = self.scaler.fit_transform(X)

        n_components = min(n_components, len(available), len(df))
        self.pca = PCA(n_components=n_components, random_state=42)
        components = self.pca.fit_transform(X_scaled)

        # Name components and add to dataframe
        for i in range(n_components):
            col_name = f'pca_{i+1}'
            raw = components[:, i]
            # Rescale to 0-100
            rmin, rmax = raw.min(), raw.max()
            if rmax > rmin:
                df[col_name] = ((raw - rmin) / (rmax - rmin) * 100).round(1)
            else:
                df[col_name] = 50.0

        # Report variance explained
        var_explained = self.pca.explained_variance_ratio_
        cum_var = np.cumsum(var_explained)
        print(f"  Components: {n_components}")
        for i in range(n_components):
            print(f"    PC{i+1}: {var_explained[i]*100:.1f}% variance "
                  f"(cumulative: {cum_var[i]*100:.1f}%)")

        # Report top loadings for PC1 (overall farm score)
        loadings = pd.DataFrame(
            self.pca.components_.T,
            index=available,
            columns=[f'PC{i+1}' for i in range(n_components)],
        )
        print(f"\n  PC1 top loadings (overall farm score):")
        top = loadings['PC1'].abs().sort_values(ascending=False).head(8)
        for feat in top.index:
            val = loadings.loc[feat, 'PC1']
            print(f"    {feat}: {val:+.3f}")

        self.pca_loadings = loadings
        return df

    def run_clustering(self, df: pd.DataFrame, feature_cols: List[str],
                       k_range: Tuple[int, int] = (3, 6)) -> pd.DataFrame:
        """K-Means clustering to identify farmer archetypes.

        Selects optimal K via silhouette score.
        """
        print("\n=== K-Means Farmer Clustering ===")

        available = [f for f in feature_cols if f in df.columns]
        X = df[available].fillna(df[available].median())
        X_scaled = StandardScaler().fit_transform(X)

        # Find optimal K
        best_k, best_score = k_range[0], -1
        scores = {}
        for k in range(k_range[0], k_range[1] + 1):
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(X_scaled)

            # Need at least 2 clusters with >1 member
            if len(set(labels)) < 2:
                continue

            sil = silhouette_score(X_scaled, labels)
            scores[k] = sil
            print(f"  K={k}: silhouette={sil:.3f}")

            if sil > best_score:
                best_score = sil
                best_k = k

        print(f"  → Optimal K={best_k} (silhouette={best_score:.3f})")

        # Fit final model
        self.kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        df['farmer_cluster'] = self.kmeans.fit_predict(X_scaled)

        # Profile each cluster
        print(f"\n  Cluster profiles (K={best_k}):")
        profile_features = [f for f in ['water_sufficiency_score', 'farm_size_score',
                                         'production_level_score', 'chemical_input_intensity',
                                         'crop_diversity', 'regen_technique_count',
                                         'climate_impact_count']
                            if f in df.columns]

        self.cluster_profiles = {}
        for c in range(best_k):
            mask = df['farmer_cluster'] == c
            n = mask.sum()
            profile = {}
            for f in profile_features:
                profile[f] = round(float(df.loc[mask, f].mean()), 2)
            self.cluster_profiles[c] = {
                'size': int(n),
                'pct': round(n / len(df) * 100, 1),
                'profile': profile,
            }
            print(f"\n    Cluster {c} (n={n}, {self.cluster_profiles[c]['pct']}%):")
            for f, v in profile.items():
                print(f"      {f}: {v}")

        return df

    def generate_analysis_report(self, output_dir: str = "data/models") -> dict:
        """Save analysis results as JSON for documentation."""
        report = {
            'composite_indices': self.index_stats,
            'pca': {
                'n_components': self.pca.n_components_ if self.pca else 0,
                'variance_explained': (
                    [round(v, 4) for v in self.pca.explained_variance_ratio_.tolist()]
                    if self.pca else []
                ),
                'loadings': (
                    {col: {feat: round(v, 4) for feat, v in self.pca_loadings[col].items()}
                     for col in self.pca_loadings.columns}
                    if hasattr(self, 'pca_loadings') else {}
                ),
            },
            'clustering': {
                'k': self.kmeans.n_clusters if self.kmeans else 0,
                'profiles': self.cluster_profiles,
            },
        }

        output_path = Path(output_dir) / "analysis_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✓ Analysis report saved to {output_path}")

        return report

    def run_full_analysis(self, df: pd.DataFrame,
                          feature_cols: List[str]) -> pd.DataFrame:
        """Run complete unsupervised analysis pipeline.

        Adds to df:
          idx_water_vulnerability, idx_agricultural_capacity,
          idx_chemical_dependency, idx_sustainability_practices,
          pca_1 .. pca_4,
          farmer_cluster
        """
        print("\n" + "=" * 60)
        print("UNSUPERVISED ANALYSIS")
        print("=" * 60)

        df = self.compute_composite_indices(df, feature_cols)
        df = self.run_pca(df, feature_cols)
        df = self.run_clustering(df, feature_cols)

        self.generate_analysis_report()

        return df
