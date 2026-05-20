"""
Color Space Conversion Module
=============================
Provides conversion functions between RGB, HSI, and HSV color spaces.

References:
    - Gonzalez & Woods, "Digital Image Processing", 4th Edition
    - Koschan & Abidi, "Digital Color Image Processing", Wiley, 2008
"""

import numpy as np


def rgb_to_hsi(image):
    """
    Convert an RGB image to HSI color space.

    The HSI (Hue-Saturation-Intensity) model separates color information
    from intensity, enabling enhancement of brightness without affecting
    chrominance.

    Parameters
    ----------
    image : ndarray, shape (H, W, 3), dtype uint8 or float64
        Input RGB image. If uint8, values are in [0, 255].

    Returns
    -------
    hsi : ndarray, shape (H, W, 3), dtype float64
        HSI image with H in [0, 2*pi], S in [0, 1], I in [0, 1].
    """
    img = image.astype(np.float64) / 255.0 if image.dtype == np.uint8 else image.astype(np.float64)

    R = img[:, :, 0]
    G = img[:, :, 1]
    B = img[:, :, 2]

    # Intensity
    I = (R + G + B) / 3.0

    # Saturation
    min_rgb = np.minimum(np.minimum(R, G), B)
    S = np.where(I > 0, 1.0 - min_rgb / (I + 1e-10), 0.0)

    # Hue
    numerator = 0.5 * ((R - G) + (R - B))
    denominator = np.sqrt((R - G) ** 2 + (R - B) * (G - B) + 1e-10)
    theta = np.arccos(np.clip(numerator / (denominator + 1e-10), -1.0, 1.0))

    H = np.where(B <= G, theta, 2.0 * np.pi - theta)

    hsi = np.stack([H, S, I], axis=2)
    return hsi


def hsi_to_rgb(hsi):
    """
    Convert an HSI image back to RGB color space.

    Parameters
    ----------
    hsi : ndarray, shape (H, W, 3), dtype float64
        HSI image with H in [0, 2*pi], S in [0, 1], I in [0, 1].

    Returns
    -------
    rgb : ndarray, shape (H, W, 3), dtype uint8
        Output RGB image with values in [0, 255].
    """
    H = hsi[:, :, 0]
    S = hsi[:, :, 1]
    I = hsi[:, :, 2]

    R = np.zeros_like(H)
    G = np.zeros_like(H)
    B = np.zeros_like(H)

    # Sector 1: 0 <= H < 2*pi/3
    mask1 = (H >= 0) & (H < 2.0 * np.pi / 3.0)
    B[mask1] = I[mask1] * (1.0 - S[mask1])
    R[mask1] = I[mask1] * (1.0 + S[mask1] * np.cos(H[mask1]) / (np.cos(np.pi / 3.0 - H[mask1]) + 1e-10))
    G[mask1] = 3.0 * I[mask1] - (R[mask1] + B[mask1])

    # Sector 2: 2*pi/3 <= H < 4*pi/3
    mask2 = (H >= 2.0 * np.pi / 3.0) & (H < 4.0 * np.pi / 3.0)
    H2 = H[mask2] - 2.0 * np.pi / 3.0
    R[mask2] = I[mask2] * (1.0 - S[mask2])
    G[mask2] = I[mask2] * (1.0 + S[mask2] * np.cos(H2) / (np.cos(np.pi / 3.0 - H2) + 1e-10))
    B[mask2] = 3.0 * I[mask2] - (R[mask2] + G[mask2])

    # Sector 3: 4*pi/3 <= H < 2*pi
    mask3 = (H >= 4.0 * np.pi / 3.0) & (H <= 2.0 * np.pi)
    H3 = H[mask3] - 4.0 * np.pi / 3.0
    G[mask3] = I[mask3] * (1.0 - S[mask3])
    B[mask3] = I[mask3] * (1.0 + S[mask3] * np.cos(H3) / (np.cos(np.pi / 3.0 - H3) + 1e-10))
    R[mask3] = 3.0 * I[mask3] - (G[mask3] + B[mask3])

    rgb = np.stack([R, G, B], axis=2)
    rgb = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    return rgb


def rgb_to_hsv(image):
    """
    Convert RGB image to HSV using OpenCV convention.

    Parameters
    ----------
    image : ndarray, shape (H, W, 3), dtype uint8

    Returns
    -------
    hsv : ndarray, shape (H, W, 3), dtype float64
        H in [0, 360], S in [0, 1], V in [0, 1].
    """
    import cv2
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float64)
    hsv[:, :, 0] = hsv[:, :, 0] * 2.0  # OpenCV H is 0-180, convert to 0-360
    hsv[:, :, 1] = hsv[:, :, 1] / 255.0
    hsv[:, :, 2] = hsv[:, :, 2] / 255.0
    return hsv


def hsv_to_rgb(hsv):
    """
    Convert HSV image back to RGB.

    Parameters
    ----------
    hsv : ndarray, shape (H, W, 3), dtype float64
        H in [0, 360], S in [0, 1], V in [0, 1].

    Returns
    -------
    rgb : ndarray, shape (H, W, 3), dtype uint8
    """
    import cv2
    hsv_cv = np.zeros_like(hsv)
    hsv_cv[:, :, 0] = hsv[:, :, 0] / 2.0  # Back to 0-180
    hsv_cv[:, :, 1] = hsv[:, :, 1] * 255.0
    hsv_cv[:, :, 2] = hsv[:, :, 2] * 255.0
    hsv_cv = hsv_cv.astype(np.uint8)
    rgb = cv2.cvtColor(hsv_cv, cv2.COLOR_HSV2RGB)
    return rgb
