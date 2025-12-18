"""
ML Pipeline Orchestrator
=========================
Master script to run complete ML pipeline from raw data to predictions.

Usage:
    python run_pipeline.py                    # Full pipeline
    python run_pipeline.py --features-only    # Feature engineering only
    python run_pipeline.py --train-only       # Training only
    python run_pipeline.py --validate         # Validation only mode
"""

import sys
import argparse
from pathlib import Path
import time

# Import pipeline modules
try:
    from feature_engineering import FeatureEngineer
    from train_models import ModelTrainer
    from interpolate_grid import GridInterpolator
    from generate_boundary import BoundaryGenerator
except ImportError:
    # If running from parent directory
    sys.path.insert(0, str(Path(__file__).parent))
    from feature_engineering import FeatureEngineer
    from train_models import ModelTrainer
    from interpolate_grid import GridInterpolator
    from generate_boundary import BoundaryGenerator


class PipelineOrchestrator:
    """Orchestrate complete ML pipeline execution."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.timings = {}
        
    def run_feature_engineering(self):
        """Step 1: Feature engineering."""
        print("\n" + "=" * 80)
        print("STEP 1: FEATURE ENGINEERING")
        print("=" * 80)
        
        start_time = time.time()
        
        engineer = FeatureEngineer()
        df, features, targets = engineer.prepare_ml_dataset()
        engineer.save_prepared_data()
        
        self.timings['feature_engineering'] = time.time() - start_time
        
        return df, features, targets
    
    def run_model_training(self, model_type: str = 'random_forest'):
        """Step 2: Model training."""
        print("\n" + "=" * 80)
        print("STEP 2: MODEL TRAINING")
        print("=" * 80)
        
        start_time = time.time()
        
        trainer = ModelTrainer()
        trainer.train_all_models(model_type=model_type)
        trainer.save_models()
        trainer.generate_report()
        
        self.timings['model_training'] = time.time() - start_time
    
    def run_grid_interpolation(self, resolution: float = 0.005):
        """Step 3: Grid interpolation."""
        print("\n" + "=" * 80)
        print("STEP 3: GRID INTERPOLATION")
        print("=" * 80)
        
        start_time = time.time()
        
        interpolator = GridInterpolator()
        interpolator.run_pipeline(resolution=resolution)
        
        self.timings['grid_interpolation'] = time.time() - start_time
    
    def run_boundary_generation(self, method: str = 'convex_hull'):
        """Step 4: Boundary generation."""
        print("\n" + "=" * 80)
        print("STEP 4: BOUNDARY GENERATION")
        print("=" * 80)
        
        start_time = time.time()
        
        generator = BoundaryGenerator()
        generator.generate_boundary(method=method)
        
        self.timings['boundary_generation'] = time.time() - start_time
    
    def print_summary(self):
        """Print pipeline execution summary."""
        print("\n" + "=" * 80)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 80)
        
        total_time = sum(self.timings.values())
        
        for step, duration in self.timings.items():
            pct = (duration / total_time) * 100 if total_time > 0 else 0
            print(f"{step:.<50} {duration:.1f}s ({pct:.1f}%)")
        
        print(f"{'TOTAL TIME':.<50} {total_time:.1f}s")
        
        print("\n" + "=" * 80)
        print("OUTPUT FILES:")
        print("=" * 80)
        
        output_files = [
            "data/ml_prepared_data.csv",
            "data/models/target_regen_adoption_model.joblib",
            "data/models/target_water_risk_model.joblib",
            "data/models/target_economic_vuln_model.joblib",
            "data/models/target_labor_shortage_model.joblib",
            "data/models/target_climate_vuln_model.joblib",
            "data/models/training_metrics.json",
            "data/models/training_report.txt",
            "data/geojson/AI_Grid_Predictions.geojson",
            "data/geojson/Farmers_Boundary.geojson"
        ]
        
        for filepath in output_files:
            path = Path(filepath)
            if path.exists():
                size = path.stat().st_size / 1024  # KB
                print(f"✓ {filepath} ({size:.1f} KB)")
            else:
                print(f"⚠️  {filepath} (not generated)")
    
    def run_full_pipeline(
        self,
        model_type: str = 'random_forest',
        grid_resolution: float = 0.005,
        boundary_method: str = 'convex_hull'
    ):
        """Execute complete pipeline."""
        
        print("\n" + "=" * 80)
        print("AGRICULTURAL AI ML PIPELINE")
        print("Mount Lebanon & Chouf District - Farmer Survey Analysis")
        print("=" * 80)
        print(f"\nConfiguration:")
        print(f"  Model Type: {model_type}")
        print(f"  Grid Resolution: {grid_resolution}° (~{grid_resolution * 111:.1f}km)")
        print(f"  Boundary Method: {boundary_method}")
        
        try:
            # Step 1: Feature Engineering
            self.run_feature_engineering()
            
            # Step 2: Model Training
            self.run_model_training(model_type=model_type)
            
            # Step 3: Grid Interpolation
            self.run_grid_interpolation(resolution=grid_resolution)
            
            # Step 4: Boundary Generation
            self.run_boundary_generation(method=boundary_method)
            
            # Summary
            self.print_summary()
            
            print("\n" + "=" * 80)
            print("✓ PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 80)
            print("\nNext steps:")
            print("1. Review training_report.txt for model performance")
            print("2. Inspect AI_Grid_Predictions.geojson for spatial patterns")
            print("3. Refresh browser to see AI heatmap layers on map")
            print("=" * 80 + "\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Pipeline failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point with CLI argument parsing."""
    
    parser = argparse.ArgumentParser(
        description="Agricultural AI ML Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py                              # Full pipeline with defaults
  python run_pipeline.py --model xgboost              # Use XGBoost models
  python run_pipeline.py --resolution 0.01            # Coarser grid (faster)
  python run_pipeline.py --features-only              # Feature engineering only
  python run_pipeline.py --train-only                 # Training only (requires prepared data)
        """
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='random_forest',
        choices=['random_forest', 'xgboost', 'logistic'],
        help='Model type for classification'
    )
    
    parser.add_argument(
        '--resolution',
        type=float,
        default=0.005,
        help='Grid resolution in degrees (default: 0.005 ≈ 500m)'
    )
    
    parser.add_argument(
        '--boundary',
        type=str,
        default='convex_hull',
        choices=['convex_hull', 'alpha_shape'],
        help='Boundary generation method'
    )
    
    parser.add_argument(
        '--features-only',
        action='store_true',
        help='Run feature engineering only'
    )
    
    parser.add_argument(
        '--train-only',
        action='store_true',
        help='Run model training only (requires prepared data)'
    )
    
    parser.add_argument(
        '--interpolate-only',
        action='store_true',
        help='Run grid interpolation only (requires trained models)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validation-only mode (no training, just report metrics)'
    )
    
    args = parser.parse_args()
    
    orchestrator = PipelineOrchestrator()
    
    # Execute based on flags
    if args.features_only:
        orchestrator.run_feature_engineering()
    elif args.train_only:
        orchestrator.run_model_training(model_type=args.model)
    elif args.interpolate_only:
        orchestrator.run_grid_interpolation(resolution=args.resolution)
    elif args.validate:
        print("Validation mode not yet implemented")
        # TODO: Implement validation-only mode
    else:
        # Full pipeline
        success = orchestrator.run_full_pipeline(
            model_type=args.model,
            grid_resolution=args.resolution,
            boundary_method=args.boundary
        )
        
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
