# Adaptive Color Space Selection for Image Enhancement

A comparative study of RGB and HSI color representations for image enhancement, with an adaptive selection framework.

## Overview

This project investigates the performance differences between RGB and HSI (Hue-Saturation-Intensity) color spaces when applying image enhancement operations. We propose an **Adaptive Color Space Selection (ACSS)** method that automatically determines the optimal color space for enhancement based on image characteristics.

## Key Features

- **RGB-to-HSI and HSI-to-RGB** color space conversion
- **CLAHE** (Contrast Limited Adaptive Histogram Equalization) in both RGB and HSI spaces
- **Histogram Equalization** and **Gamma Correction** baselines
- **Adaptive Color Space Selection** using image features (colorfulness, intensity variance)
- **Hyperparameter optimization** via grid search
- Comprehensive evaluation using **PSNR**, **SSIM**, and **CIEDE2000** metrics

## Project Structure

```
├── src/
│   ├── __init__.py
│   ├── color_spaces.py        # RGB/HSI/HSV conversion functions
│   ├── enhancement.py         # CLAHE, HE, Gamma enhancement methods
│   ├── adaptive_selector.py   # ACSS adaptive selection logic
│   ├── metrics.py             # PSNR, SSIM, CIEDE2000, image features
│   ├── visualization.py       # Figure and chart generation
│   └── experiments.py         # Main experiment runner
├── data/                      # Kodak dataset (auto-downloaded)
├── results/
│   ├── figures/               # Generated comparison figures
│   └── experiment_results.json
├── requirements.txt
└── README.md
```

## Installation

```bash
git clone https://github.com/MustafaBicerr/image-processing-final.git
cd image-processing-final
pip install -r requirements.txt
```

## Usage

### Run Full Experiment

```bash
python -m src.experiments
```

This will:
1. Download the Kodak Lossless True Color Image Suite (24 images)
2. Apply all enhancement methods (CLAHE, HE, Gamma in both RGB and HSI)
3. Run the proposed ACSS adaptive method
4. Compute quality metrics (PSNR, SSIM, CIEDE2000)
5. Perform hyperparameter grid search
6. Generate comparison figures and result tables

### Use Individual Components

```python
from src.color_spaces import rgb_to_hsi, hsi_to_rgb
from src.enhancement import apply_clahe_rgb, apply_clahe_hsi
from src.adaptive_selector import adaptive_enhance

import cv2

# Load image
img = cv2.imread('image.png')
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# Adaptive enhancement
enhanced, selected_space, features = adaptive_enhance(img)
print(f"Selected color space: {selected_space}")
```

## Method

The ACSS method extracts the following features from each input image:
- **Colorfulness** (Hasler & Süsstrunk, 2003)
- **Intensity Variance**
- **Contrast Ratio**
- **Mean Saturation**

A threshold-based decision rule selects the color space:
- If `colorfulness > τ_c` AND `intensity_variance < τ_v` → **HSI** enhancement
- Otherwise → **RGB** enhancement

Thresholds are optimized via grid search on a validation set.

## Dataset

**Kodak Lossless True Color Image Suite** — 24 high-quality natural images at 768×512 resolution.

## Results

Results are saved in `results/experiment_results.json` and visual comparisons in `results/figures/`.

## Author

**Mustafa Biçer** — Abdullah Gül University  
Course: Image Processing Term Project

## License

This project is released for academic purposes.
