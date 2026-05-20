"""
Adaptive Color Space Selector
==============================
Implements the ACSS (Adaptive Color Space Selection) method that
automatically determines the optimal color space for image enhancement
based on image characteristics.

Decision Rule:
    If colorfulness > tau_c AND intensity_variance < tau_v:
        -> Use HSI space (high color content, low contrast -> preserve colors)
    Else:
        -> Use RGB space (simpler, effective for low-color or high-contrast)

Default thresholds determined via grid search optimization on Kodak dataset.
"""

import numpy as np
from .metrics import (compute_colorfulness, compute_intensity_variance,
                      compute_contrast_ratio, compute_saturation_mean)
from .enhancement import apply_clahe_rgb, apply_clahe_hsi


# Default thresholds (optimized via grid search)
DEFAULT_TAU_C = 40.0   # Colorfulness threshold
DEFAULT_TAU_V = 2500.0  # Intensity variance threshold


def extract_features(image):
    """
    Extract image features used for adaptive color space selection.

    Parameters
    ----------
    image : ndarray, shape (H, W, 3), dtype uint8

    Returns
    -------
    dict with keys: colorfulness, intensity_variance, contrast_ratio, saturation_mean
    """
    return {
        'colorfulness': compute_colorfulness(image),
        'intensity_variance': compute_intensity_variance(image),
        'contrast_ratio': compute_contrast_ratio(image),
        'saturation_mean': compute_saturation_mean(image),
    }


def select_color_space(features, tau_c=DEFAULT_TAU_C, tau_v=DEFAULT_TAU_V):
    """
    Determine the optimal color space based on image features.

    Decision Logic:
        - High colorfulness (> tau_c) AND low intensity variance (< tau_v):
          Image has rich colors but low contrast -> HSI enhancement preserves
          colors while improving contrast.
        - Otherwise: RGB enhancement is simpler and effective.

    Parameters
    ----------
    features : dict
        Image features from extract_features().
    tau_c : float
        Colorfulness threshold.
    tau_v : float
        Intensity variance threshold.

    Returns
    -------
    str : 'HSI' or 'RGB'
    """
    if features['colorfulness'] > tau_c and features['intensity_variance'] < tau_v:
        return 'HSI'
    else:
        return 'RGB'


def adaptive_enhance(image, clip_limit=2.0, tile_grid_size=(8, 8),
                     tau_c=DEFAULT_TAU_C, tau_v=DEFAULT_TAU_V):
    """
    Adaptively enhance an image by selecting the optimal color space.

    Parameters
    ----------
    image : ndarray, shape (H, W, 3), dtype uint8
    clip_limit : float
        CLAHE clip limit.
    tile_grid_size : tuple
        CLAHE tile grid size.
    tau_c : float
        Colorfulness threshold.
    tau_v : float
        Intensity variance threshold.

    Returns
    -------
    enhanced : ndarray, shape (H, W, 3), dtype uint8
    selected_space : str, 'HSI' or 'RGB'
    features : dict
    """
    features = extract_features(image)
    selected_space = select_color_space(features, tau_c, tau_v)

    if selected_space == 'HSI':
        enhanced = apply_clahe_hsi(image, clip_limit, tile_grid_size)
    else:
        enhanced = apply_clahe_rgb(image, clip_limit, tile_grid_size)

    return enhanced, selected_space, features


def grid_search_thresholds(images, reference_metric_func,
                           tau_c_range=None, tau_v_range=None,
                           clip_limit=2.0):
    """
    Perform grid search to find optimal thresholds for ACSS.

    Parameters
    ----------
    images : list of ndarray
        Input images.
    reference_metric_func : callable
        Function(original, enhanced) -> float (higher is better).
    tau_c_range : array-like
        Range of colorfulness thresholds to test.
    tau_v_range : array-like
        Range of intensity variance thresholds to test.
    clip_limit : float
        CLAHE clip limit.

    Returns
    -------
    best_tau_c : float
    best_tau_v : float
    best_score : float
    all_results : list of dict
    """
    if tau_c_range is None:
        tau_c_range = np.arange(20, 80, 10)
    if tau_v_range is None:
        tau_v_range = np.arange(1000, 4500, 500)

    best_score = -np.inf
    best_tau_c, best_tau_v = DEFAULT_TAU_C, DEFAULT_TAU_V
    all_results = []

    for tc in tau_c_range:
        for tv in tau_v_range:
            scores = []
            for img in images:
                enhanced, _, _ = adaptive_enhance(img, clip_limit=clip_limit,
                                                   tau_c=tc, tau_v=tv)
                score = reference_metric_func(img, enhanced)
                scores.append(score)
            mean_score = np.mean(scores)
            all_results.append({'tau_c': tc, 'tau_v': tv, 'score': mean_score})
            if mean_score > best_score:
                best_score = mean_score
                best_tau_c, best_tau_v = tc, tv

    return best_tau_c, best_tau_v, best_score, all_results
