"""
Experiment Runner
=================
Downloads the Kodak dataset, runs all enhancement methods,
computes metrics, performs grid search optimization,
and generates all results figures and tables.

Usage:
    python -m src.experiments
"""

import os
import sys
import json
import numpy as np
import cv2
import requests
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.enhancement import (apply_clahe_rgb, apply_clahe_hsi,
                              apply_histogram_equalization_rgb,
                              apply_histogram_equalization_hsi,
                              apply_gamma_correction_rgb,
                              apply_gamma_correction_hsi)
from src.adaptive_selector import adaptive_enhance, grid_search_thresholds, extract_features
from src.metrics import (compute_psnr, compute_ssim, compute_ciede2000,
                         compute_colorfulness, compute_intensity_variance,
                         compute_contrast_ratio)
from src.visualization import (plot_side_by_side, plot_metrics_bar_chart,
                                plot_threshold_heatmap, plot_per_image_analysis,
                                create_pipeline_flowchart)


# --- Dataset ---
KODAK_BASE_URL = "http://r0k.us/graphics/kodak/kodak/"
KODAK_COUNT = 24
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
FIGURES_DIR = os.path.join(RESULTS_DIR, 'figures')


def download_kodak_dataset():
    """Download Kodak Lossless True Color Image Suite."""
    os.makedirs(DATA_DIR, exist_ok=True)
    images = []
    names = []

    for i in range(1, KODAK_COUNT + 1):
        filename = f"kodim{i:02d}.png"
        filepath = os.path.join(DATA_DIR, filename)

        if not os.path.exists(filepath):
            url = KODAK_BASE_URL + filename
            print(f"  Downloading {filename}...")
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
            except Exception as e:
                print(f"  Warning: Failed to download {filename}: {e}")
                continue

        img = cv2.imread(filepath)
        if img is not None:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            images.append(img)
            names.append(filename)
        else:
            print(f"  Warning: Failed to load {filename}")

    print(f"  Loaded {len(images)} images from Kodak dataset.")
    return images, names


def run_enhancement_methods(image, clip_limit=2.0):
    """Run all enhancement methods on a single image and return results."""
    results = {}
    runtimes = {}

    methods = {
        'CLAHE-RGB': lambda img: apply_clahe_rgb(img, clip_limit=clip_limit),
        'CLAHE-HSI': lambda img: apply_clahe_hsi(img, clip_limit=clip_limit),
        'HE-RGB': apply_histogram_equalization_rgb,
        'HE-HSI': apply_histogram_equalization_hsi,
        'Gamma-RGB': lambda img: apply_gamma_correction_rgb(img, gamma=0.7),
        'Gamma-HSI': lambda img: apply_gamma_correction_hsi(img, gamma=0.7),
    }

    for name, func in methods.items():
        start = time.perf_counter()
        results[name] = func(image)
        runtimes[name] = time.perf_counter() - start

    # Adaptive method
    start = time.perf_counter()
    enhanced, space, features = adaptive_enhance(image, clip_limit=clip_limit)
    runtimes['ACSS'] = time.perf_counter() - start
    results['ACSS'] = enhanced

    return results, runtimes, space, features


def compute_all_metrics(original, enhanced_dict):
    """Compute all metrics for each enhanced image."""
    all_metrics = {}
    for name, enhanced in enhanced_dict.items():
        all_metrics[name] = {
            'PSNR': compute_psnr(original, enhanced),
            'SSIM': compute_ssim(original, enhanced),
            'CIEDE2000': compute_ciede2000(original, enhanced),
        }
    return all_metrics


