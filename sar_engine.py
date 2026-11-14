"""Computation helpers for Dancing with the SARs.

Synthetic surfaces are *teaching illustrations*, never NISAR observations.
Numerical CSV analysis is valid only for user-supplied aligned and calibrated data.
"""
from __future__ import annotations

from io import BytesIO
import hashlib
import numpy as np
import pandas as pd
from PIL import Image

LOCATIONS = {
    "Abu Dhabi coast, UAE": (24.46, 54.37, "Coastal flooding / wetlands"),
    "Amazon rainforest, Brazil": (-3.12, -60.02, "Forest disturbance"),
    "Jakarta, Indonesia": (-6.20, 106.82, "Ground movement"),
    "Greenland ice sheet": (69.22, -49.84, "Ice change"),
    "Bangladesh delta": (22.35, 90.25, "Flooding"),
    "Central California, USA": (37.75, -121.4, "Ground movement / agriculture"),
    "South Africa farmland": (-29.0, 25.0, "Agriculture / vegetation"),
    "Himalayan glaciers, Nepal": (28.5, 84.0, "Glacier change"),
}
CHANGES = {
    "🌊 Flooding": {
        "hint": "Open water often returns weaker radar signals; flooded vegetation can be brighter because of double-bounce scattering.",
        "question": "Where do new dark or bright patches appear, and could geometry or moisture explain them?",
        "reality": "Flood extent cannot be proven from an uncalibrated image difference alone.",
    },
    "🌳 Forest loss": {
        "hint": "Vegetation structure influences L-band backscatter and coherence. A decrease does not always mean deforestation.",
        "question": "Are the changes confined to vegetation, and can you rule out seasonal moisture or viewing differences?",
        "reality": "Forest loss needs suitable reference data and multitemporal interpretation.",
    },
    "🏙️ Ground movement": {
        "hint": "Subtle ground displacement is measured using interferometric phase, not by subtracting ordinary image brightness.",
        "question": "Would paired, co-registered SLC observations and interferometric processing be needed here?",
        "reality": "This demo does not measure displacement in centimeters or millimeters.",
    },
    "🧊 Ice change": {
        "hint": "Ice texture, liquid water, and surface roughness can change radar returns; ice velocity needs specialized tracking.",
        "question": "Could changes in meltwater, surface texture, or motion explain the radar pattern?",
        "reality": "Radar brightness difference alone is not a melt-rate measurement.",
    },
}


def _seed(*items):
    raw = '|'.join(map(str, items)).encode('utf-8')
    return int.from_bytes(hashlib.sha256(raw).digest()[:4], 'big')


def make_demo(location: str, change_type: str, day_gap: int, shape=(168, 224)):
    """Return simulated before and after brightness *in illustrative dB units*.
    Dates control an illustrative effect magnitude; nothing is fetched from a satellite.
    """
    rng = np.random.default_rng(_seed(location, change_type, 'sar_demo_v3'))
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx - w / 2) / (w / 2)
    ny = (yy - h / 2) / (h / 2)
    texture = rng.normal(0, 1.5, size=shape)
    # Speckle-like texture plus broad spatial variation.
    before = -13 + 2.6 * np.sin(xx / 15) + 1.7 * np.cos(yy / 13) + texture
    before = np.clip(before, -28, 2)
    strength = 0.5 + 0.6 * min(max(day_gap, 1), 180) / 180
    blob1 = np.exp(-(((nx + .24) / .43)**2 + ((ny - .12) / .34)**2) * 2.1)
    blob2 = np.exp(-(((nx - .45) / .30)**2 + ((ny + .33) / .40)**2) * 1.8)
    irregular = np.sin(8 * nx + 4 * ny) * np.cos(5 * ny - 2 * nx)
    if 'Flood' in change_type:
        delta = -9 * strength * blob1 - 5 * strength * blob2 + 1.4 * irregular * blob1
    elif 'Forest' in change_type:
        block = (np.abs(nx + .12) < .46) & (np.abs(ny - .1) < .47)
        delta = -6.0 * strength * block * (0.55 + 0.45 * blob1) + .7 * irregular
    elif 'Ground' in change_type:
        delta = 3.1 * strength * np.sin((nx + ny) * 12) * (blob1 + .7 * blob2)
    else:
        delta = 5.2 * strength * (blob1 - .72 * blob2) + 0.8 * irregular
    after = np.clip(before + delta + rng.normal(0, 0.5, shape), -30, 4)
    return before.astype('float32'), after.astype('float32')


