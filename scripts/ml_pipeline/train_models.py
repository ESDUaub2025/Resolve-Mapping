"""
Model Training Pipeline
========================
Train machine learning models with spatial cross-validation.

Models: RandomForest, XGBoost for each of 5 prediction targets
Validation: Spatial leave-one-village-out cross-validation
Output: Trained models (.joblib), validation metrics, feature importance
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import json
import joblib
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import cross_val_score, LeaveOneGroupOut
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    f1_score, precision_score, recall_score, accuracy_score
)
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("Warning: XGBoost not installed, using RandomForest only")


class ModelTrainer:
    """Train and validate ML models for agricultural predictions."""
    
    def __init__(self, data_path: str = "data/ml_prepared_data.csv"):
        self.data_path = Path(data_path)
        self.df = None
        self.features = None
        self.targets = None
        self.models = {}
        self.metrics = {}
        
    def load_data(self):
        """Load prepared dataset."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Prepared data not found: {self.data_path}")
        
        self.df = pd.read_csv(self.data_path)
        
        # Identify feature and target columns
        self.targets = [c for c in self.df.columns if c.startswith('target_')]
        village_col = next((c for c in self.df.columns if 'village' in c.lower() or c in ['_3', 'merge_key']), 'merge_key')
        exclude_cols = ['feature_id', 'theme', 'coord_hash', village_col, 'longitude', 'latitude'] + self.targets
        self.features = [c for c in self.df.columns if c not in exclude_cols and self.df[c].dtype in ['int64', 'float64']]
        
        print(f"✓ Loaded {len(self.df)} samples")
        print(f"  Features: {len(self.features)}")
        print(f"  Targets: {len(self.targets)}")
        
    def spatial_cross_validation(self, X, y, groups, model, n_splits: int = 5):
        """Perform spatial cross-validation using LeaveOneGroupOut on villages."""
        
        # For large number of villages, use subset of villages as groups
        unique_groups = groups.unique()
        if len(unique_groups) > n_splits:
            # Sample n_splits villages randomly for cross-validation
            selected_groups = np.random.choice(unique_groups, n_splits, replace=False)
            mask = groups.isin(selected_groups)
            X_cv, y_cv, groups_cv = X[mask], y[mask], groups[mask]
        else:
            X_cv, y_cv, groups_cv = X, y, groups
        
        logo = LeaveOneGroupOut()
        scores = []
        
        for train_idx, test_idx in logo.split(X_cv, y_cv, groups_cv):
            X_train, X_test = X_cv.iloc[train_idx], X_cv.iloc[test_idx]
            y_train, y_test = y_cv.iloc[train_idx], y_cv.iloc[test_idx]
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            scores.append(f1_score(y_test, y_pred, zero_division=0))
        
        return np.mean(scores), np.std(scores)
    
    def train_model(self, target: str, model_type: str = 'random_forest') -> Dict:
        """Train a single model for given target."""
        
        print(f"\n--- Training {model_type} for {target} ---")
        
        # Prepare data
        X = self.df[self.features]
        y = self.df[target]
        
        # Create spatial groups based on coordinates (grid cells for CV)
        # Use 0.02 degree grid (~2km) to ensure multiple groups
        lon_bins = pd.cut(self.df['longitude'], bins=5, labels=False)
        lat_bins = pd.cut(self.df['latitude'], bins=5, labels=False)
        groups = lon_bins * 10 + lat_bins  # Combine into unique group IDs
        
        print(f"Spatial groups for CV: {groups.nunique()} unique groups")
        
        # Check class balance
        pos_rate = y.mean() * 100
        print(f"Positive class rate: {pos_rate:.1f}%")
        
        if y.sum() < 5:
            print(f"⚠️  Insufficient positive samples ({y.sum()}), skipping model training")
            return None
        
        # Initialize model
        if model_type == 'random_forest':
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'xgboost' and HAS_XGBOOST:
            scale_pos_weight = (len(y) - y.sum()) / max(y.sum(), 1)
            model = XGBClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                scale_pos_weight=scale_pos_weight,
                random_state=42,
                n_jobs=-1,
                eval_metric='logloss'
            )
        elif model_type == 'logistic':
            model = LogisticRegression(
                class_weight='balanced',
                max_iter=1000,
                random_state=42
            )
        else:
            print(f"Unknown model type: {model_type}, using RandomForest")
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Spatial cross-validation
        print("Running spatial cross-validation...")
        cv_f1_mean, cv_f1_std = self.spatial_cross_validation(X, y, groups, model, n_splits=5)
        print(f"CV F1-Score: {cv_f1_mean:.3f} ± {cv_f1_std:.3f}")
        
        # Train final model on all data
        print("Training final model on full dataset...")
        model.fit(X, y)
        
        # Predictions and metrics
        y_pred = model.predict(X)
        y_proba = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else y_pred
        
        metrics = {
            'target': target,
            'model_type': model_type,
            'n_samples': len(y),
            'n_features': len(self.features),
            'pos_rate': pos_rate,
            'cv_f1_mean': cv_f1_mean,
            'cv_f1_std': cv_f1_std,
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1_score': f1_score(y, y_pred, zero_division=0),
        }
        
        if len(np.unique(y)) > 1:
            metrics['roc_auc'] = roc_auc_score(y, y_proba)
        
        # Feature importance
        if hasattr(model, 'feature_importances_'):
            importance = pd.DataFrame({
                'feature': self.features,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False).head(10)
            metrics['top_features'] = importance.to_dict('records')
        
        print(f"\n✓ Model trained:")
        print(f"  Accuracy: {metrics['accuracy']:.3f}")
        print(f"  F1-Score: {metrics['f1_score']:.3f}")
        print(f"  ROC-AUC: {metrics.get('roc_auc', 'N/A')}")
        
        if 'top_features' in metrics:
            print("\nTop 5 Features:")
            for feat in metrics['top_features'][:5]:
                print(f"  {feat['feature']}: {feat['importance']:.3f}")
        
        return {
            'model': model,
            'metrics': metrics,
            'confusion_matrix': confusion_matrix(y, y_pred).tolist()
        }
    
    def train_all_models(self, model_type: str = 'random_forest'):
        """Train models for all target variables."""
        
        print("\n=== Training All Models ===\n")
        
        self.load_data()
        
        for target in self.targets:
            result = self.train_model(target, model_type)
            if result:
                self.models[target] = result['model']
                self.metrics[target] = result['metrics']
                self.metrics[target]['confusion_matrix'] = result['confusion_matrix']
        
        print(f"\n✓ Trained {len(self.models)} models successfully")
    
    def save_models(self, output_dir: str = "data/models"):
        """Save trained models and metrics."""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save each model
        for target, model in self.models.items():
            model_file = output_path / f"{target}_model.joblib"
            joblib.dump(model, model_file)
            print(f"✓ Saved {model_file.name}")
        
        # Save metrics report
        metrics_file = output_path / "training_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        print(f"✓ Saved {metrics_file.name}")
        
        # Save feature list
        features_file = output_path / "feature_list.json"
        with open(features_file, 'w') as f:
            json.dump({'features': self.features, 'targets': self.targets}, f, indent=2)
        print(f"✓ Saved {features_file.name}")
        
        print(f"\n✓ All models saved to {output_path}/")
    
    def generate_report(self, output_file: str = "data/models/training_report.txt"):
        """Generate human-readable training report."""
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("AGRICULTURAL AI MODEL TRAINING REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        for target, metrics in self.metrics.items():
            report_lines.append(f"\n{target.upper()}")
            report_lines.append("-" * 40)
            report_lines.append(f"Model Type: {metrics['model_type']}")
            report_lines.append(f"Samples: {metrics['n_samples']}")
            report_lines.append(f"Features: {metrics['n_features']}")
            report_lines.append(f"Positive Rate: {metrics['pos_rate']:.1f}%")
            report_lines.append("")
            report_lines.append("Cross-Validation Metrics:")
            report_lines.append(f"  F1-Score (CV): {metrics['cv_f1_mean']:.3f} ± {metrics['cv_f1_std']:.3f}")
            report_lines.append("")
            report_lines.append("Training Set Performance:")
            report_lines.append(f"  Accuracy:  {metrics['accuracy']:.3f}")
            report_lines.append(f"  Precision: {metrics['precision']:.3f}")
            report_lines.append(f"  Recall:    {metrics['recall']:.3f}")
            report_lines.append(f"  F1-Score:  {metrics['f1_score']:.3f}")
            if 'roc_auc' in metrics:
                report_lines.append(f"  ROC-AUC:   {metrics['roc_auc']:.3f}")
            
            if 'top_features' in metrics:
                report_lines.append("")
                report_lines.append("Top 5 Most Important Features:")
                for i, feat in enumerate(metrics['top_features'][:5], 1):
                    report_lines.append(f"  {i}. {feat['feature']}: {feat['importance']:.3f}")
            
            if 'confusion_matrix' in metrics:
                cm = metrics['confusion_matrix']
                report_lines.append("")
                report_lines.append("Confusion Matrix:")
                report_lines.append(f"  [[TN={cm[0][0]}, FP={cm[0][1]}],")
                report_lines.append(f"   [FN={cm[1][0]}, TP={cm[1][1]}]]")
        
        report_lines.append("\n" + "=" * 80)
        
        report_text = "\n".join(report_lines)
        
        # Save to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report_text)
        
        # Print to console
        print("\n" + report_text)
        print(f"\n✓ Report saved to {output_path}")


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    model_type = sys.argv[1] if len(sys.argv) > 1 else 'random_forest'
    
    print(f"Training models with {model_type}...")
    
    trainer = ModelTrainer()
    trainer.train_all_models(model_type=model_type)
    trainer.save_models()
    trainer.generate_report()
    
    print("\n=== Model Training Complete ===")
