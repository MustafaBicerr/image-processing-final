"""
Image Quality Metrics Module
=============================
Provides objective quality metrics for comparing original and enhanced images.
"""

import numpy as np
from skimage.metrics import peak_signal_noise_ratio, structural_similarity
import time
from functools import wraps


def compute_psnr(original, enhanced):
    """Compute Peak Signal-to-Noise Ratio (dB)."""
    return peak_signal_noise_ratio(original, enhanced)


def compute_ssim(original, enhanced):
    """Compute Structural Similarity Index."""
    if len(original.shape) == 3:
        return structural_similarity(original, enhanced, channel_axis=2)
    return structural_similarity(original, enhanced)


def compute_ciede2000(original, enhanced):
    """Compute mean CIEDE2000 perceptual color difference."""
    from skimage.color import rgb2lab, deltaE_ciede2000
    lab1 = rgb2lab(original)
    lab2 = rgb2lab(enhanced)
    return np.mean(deltaE_ciede2000(lab1, lab2))


def compute_colorfulness(image):
    """
    Colorfulness metric (Hasler & Susstrunk, 2003).
    DOI: 10.1117/12.477378
    """
    img = image.astype(np.float64)
    R, G, B = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    rg = R - G
    yb = 0.5 * (R + G) - B
    sigma_rg, sigma_yb = np.std(rg), np.std(yb)
    mu_rg, mu_yb = np.mean(rg), np.mean(yb)
    return np.sqrt(sigma_rg**2 + sigma_yb**2) + 0.3 * np.sqrt(mu_rg**2 + mu_yb**2)


def compute_intensity_variance(image):
    """Compute variance of grayscale intensities."""
    import cv2
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return np.var(gray.astype(np.float64))


def compute_contrast_ratio(image):
    """Compute global contrast ratio using 5th/95th percentiles."""
    import cv2
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float64)
    p5 = np.percentile(gray, 5)
    p95 = np.percentile(gray, 95)
    return (p95 - p5) / (p95 + p5 + 1e-10)


def compute_saturation_mean(image):
    """Compute mean saturation in HSV space."""
    import cv2
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    return np.mean(hsv[:, :, 1].astype(np.float64) / 255.0)


def measure_runtime(func):
    """Decorator that returns (result, elapsed_seconds)."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        return result, elapsed
    return wrapper
