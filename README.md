# ABAQUS_scripting
Sample tutorial for Abaqus scripting

## static_K1.py
- Run command: abaqus cae nogui=static_K1.py
- Geometry is drawn, meshed, submitted. As odb becomes available, K1/K2/J... values are extracted into summary_fracture.dat

## Running parametric sweep
- crack length is augmented per rid
- input_template has initial crack length. As rid number increases, the length is augmented
- python orchestrator.py will start the parametric study, yielding results folder as rid0000, rid0001, rid0002, ...
- python extractor.py will extract results from existing rid folders, yielding all_results.dat like:

# rid, crack_length, K1,K2,J,T

0, 2.5000e-01, 1.1277e+00, -1.5243e-01, 5.8946e-03, -5.5933e-01

1, 5.0000e-01, 1.5843e+00, -4.0252e-01, 1.2163e-02, -3.7799e-01

2, 7.5000e-01, 1.9377e+00, -6.7458e-01, 1.9163e-02, -1.6483e-01
