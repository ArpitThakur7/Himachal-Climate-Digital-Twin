# ════════════════════════════════════════════════════════════════════════════════
# COMPREHENSIVE RESEARCH MASTER PLAN: Himachal Climate Digital Twin
# Objective: Transform the engineering prototype into an NHESS-publishable paper.
# Philosophy: Chase the objective like a loop — Data Prep → Modeling → Validation → Iteration
# ════════════════════════════════════════════════════════════════════════════════

"""
OVERALL OBJECTIVE: 
Prove quantitatively that integrating terrain, satellite soil moisture, and 
infrastructure networks (The Digital Twin) provides significantly better disaster 
warning lead-times and impact predictions than traditional rainfall-only thresholds.
"""

# ==============================================================================
# PHASE 1: STATISTICAL FOUNDATION (Establishing the Climatological Baseline)
# ==============================================================================
# OBJECTIVE: Move beyond visual charts to rigorous statistical proof of climate shift.
# TARGET PAPER SECTION: Section 3.1 (Methodology) & Section 4.1 (Results)
#
# LIBRARIES TO INSTALL: pip install pymannkendall pandas scipy
# SCRIPT TO CREATE: analysis/statistical_tests.py
#
# --- THE LOOP ---
# 1. LOAD DATA: Load mandi_kullu_chamba.parquet (20 years of daily rainfall)
# 2. FEATURE ENGINEERING (Annual Aggregation Loop):
#    For year in 2005 to 2025:
#       For district in ['Mandi', 'Kullu', 'Chamba']:
#           - Compute Monsoon Total (Sum of Jun-Sep rainfall)
#           - Compute Wet Day Intensity (Mean rainfall where day > 1mm)
#           - Compute Heavy Rain Days (Count of days > 64.5mm)
#           - Compute Max Consecutive Dry Days (Longest streak of < 1mm)
#           - Extract Peak Single-Day Rainfall
# 3. STATISTICAL TESTING LOOP:
#    For metric in [Monsoon Total, Intensity, Heavy Days, Dry Spells, Peak Rain]:
#       For district in districts:
#           A. Run Mann-Kendall Trend Test:
#              - Is there a monotonic upward/downward trend? (p-value < 0.05)
#           B. Run Sen's Slope Estimator:
#              - What is the magnitude of change per decade? (e.g., +15mm/decade)
#           C. Run Welch's t-test (Split data: 2005-2014 vs 2015-2025):
#              - Is the recent decade statistically different from the past?
# 4. OUTPUTS:
#    - climate-data/outputs/statistical_results_table.csv (Columns: Metric, District, MK-Trend, p-value, Sen-Slope, T-Test-Sig)
#    - *** This becomes TABLE 2 in the research paper. ***


# ==============================================================================
# PHASE 2: TERRAIN & VULNERABILITY MAPPING (The Spatial Context)
# ==============================================================================
# OBJECTIVE: Quantify the physical landscape's susceptibility to failure.
# TARGET PAPER SECTION: Section 3.2 (Study Area & Environmental Context)
#
# LIBRARIES TO INSTALL: pip install numpy rasterio matplotlib
# SCRIPT TO CREATE: analysis/compute_slope.py
#
# --- THE LOOP ---
# 1. COMPUTE GRADIENT:
#    - Load elevation_mosaic.npy.
#    - Use np.gradient to compute dz/dx and dz/dy across the grid.
# 2. CALCULATE SLOPE (The core vulnerability metric):
#    - slope_pct = sqrt((dz/dx)^2 + (dz/dy)^2)
#    - slope_deg = arctan(slope_pct) * (180/pi)
# 3. CATEGORIZE RISK LOOP:
#    For each pixel in the slope array:
#       - < 15°  -> 1 (Low Risk)
#       - 15-30° -> 2 (Moderate Risk)
#       - 30-45° -> 3 (High Risk)
#       - > 45°  -> 4 (Extreme Risk)
# 4. OUTPUTS:
#    - climate-data/terrain/slope_mosaic.npy (Saved for ML pipeline)
#    - climate-data/terrain/aspect_mosaic.npy
#    - climate-data/outputs/slope_risk_map.png (Color-coded map overlaid with district boundaries)
#    - *** This becomes FIGURE 3 in the research paper. ***


