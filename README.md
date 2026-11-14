# Dancing with SARs — NISAR Earth Change Explorer

**An interactive Grade 11 ICT / NASA Space Apps 2026 research prototype** for the official **Dancing with the SARs** challenge.

This project teaches Synthetic Aperture Radar (SAR), helps researchers discover available NISAR acquisition metadata, demonstrates before/after concepts, and compares **user-supplied aligned radar backscatter grids**. It does **not** automatically convert raw NISAR HDF5 granules into displacement or flood maps.

## What is included

- **Explore Earth** — 8 world locations plus custom latitude/longitude; four surface-change investigations; interactive map; observation dates; clear *simulated* before/after previews and change heatmap
- **Live NISAR catalog lookup** — search for matching NISAR GCOV granule metadata via the publicly documented NASA ASF Search API; the internet connection must be working
- **Compare Data** — upload preprocessed co-registered calibrated backscatter values as a CSV; inspect before/after images and compute differences in dB; download analysis. Alternatively, compare two pictures visually (non-quantitative)
- **Radar Learning** — accessible learning cards about SAR, NISAR, backscatter, coherence and InSAR; self-check quiz
- **Research Notebook** — record evidence, possible causes and scientific limitations; export notes as Markdown/JSON
- **NASA Resources** — links to official mission and data access documentation
- **High-contrast, responsive design** — designed for phone and laptop browsers

## Run on Windows

1. Extract this ZIP. Keep `app.py`, `sar_engine.py`, `requirements.txt`, `.streamlit/`, and `assets/` together.
2. Open the folder in File Explorer, click the **address bar**, type `cmd`, press Enter.
3. Run:

```bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

4. It will open in your browser, usually at `http://localhost:8501`.

If Python is not recognized, install it from https://www.python.org/downloads/ and try again.

## Deploy online from GitHub to Streamlit Community Cloud

1. Create a **public** GitHub repository, e.g. `dancing-with-sars-nisar`.
2. Upload the **extracted contents**, not the ZIP. Make sure `.streamlit/config.toml` remains inside `.streamlit/` and `assets/radar_hero.svg` inside `assets/`.
3. Visit https://share.streamlit.io/ and create an app from GitHub.
4. Choose your repository; branch `main`; main file path `app.py`.
5. Click **Deploy** and test the public URL in a private/incognito tab.

On Samsung/Android, open the public app in Chrome and choose **⋮ → Add to Home screen**. On iPhone, use Safari's Share menu → **Add to Home Screen**. This is a mobile-friendly **web app shortcut**, not a native Android APK.

## Important: demonstration vs measured observations

- The maps under **Explore Earth** are **synthetic teaching simulations**, not NISAR acquisitions. The chosen dates only affect the synthetic signal amplitude. The simulated pixel values should not be cited as NASA measurements.
- The **Live ASF catalog** returns actual *catalog records*, if matching products exist and the API is available. It does **not** return processed pairs or prove a change.
- The **numeric CSV** upload is for **existing processed grids**. The app assumes the `before_db` and `after_db` columns contain compatible, calibrated, aligned values. An arbitrary photograph or uncalibrated radar preview is not suitable for numerical physical interpretation.
- The **image upload** mode measures visual changes in image-pixel intensity only. It may distort images by resizing and should not be described as a SAR-based scientific estimate.
- **Ground movement** generally requires InSAR phase processing, coherence, geometry correction, calibration and suitable controls. Backscatter differences cannot establish line-of-sight displacement.

## CSV format

```csv
row,col,before_db,after_db
0,0,-12.5,-13.1
0,1,-10.2,-8.8
1,0,-14.0,-16.3
1,1,-9.7,-10.1
```

Each pair of cells must refer to the same geographic grid pixel. The result is `delta_db = after_db - before_db`. Use `row` and `col` starting from zero (nonnegative integers). The app accepts 1–300,000 rows and will cap image rendering at one million cells.

The app contains a downloadable **synthetic example CSV**, explicitly labeled as such.

## NASA data workflow for actual judging evidence

1. Visit https://search.asf.alaska.edu/ and search the relevant area.
2. Select **NISAR** and a suitable product (e.g., calibrated L-band GCOV). Confirm actual matching dates and product availability.
3. Download products with a NASA Earthdata Login if needed. Choose a sensible analysis method for your target phenomenon (e.g., calibrated backscatter comparisons vs. InSAR deformation).
4. Process the source products in specialist SAR tools to get aligned calibrated arrays. Preserve provenance: granule IDs, acquisition times, polarization, orbit and processing choices.
5. Export aligned dB values in the documented CSV form and upload them into this app.
6. Record changes, confidence, uncertainty, source citations, limitations, and independent validation in the notebook; download findings.

## Verified references (checked 14 November 2026)

- NASA Space Apps 2026 challenge: https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/
- NASA/ISRO NISAR mission: https://science.nasa.gov/mission/nisar/
- NASA NISAR data guide: https://science.nasa.gov/mission/nisar/data/
- ASF NISAR access guide: https://nisar-docs.asf.alaska.edu/access-overview/
- ASF NISAR ASF Search guide: https://nisar-docs.asf.alaska.edu/asf-search/
- ASF Search API: https://docs.asf.alaska.edu/api/basics/
- ASF Vertex: https://search.asf.alaska.edu/
- ISRO Bhoonidhi: https://bhoonidhi.nrsc.gov.in/

The visual SVG banner in this repository is original illustrative artwork, **not a NASA image**. This student prototype is not affiliated with or endorsed by NASA or ISRO.

## Suggested student roles (four or five students)

Research / mission context • geospatial investigation and data collection • Python UI & visualizations • data interpretation and evaluation • testing, documentation, and presentation.

## License

Original prototype code and illustrations: MIT (see `LICENSE`). NASA and ISRO names and mission information retain their respective attribution.
