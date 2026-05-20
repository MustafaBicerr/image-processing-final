"""
Visualization Module
====================
Generates figures and charts for the experimental results.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os


def plot_side_by_side(original, results_dict, image_name, save_dir):
    """
    Create side-by-side comparison of original and enhanced images.

    Parameters
    ----------
    original : ndarray
    results_dict : dict of {method_name: enhanced_image}
    image_name : str
    save_dir : str
    """
    n = len(results_dict) + 1
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 4))

    axes[0].imshow(original)
    axes[0].set_title('Original', fontsize=10, fontweight='bold')
    axes[0].axis('off')

    for i, (name, img) in enumerate(results_dict.items(), 1):
        axes[i].imshow(img)
        axes[i].set_title(name, fontsize=10, fontweight='bold')
        axes[i].axis('off')

    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f'comparison_{image_name}.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return path


def plot_metrics_bar_chart(metrics_df, metric_name, save_dir):
    """
    Create a grouped bar chart for a specific metric across methods.

    Parameters
    ----------
    metrics_df : dict of {method_name: list_of_values}
    metric_name : str
    save_dir : str
    """
    methods = list(metrics_df.keys())
    means = [np.mean(v) for v in metrics_df.values()]
    stds = [np.std(v) for v in metrics_df.values()]

    colors = ['#2196F3', '#FF5722', '#4CAF50', '#9C27B0', '#FF9800', '#607D8B']

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(methods, means, yerr=stds, capsize=5,
                  color=colors[:len(methods)], edgecolor='white', linewidth=1.2)
    ax.set_ylabel(metric_name, fontsize=12, fontweight='bold')
    ax.set_title(f'{metric_name} Comparison Across Methods', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.01,
                f'{mean:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f'{metric_name.lower().replace(" ", "_")}_comparison.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return path


def plot_threshold_heatmap(results, save_dir):
    """
    Plot heatmap of grid search results for threshold optimization.

    Parameters
    ----------
    results : list of dict with keys 'tau_c', 'tau_v', 'score'
    save_dir : str
    """
    tau_c_vals = sorted(set(r['tau_c'] for r in results))
    tau_v_vals = sorted(set(r['tau_v'] for r in results))

    score_matrix = np.zeros((len(tau_v_vals), len(tau_c_vals)))
    for r in results:
        i = tau_v_vals.index(r['tau_v'])
        j = tau_c_vals.index(r['tau_c'])
        score_matrix[i, j] = r['score']

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(score_matrix, cmap='viridis', aspect='auto',
                   origin='lower')
    ax.set_xticks(range(len(tau_c_vals)))
    ax.set_xticklabels([f'{v:.0f}' for v in tau_c_vals])
    ax.set_yticks(range(len(tau_v_vals)))
    ax.set_yticklabels([f'{v:.0f}' for v in tau_v_vals])
    ax.set_xlabel('Colorfulness Threshold (τ_c)', fontsize=12)
    ax.set_ylabel('Intensity Variance Threshold (τ_v)', fontsize=12)
    ax.set_title('Hyperparameter Grid Search Results (SSIM)', fontsize=14, fontweight='bold')
    plt.colorbar(im, ax=ax, label='Mean SSIM')

    # Mark best
    best = max(results, key=lambda r: r['score'])
    bi = tau_v_vals.index(best['tau_v'])
    bj = tau_c_vals.index(best['tau_c'])
    ax.plot(bj, bi, 'r*', markersize=20)

    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, 'threshold_heatmap.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return path


def plot_per_image_analysis(image_names, rgb_scores, hsi_scores, adaptive_scores,
                            metric_name, save_dir):
    """Plot per-image metric comparison across three methods."""
    x = np.arange(len(image_names))
    width = 0.25

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(x - width, rgb_scores, width, label='CLAHE-RGB', color='#2196F3')
    ax.bar(x, hsi_scores, width, label='CLAHE-HSI', color='#FF5722')
    ax.bar(x + width, adaptive_scores, width, label='ACSS (Proposed)', color='#4CAF50')

    ax.set_xlabel('Image', fontsize=12)
    ax.set_ylabel(metric_name, fontsize=12)
    ax.set_title(f'Per-Image {metric_name} Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(image_names, rotation=45, ha='right', fontsize=8)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f'per_image_{metric_name.lower()}.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return path


def create_pipeline_flowchart(save_dir):
    """Create a simple pipeline flowchart using matplotlib."""
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4)
    ax.axis('off')

    boxes = [
        (1, 2, 'Input\nImage'),
        (3.5, 2, 'Feature\nExtraction'),
        (6, 2, 'Decision\nRule'),
        (8.5, 3, 'HSI\nEnhancement'),
        (8.5, 1, 'RGB\nEnhancement'),
        (11, 2, 'Output\nImage'),
    ]

    for x, y, text in boxes:
        color = '#4CAF50' if 'Decision' in text else '#2196F3'
        if 'HSI' in text:
            color = '#FF5722'
        elif 'RGB' in text:
            color = '#9C27B0'
        bbox = dict(boxstyle='round,pad=0.4', facecolor=color, alpha=0.8, edgecolor='white')
        ax.text(x, y, text, fontsize=11, ha='center', va='center',
                bbox=bbox, color='white', fontweight='bold')

    # Arrows
    arrow_props = dict(arrowstyle='->', color='gray', lw=2)
    ax.annotate('', xy=(2.8, 2), xytext=(1.8, 2), arrowprops=arrow_props)
    ax.annotate('', xy=(5.2, 2), xytext=(4.3, 2), arrowprops=arrow_props)
    ax.annotate('', xy=(7.8, 3), xytext=(6.8, 2.3), arrowprops=arrow_props)
    ax.annotate('', xy=(7.8, 1), xytext=(6.8, 1.7), arrowprops=arrow_props)
    ax.annotate('', xy=(10.2, 2.3), xytext=(9.3, 3), arrowprops=arrow_props)
    ax.annotate('', xy=(10.2, 1.7), xytext=(9.3, 1), arrowprops=arrow_props)

    # Labels on decision arrows
    ax.text(7.3, 2.8, 'High color\nLow contrast', fontsize=7, ha='center', color='gray')
    ax.text(7.3, 1.2, 'Otherwise', fontsize=7, ha='center', color='gray')

    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, 'pipeline_flowchart.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return path