# ==============================================================================
# PHASE 3: GROUND TRUTH LABELING (The Dependent Variable)
# ==============================================================================
# OBJECTIVE: Build a historical database of when and where disasters actually happened.
# TARGET PAPER SECTION: Section 2 (Data Sources)
#
# LIBRARIES TO INSTALL: pip install requests pandas
# SCRIPT TO CREATE: pipeline/build_disaster_labels.py
#
# --- THE LOOP ---
# 1. FETCH HISTORICAL REPORTS:
#    - Query ReliefWeb API for "Himachal Pradesh" + "Landslide" OR "Flood" (2005-2025).
# 2. MANUAL CURATION (The critical human-in-the-loop step):
#    - Ensure major known events are accurately dated and localized:
#       * Kotropi Landslide (Mandi): 2017-08-13 (46 deaths)
#       * Kullu Floods: 2018-09-01
#       * Toong Landslide (Kinnaur): 2021-08-11
#       * Mandi Cloudburst: 2023-07-09
# 3. LABEL INTEGRATION LOOP:
#    - Load mandi_kullu_chamba.parquet.
#    - Initialize column `disaster_within_3days` = False
#    - For each row (Date, District):
#       - If (Date + 0 to 3 days, District) exists in disaster database:
#           - Set `disaster_within_3days` = True
# 4. OUTPUTS:
#    - climate-data/disaster/disaster_events.csv
#    - climate-data/processed/mandi_kullu_chamba_labelled.parquet (The ultimate ML training dataset)
#    - *** This becomes TABLE 1 in the research paper. ***


# ==============================================================================
# PHASE 4: THE CASCADE ENGINE (*** YOUR CORE NOVEL CONTRIBUTION ***)
# ==============================================================================
# OBJECTIVE: Model the domino effect of disasters (Rain -> Landslide -> Road Block -> Isolation).
# TARGET PAPER SECTION: Section 3.4 (Cascading Framework) & Section 4.3 (Cascade Results)
#
# LIBRARIES TO INSTALL: pip install networkx geopandas shapely folium
# SCRIPT TO CREATE: intelligence/cascade_engine.py
#
# --- THE LOOP ---
# 1. GRAPH CONSTRUCTION:
#    - Load road segments from OSMnx GPKG files into a NetworkX directed graph (G).
#    - Nodes = Road intersections, Villages, Hospitals.
#    - Edges = Road segments.
# 2. ATTRIBUTE ASSIGNMENT LOOP (The Exposure Layer):
#    For edge in G.edges:
#       - Get midpoint coordinates.
#       - Extract slope from slope_mosaic.npy at coordinates.
#       - Compute distance to nearest river (from hp_rivers.geojson).
#       - Assign edge weight = travel time (Length / Speed Limit).
# 3. THE CASCADE SIMULATION LOOP (Run for Kotropi 2017 Hindcast):
#    - Input condition: Extreme rainfall (e.g., actual rainfall from Aug 10-13, 2017).
#    - Step A (Hazard Generation): Calculate soil saturation based on rain history.
#    - Step B (Slope Failure Trigger):
#       For edge in G.edges:
#           If edge.slope > 35° AND rainfall > threshold AND soil_saturation > threshold:
#               - Mark edge as FAILED.
#    - Step C (Network Degradation):
#       - Remove all FAILED edges from Graph G -> creates Graph G_degraded.
# 4. IMPACT QUANTIFICATION LOOP:
#    For village in G.nodes:
#       - Compute shortest_path(village, nearest_hospital) in original G.
#       - Compute shortest_path(village, nearest_hospital) in G_degraded.
#       - If path doesn't exist in G_degraded -> STATUS: ISOLATED.
#       - Else -> STATUS: DELAYED (Time_degraded - Time_original).
# 5. OUTPUTS:
#    - climate-data/outputs/cascade_simulation_results.json
#    - climate-data/outputs/cascade_map_kotropi.html (Folium Map: Red lines for failed roads, black markers for isolated villages)
#    - climate-data/outputs/village_isolation_table.csv
#    - *** This becomes FIGURE 5 & TABLE 4 in the research paper. ***


