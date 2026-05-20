"""
Image Enhancement Module
=========================
Implements enhancement operations in different color spaces.

Supported methods:
    - CLAHE (Contrast Limited Adaptive Histogram Equalization)
    - Global Histogram Equalization
    - Gamma Correction

Each method can operate in RGB or HSI space.
"""

import numpy as np
import cv2
from .color_spaces import rgb_to_hsi, hsi_to_rgb


def apply_clahe_rgb(image, clip_limit=2.0, tile_grid_size=(8, 8)):
    """
    Apply CLAHE independently to each RGB channel.

    This approach treats each color channel as a separate grayscale image.
    While simple, it can introduce color shifts since luminance and
    chrominance are coupled in RGB space.

    Parameters
    ----------
    image : ndarray, shape (H, W, 3), dtype uint8
        Input RGB image.
    clip_limit : float
        Threshold for contrast limiting in CLAHE.
    tile_grid_size : tuple of int
        Size of the grid for histogram equalization.

    Returns
    -------
    enhanced : ndarray, shape (H, W, 3), dtype uint8
        Enhanced RGB image.
    """
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    channels = cv2.split(image)
    enhanced_channels = [clahe.apply(ch) for ch in channels]
    enhanced = cv2.merge(enhanced_channels)
    return enhanced


def apply_clahe_hsi(image, clip_limit=2.0, tile_grid_size=(8, 8)):
    """
    Apply CLAHE to the Intensity channel in HSI space.

    By converting to HSI and enhancing only the intensity component,
    this method preserves hue and saturation, avoiding color distortions
    that are common with direct RGB enhancement.

    Parameters
    ----------
    image : ndarray, shape (H, W, 3), dtype uint8
        Input RGB image.
    clip_limit : float
        Threshold for contrast limiting in CLAHE.
    tile_grid_size : tuple of int
        Size of the grid for histogram equalization.

    Returns
    -------
    enhanced : ndarray, shape (H, W, 3), dtype uint8
        Enhanced RGB image (converted back from HSI).
    """
    hsi = rgb_to_hsi(image)

    # Scale intensity to 0-255 for CLAHE
    intensity = (hsi[:, :, 2] * 255.0).astype(np.uint8)

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    enhanced_intensity = clahe.apply(intensity)

    # Put enhanced intensity back
    hsi[:, :, 2] = enhanced_intensity.astype(np.float64) / 255.0

    enhanced = hsi_to_rgb(hsi)
    return enhanced


def apply_histogram_equalization_rgb(image):
    """
    Apply global histogram equalization to each RGB channel independently.

    Parameters
    ----------
    image : ndarray, shape (H, W, 3), dtype uint8

    Returns
    -------
    enhanced : ndarray, shape (H, W, 3), dtype uint8
    """
    channels = cv2.split(image)
    enhanced_channels = [cv2.equalizeHist(ch) for ch in channels]
    enhanced = cv2.merge(enhanced_channels)
    return enhanced


def apply_histogram_equalization_hsi(image):
    """
    Apply global histogram equalization to the Intensity channel in HSI space.

    Parameters
    ----------
    image : ndarray, shape (H, W, 3), dtype uint8

    Returns
    -------
    enhanced : ndarray, shape (H, W, 3), dtype uint8
    """
    hsi = rgb_to_hsi(image)

    intensity = (hsi[:, :, 2] * 255.0).astype(np.uint8)
    enhanced_intensity = cv2.equalizeHist(intensity)
    hsi[:, :, 2] = enhanced_intensity.astype(np.float64) / 255.0

    enhanced = hsi_to_rgb(hsi)
    return enhanced


def apply_gamma_correction_rgb(image, gamma=1.0):
    """
    Apply gamma correction to each RGB channel.

    The gamma transformation is defined as:
        s = c * r^gamma
    where r is the input pixel value (normalized), s is the output,
    and c is a scaling constant (typically 1).

    Parameters
    ----------
    image : ndarray, shape (H, W, 3), dtype uint8
    gamma : float
        Gamma value. gamma < 1 brightens, gamma > 1 darkens.

    Returns
    -------
    enhanced : ndarray, shape (H, W, 3), dtype uint8
    """
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255
                      for i in np.arange(0, 256)]).astype(np.uint8)
    enhanced = cv2.LUT(image, table)
    return enhanced


def apply_gamma_correction_hsi(image, gamma=1.0):
    """
    Apply gamma correction to the Intensity channel in HSI space.

    Parameters
    ----------
    image : ndarray, shape (H, W, 3), dtype uint8
    gamma : float

    Returns
    -------
    enhanced : ndarray, shape (H, W, 3), dtype uint8
    """
    hsi = rgb_to_hsi(image)

    intensity = hsi[:, :, 2]
    intensity = np.clip(intensity, 0, 1)
    inv_gamma = 1.0 / gamma
    enhanced_intensity = np.power(intensity, inv_gamma)
    hsi[:, :, 2] = enhanced_intensity

    enhanced = hsi_to_rgb(hsi)
    return enhanced


# Registry of all enhancement methods for easy iteration
ENHANCEMENT_METHODS = {
    'CLAHE_RGB': apply_clahe_rgb,
    'CLAHE_HSI': apply_clahe_hsi,
    'HE_RGB': apply_histogram_equalization_rgb,
    'HE_HSI': apply_histogram_equalization_hsi,
    'Gamma_RGB': lambda img: apply_gamma_correction_rgb(img, gamma=0.7),
    'Gamma_HSI': lambda img: apply_gamma_correction_hsi(img, gamma=0.7),
}