def run_full_experiment():
    """Run the complete experiment pipeline."""
    print("=" * 60)
    print("ADAPTIVE COLOR SPACE SELECTION - FULL EXPERIMENT")
    print("=" * 60)

    # Step 1: Download dataset
    print("\n[1/6] Downloading Kodak dataset...")
    images, names = download_kodak_dataset()
    if len(images) == 0:
        print("ERROR: No images loaded. Exiting.")
        return

    # Step 2: Run all methods on all images
    print("\n[2/6] Running enhancement methods on all images...")
    all_results = {}
    all_runtimes = {}
    all_spaces = {}
    all_features = {}

    for i, (img, name) in enumerate(zip(images, names)):
        print(f"  Processing {name} ({i+1}/{len(images)})...")
        results, runtimes, space, features = run_enhancement_methods(img)
        all_results[name] = results
        all_runtimes[name] = runtimes
        all_spaces[name] = space
        all_features[name] = features

    # Step 3: Compute metrics
    print("\n[3/6] Computing quality metrics...")
    all_metrics = {}
    for name, img in zip(names, images):
        all_metrics[name] = compute_all_metrics(img, all_results[name])

    # Step 4: Aggregate results
    print("\n[4/6] Aggregating results...")
    methods_list = ['CLAHE-RGB', 'CLAHE-HSI', 'HE-RGB', 'HE-HSI',
                    'Gamma-RGB', 'Gamma-HSI', 'ACSS']

    # Aggregate metrics
    agg = {m: {'PSNR': [], 'SSIM': [], 'CIEDE2000': [], 'Runtime': []}
           for m in methods_list}

    for name in names:
        for method in methods_list:
            if method in all_metrics[name]:
                agg[method]['PSNR'].append(all_metrics[name][method]['PSNR'])
                agg[method]['SSIM'].append(all_metrics[name][method]['SSIM'])
                agg[method]['CIEDE2000'].append(all_metrics[name][method]['CIEDE2000'])
            if method in all_runtimes[name]:
                agg[method]['Runtime'].append(all_runtimes[name][method])

    # Print summary table
    print("\n" + "=" * 90)
    print(f"{'Method':<15} {'PSNR (dB)':<14} {'SSIM':<14} {'CIEDE2000':<14} {'Runtime (ms)':<14}")
    print("-" * 90)
    for method in methods_list:
        psnr_mean = np.mean(agg[method]['PSNR']) if agg[method]['PSNR'] else 0
        ssim_mean = np.mean(agg[method]['SSIM']) if agg[method]['SSIM'] else 0
        ciede_mean = np.mean(agg[method]['CIEDE2000']) if agg[method]['CIEDE2000'] else 0
        rt_mean = np.mean(agg[method]['Runtime']) * 1000 if agg[method]['Runtime'] else 0
        print(f"{method:<15} {psnr_mean:<14.3f} {ssim_mean:<14.4f} {ciede_mean:<14.3f} {rt_mean:<14.2f}")
    print("=" * 90)

    # Step 5: Grid search for threshold optimization
    print("\n[5/6] Running hyperparameter grid search...")
    best_tc, best_tv, best_score, grid_results = grid_search_thresholds(
        images[:12],  # Use first 12 for optimization
        compute_ssim,
        tau_c_range=np.arange(20, 80, 10),
        tau_v_range=np.arange(1000, 4500, 500)
    )
    print(f"  Best thresholds: tau_c={best_tc:.1f}, tau_v={best_tv:.1f}, SSIM={best_score:.4f}")

    # Step 6: Generate figures
    print("\n[6/6] Generating figures...")
    os.makedirs(FIGURES_DIR, exist_ok=True)

    # Pipeline flowchart
    create_pipeline_flowchart(FIGURES_DIR)
    print("  Created pipeline flowchart")

    # Visual comparisons for selected images
    sample_indices = [0, 4, 8, 12, 16, 20] if len(images) > 20 else list(range(min(6, len(images))))
    for idx in sample_indices:
        if idx < len(images):
            key_methods = {k: all_results[names[idx]][k]
                          for k in ['CLAHE-RGB', 'CLAHE-HSI', 'ACSS']}
            plot_side_by_side(images[idx], key_methods, names[idx].replace('.png', ''),
                            FIGURES_DIR)
    print("  Created visual comparison figures")

    # Metric bar charts
    for metric in ['PSNR', 'SSIM', 'CIEDE2000']:
        key_methods = ['CLAHE-RGB', 'CLAHE-HSI', 'ACSS']
        metric_data = {m: agg[m][metric] for m in key_methods}
        plot_metrics_bar_chart(metric_data, metric, FIGURES_DIR)
    print("  Created metric bar charts")

    # Threshold heatmap
    plot_threshold_heatmap(grid_results, FIGURES_DIR)
    print("  Created threshold heatmap")

    # Per-image analysis
    rgb_psnr = agg['CLAHE-RGB']['PSNR']
    hsi_psnr = agg['CLAHE-HSI']['PSNR']
    acss_psnr = agg['ACSS']['PSNR']
    short_names = [n.replace('.png', '') for n in names]
    plot_per_image_analysis(short_names, rgb_psnr, hsi_psnr, acss_psnr,
                           'PSNR', FIGURES_DIR)

    rgb_ssim = agg['CLAHE-RGB']['SSIM']
    hsi_ssim = agg['CLAHE-HSI']['SSIM']
    acss_ssim = agg['ACSS']['SSIM']
    plot_per_image_analysis(short_names, rgb_ssim, hsi_ssim, acss_ssim,
                           'SSIM', FIGURES_DIR)
    print("  Created per-image analysis charts")

    # Save results to JSON
    results_data = {
        'methods': methods_list,
        'aggregated': {},
        'per_image': {},
        'grid_search': {
            'best_tau_c': float(best_tc),
            'best_tau_v': float(best_tv),
            'best_ssim': float(best_score),
        },
        'adaptive_selections': all_spaces,
        'image_features': {k: {fk: float(fv) for fk, fv in v.items()}
                          for k, v in all_features.items()},
    }

    for method in methods_list:
        results_data['aggregated'][method] = {
            'PSNR_mean': float(np.mean(agg[method]['PSNR'])),
            'PSNR_std': float(np.std(agg[method]['PSNR'])),
            'SSIM_mean': float(np.mean(agg[method]['SSIM'])),
            'SSIM_std': float(np.std(agg[method]['SSIM'])),
            'CIEDE2000_mean': float(np.mean(agg[method]['CIEDE2000'])),
            'CIEDE2000_std': float(np.std(agg[method]['CIEDE2000'])),
            'Runtime_mean_ms': float(np.mean(agg[method]['Runtime']) * 1000),
        }

    for name in names:
        results_data['per_image'][name] = {}
        for method in methods_list:
            if method in all_metrics[name]:
                results_data['per_image'][name][method] = {
                    k: float(v) for k, v in all_metrics[name][method].items()
                }

    results_path = os.path.join(RESULTS_DIR, 'experiment_results.json')
    with open(results_path, 'w') as f:
        json.dump(results_data, f, indent=2)
    print(f"\n  Results saved to {results_path}")

    print("\n" + "=" * 60)
    print("EXPERIMENT COMPLETE")
    print("=" * 60)

    return results_data


if __name__ == '__main__':
    run_full_experiment()