def sar_gray(arr):
    arr = np.nan_to_num(arr, nan=-20.0, posinf=4, neginf=-30)
    norm = np.clip((arr + 28) / 32, 0, 1) ** .7
    g = (norm * 230 + 12).astype(np.uint8)
    rgb = np.stack([g, (g*.97).astype(np.uint8), (g*.86).astype(np.uint8)], axis=-1)
    return Image.fromarray(rgb, 'RGB')


def change_heatmap(before, after, threshold=3.0):
    diff = after - before
    scaled = np.clip(np.abs(diff) / max(8.0, threshold * 2), 0, 1)
    pos = diff >= 0
    # Positive: cyan/teal. Negative: copper/orange. Background: navy.
    out = np.zeros((*diff.shape, 3), dtype=np.float32)
    out[:] = [21, 38, 64]
    color_positive = np.array([42, 210, 194])
    color_negative = np.array([253, 154, 99])
    out = out * (1-scaled[..., None]) + np.where(pos[..., None], color_positive, color_negative) * scaled[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype('uint8'), 'RGB')


def img_bytes(img):
    b = BytesIO();img.save(b, format='PNG');return b.getvalue()


def analyze_aligned_csv(raw: bytes, threshold: float):
    """Compare user supplied, already co-registered calibrated backscatter in dB.
    Requires row, col, before_db, after_db. Does not infer physical land change.
    """
    df = pd.read_csv(BytesIO(raw))
    required = ['row', 'col', 'before_db', 'after_db']
    missing = [x for x in required if x not in df.columns]
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(missing) + '. Use the included CSV template.')
    if len(df) == 0 or len(df) > 300000:
        raise ValueError('File must contain between 1 and 300,000 rows.')
    for col in required:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=required).copy()
    if df.empty:
        raise ValueError('No valid numerical rows found.')
    if (df['row'] < 0).any() or (df['col'] < 0).any():
        raise ValueError('row and col must be nonnegative.')
    if (df['row'] % 1 != 0).any() or (df['col'] % 1 != 0).any():
        raise ValueError('row and col must be integer grid indices.')
    df['row'] = df['row'].astype(int);df['col'] = df['col'].astype(int)
    if df.duplicated(['row','col']).any():
        raise ValueError('Duplicate pixel locations found in row/col coordinates.')
    df['delta_db'] = df['after_db'] - df['before_db']
    df['abs_change_ge_threshold'] = df['delta_db'].abs() >= threshold
    return df


def matrix_from_csv(df):
    h = int(df['row'].max())+1
    w = int(df['col'].max())+1
    if h*w > 1_000_000:
        raise ValueError('Grid dimensions too large to render. Reduce row/col range.')
    bef = np.full((h, w), np.nan)
    aft = np.full((h, w), np.nan)
    bef[df['row'].to_numpy(), df['col'].to_numpy()] = df['before_db'].to_numpy()
    aft[df['row'].to_numpy(), df['col'].to_numpy()] = df['after_db'].to_numpy()
    return bef, aft


def demo_csv():
    before, after = make_demo('South Africa farmland','🌳 Forest loss',80,shape=(40,50))
    rows, cols = np.indices(before.shape)
    return pd.DataFrame({'row':rows.ravel(),'col':cols.ravel(),'before_db':before.ravel().round(3),'after_db':after.ravel().round(3)}).to_csv(index=False).encode('utf-8')


def align_visual_pair(before, after, size=(280,200)):
    """Convert arbitrary illustrative/uploaded screenshots for a visual-only comparison."""
    b=Image.open(BytesIO(before)).convert('L').resize(size, Image.Resampling.BILINEAR)
    a=Image.open(BytesIO(after)).convert('L').resize(size, Image.Resampling.BILINEAR)
    x = np.asarray(b,dtype=float); y = np.asarray(a,dtype=float)
    diff = np.abs(y-x)
    out=np.zeros((*x.shape,3),dtype=np.uint8)
    strength=np.clip(diff*3,0,255).astype('uint8')
    out[...,0]=strength
    out[...,1]=(strength*.62).astype('uint8')
    out[...,2]=(strength*.14).astype('uint8')
    return b,a,Image.fromarray(out, 'RGB'), float(np.mean(diff))