# ==============================================================================
# PHASE 5: MULTI-HAZARD PREDICTION ML MODEL (The AI Core)
# ==============================================================================
# OBJECTIVE: Train a model that outperforms IMD's standard 64.5mm threshold.
# TARGET PAPER SECTION: Section 3.3 (AI Modeling) & Section 4.2 (Model Performance)
#
# LIBRARIES TO INSTALL: pip install xgboost scikit-learn
# SCRIPT TO CREATE: intelligence/train_hazard_model.py
#
# --- THE LOOP ---
# 1. DATA SPLIT:
#    - Train: 2005 - 2020
#    - Val: 2021 - 2022
#    - Test: 2023 - 2025
# 2. FEATURE MATRIX CONSTRUCTION:
#    - X = [Rain_Today, Rain_3Day_Sum, Rain_7Day_Sum, Slope, Elevation, Soil_Moisture, River_Dist, Month]
#    - Y = disaster_within_3days (0 or 1)
# 3. BASELINE EVALUATION LOOP:
#    - Baseline 1 (IMD Standard): If Rain_Today > 64.5mm -> Predict 1 (Disaster).
#    - Baseline 2 (Rainfall Only AI): Train XGBoost using ONLY rainfall features.
# 4. FULL MODEL TRAINING LOOP:
#    - Train XGBoost Multi-Hazard Classifier on ALL features (X).
#    - Hyperparameter tuning loop (GridSearch): Max Depth, Learning Rate, N-Estimators.
# 5. EVALUATION LOOP (On Test Set: 2023-2025):
#    For model in [Baseline 1, Baseline 2, Full XGBoost]:
#       - Calculate Precision (When we alert, is there a disaster?)
#       - Calculate Recall (Out of all disasters, how many did we catch?)
#       - Calculate F1-Score (Harmonic mean)
#       - Calculate ROC-AUC.
#       - Calculate Lead Time (How many hours before the event did the alert trigger?)
# 6. OUTPUTS:
#    - intelligence/models/xgboost_hazard.json (Trained model weights)
#    - climate-data/outputs/model_comparison_table.csv (proving your Digital Twin beats standard forecasting).
#    - climate-data/outputs/roc_curve.png
#    - *** This becomes TABLE 3 & FIGURE 6 in the research paper. ***


# ==============================================================================
# PHASE 6: EXPLAINABLE AI (Building Government Trust)
# ==============================================================================
# OBJECTIVE: Make the AI's decisions transparent so SDMA officials trust it.
# TARGET PAPER SECTION: Section 4.4 (Explainability)
#
# LIBRARIES TO INSTALL: pip install shap
# SCRIPT TO ADD TO: intelligence/train_hazard_model.py
#
# --- THE LOOP ---
# 1. SHAP VALUE GENERATION:
#    - Initialize shap.TreeExplainer(xgboost_model).
#    - Calculate SHAP values for the Test dataset.
# 2. INTERPRETATION LOOP:
#    - Generate SHAP Summary Plot (Global importance: Does slope matter more than 3-day rain?).
#    - Generate SHAP Force Plot for Kotropi 2017 event (Local importance: WHY did the model flag Kotropi?).
# 3. OUTPUTS:
#    - climate-data/outputs/shap_summary.png
#    - climate-data/outputs/shap_force_kotropi.png
#    - *** This becomes FIGURE 7 in the research paper. ***


# ==============================================================================
# SUMMARY CHASE METRICS (How you know you are done and ready to publish)
# ==============================================================================
# SUCCESS METRIC 1: Is your p-value for the rainfall trend < 0.05? 
#                   (Proves the climate shift is real, not just noise).
# SUCCESS METRIC 2: Does your XGBoost model have a higher F1-score than the 64.5mm threshold? 
#                   (Proves the AI adds significant value).
# SUCCESS METRIC 3: Did the Cascade Engine successfully isolate a village in the Kotropi 2017 simulation? 
#                   (Proves your novel contribution works on historical ground truth).
