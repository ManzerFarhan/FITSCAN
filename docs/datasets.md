# FITSCAN - Reference datasets

_Generated 2026-11-11 by `backend/scripts/datasets/build_reference_data.py`. Do not edit by hand._

## What these datasets are used for

| Use | Detail |
|---|---|
| Sanity bounds | Each test's `plausible_min/max` (used only to catch OCR slips such as a lost decimal point) must accept at least 99.8 % of real values. The last column below shows how many real values a bound would flag. |
| Benchmark realism | `backend/tests/fixtures/panel_benchmark.py` draws test values from these distributions to build 30 synthetic reports for the 10 priority panels. |
| **Not used for** | Diagnosis, disease prediction, risk scores or reference ranges. FITSCAN always uses the range printed on the user's own report (BR-01) and never diagnoses (BR-04). The datasets' disease labels (CKD, liver disease, hepatitis) are ignored. |

Only aggregate statistics are stored (`backend/data/reference/population_stats.json`). Raw downloads are cached in
`backend/data/external/` (git-ignored); no individual record is copied into the app, tests or fixtures.

## Sources

| Dataset | Description | Licence | Link |
|---|---|---|---|
| NHANES 2017-2018 (cycle J) | U.S. CDC / National Center for Health Statistics - National Health and Nutrition Examination Survey, laboratory files CBC_J, BIOPRO_J, GHB_J, GLU_J, TCHOL_J, HDL_J, TRIGLY_J, FERTIN_J, FETIB_J, HSCRP_J, VID_J, DEMO_J | Public domain (U.S. government work) | https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2017 |
| NHANES 2011-2012 (cycle G) | Thyroid profile file THYROD_G (most recent NHANES cycle with thyroid tests) | Public domain | https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2011 |
| NHANES 2005-2006 (cycle D) | Vitamin B12 (B12_D) and folate (FOLATE_D) - most recent cycle with serum B12 | Public domain | https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2005 |
| UCI Chronic Kidney Disease | L. Rubini, P. Soundarapandian, P. Eswaran (2015). 400 patients, Apollo Hospitals, Tamil Nadu, India | CC BY 4.0 | https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease |
| UCI ILPD (Indian Liver Patient Dataset) | B. Ramana, N. Venkateswarlu (2012). 583 patients, north-east Andhra Pradesh, India | CC BY 4.0 | https://archive.ics.uci.edu/dataset/225/ilpd+indian+liver+patient+dataset |
| UCI HCV data | R. Lichtinghagen, F. Klawonn, G. Hoffmann (2020). 615 blood donors and hepatitis C patients, Hannover, Germany | CC BY 4.0 | https://archive.ics.uci.edu/dataset/571/hcv+data |

## Records per test (68 tests, 410,202 values)

| Panel | Test | Records | Source (dataset `column`, records) | 1st - 50th - 99th percentile | Real values outside sanity bounds |
|---|---|---|---|---|---|
| B12 | Folate (Folic Acid) | 8,143 | NHANES FOLATE_D `LBXFOL` (n=8,143) | 3.9 - 12.3 - 46.8 ng/mL | 0.07% |
| B12 | Vitamin B12 | 8,049 | NHANES B12_D `LBXB12` (n=8,049) | 160 - 542 - 1.83e+03 pg/mL | 0.10% |
| CARDIAC | CK (Creatine Kinase) | 5,899 | NHANES BIOPRO_J `LBXSCK` (n=5,899) | 31 - 115 - 966 U/L | 0.00% |
| CBC | Absolute Basophil Count | 7,523 | NHANES CBC_J `LBDBANO` (n=7,523) | 0 - 0 - 0.1 10^3/µL | 0.00% |
| CBC | Basophils | 7,523 | NHANES CBC_J `LBXBAPCT` (n=7,523) | 0.2 - 0.7 - 1.8 % | 0.00% |
| CBC | Absolute Eosinophil Count | 7,523 | NHANES CBC_J `LBDEONO` (n=7,523) | 0 - 0.2 - 0.9 10^3/µL | 0.00% |
| CBC | Eosinophils | 7,523 | NHANES CBC_J `LBXEOPCT` (n=7,523) | 0.3 - 2.4 - 11.9 % | 0.00% |
| CBC | Hematocrit (PCV) | 7,857 | NHANES CBC_J `LBXHCT` (n=7,528); UCI Chronic Kidney Disease (India) `pcv` (n=329) | 28 - 40.7 - 51.1 % | 0.00% |
| CBC | Hemoglobin | 7,876 | NHANES CBC_J `LBXHGB` (n=7,528); UCI Chronic Kidney Disease (India) `hemo` (n=348) | 9 - 13.6 - 17.2 g/dL | 0.00% |
| CBC | Absolute Lymphocyte Count | 7,523 | NHANES CBC_J `LBDLYMNO` (n=7,523) | 0.9 - 2.3 - 5.9 10^3/µL | 0.01% |
| CBC | Lymphocytes | 7,523 | NHANES CBC_J `LBXLYPCT` (n=7,523) | 13 - 33.1 - 64.4 % | 0.00% |
| CBC | MCH | 7,528 | NHANES CBC_J `LBXMCHSI` (n=7,528) | 20.8 - 29.3 - 34.2 pg | 0.00% |
| CBC | MCHC | 7,528 | NHANES CBC_J `LBXMC` (n=7,528) | 31 - 33.6 - 35.5 g/dL | 0.00% |
| CBC | MCV | 7,528 | NHANES CBC_J `LBXMCVSI` (n=7,528) | 66.2 - 87.1 - 100 fL | 0.01% |
| CBC | Absolute Monocyte Count | 7,523 | NHANES CBC_J `LBDMONO` (n=7,523) | 0.3 - 0.6 - 1.2 10^3/µL | 0.00% |
| CBC | Monocytes | 7,523 | NHANES CBC_J `LBXMOPCT` (n=7,523) | 4.4 - 7.9 - 14.9 % | 0.00% |
| CBC | MPV | 7,528 | NHANES CBC_J `LBXMPSI` (n=7,528) | 6.3 - 8 - 10.5 fL | 0.00% |
| CBC | Absolute Neutrophil Count | 7,523 | NHANES CBC_J `LBDNENO` (n=7,523) | 1.2 - 3.8 - 9.2 10^3/µL | 0.00% |
| CBC | Neutrophils | 7,523 | NHANES CBC_J `LBXNEPCT` (n=7,523) | 23 - 55.1 - 77.3 % | 0.00% |
| CBC | Nucleated RBCs | 7,523 | NHANES CBC_J `LBXNRBC` (n=7,523) | 0 - 0.1 - 0.3 /100WBCs | 0.00% |
| CBC | Platelet Count | 7,528 | NHANES CBC_J `LBXPLTSI` (n=7,528) | 123 - 251 - 464 10^3/µL | 0.00% |
| CBC | RBC Count | 7,797 | NHANES CBC_J `LBXRBCSI` (n=7,528); UCI Chronic Kidney Disease (India) `rbcc` (n=269) | 3.45 - 4.71 - 6.08 10^6/µL | 0.00% |
| CBC | RDW-CV | 7,528 | NHANES CBC_J `LBXRDW` (n=7,528) | 12.1 - 13.5 - 18.7 % | 0.00% |
| CBC | Total WBC Count (TLC) | 7,822 | NHANES CBC_J `LBXWBCSI` (n=7,528); UCI Chronic Kidney Disease (India) `wbcc` (n=294) | 3.4 - 7.1 - 14 10^3/µL | 0.01% |
| INFLAMMATION | C-Reactive Protein | 7,250 | NHANES HSCRP_J `LBXHSCRP` (n=7,250) | 0.11 - 1.35 - 36.3 mg/L | 0.00% |
| INFLAMMATION | hs-CRP (High-Sensitivity CRP) | 7,250 | NHANES HSCRP_J `LBXHSCRP` (n=7,250) | 0.11 - 1.35 - 36.3 mg/L | 0.00% |
| IRON | Ferritin | 6,589 | NHANES FERTIN_J `LBXFER` (n=6,589) | 5.83 - 80.7 - 780 ng/mL | 0.00% |
| IRON | Iron | 5,902 | NHANES BIOPRO_J `LBXSIR` (n=5,902) | 21 - 83 - 198 µg/dL | 0.00% |
| IRON | TIBC (Total Iron Binding Capacity) | 5,893 | NHANES FETIB_J `LBDTIB` (n=5,893) | 218 - 324 - 476 µg/dL | 0.00% |
| IRON | Transferrin Saturation | 5,893 | NHANES FETIB_J `LBDPCT` (n=5,893) | 5 - 26 - 62 % | 0.00% |
| IRON | UIBC (Unsaturated Iron Binding Capacity) | 5,899 | NHANES FETIB_J `LBXUIB` (n=5,899) | 101 - 236 - 435 µg/dL | 0.00% |
| KFT | Bicarbonate | 5,901 | NHANES BIOPRO_J `LBXSC3SI` (n=5,901) | 20 - 26 - 31 mmol/L | 0.00% |
| KFT | Blood Urea Nitrogen (BUN) | 5,901 | NHANES BIOPRO_J `LBXSBU` (n=5,901) | 6 - 14 - 36 mg/dL | 0.00% |
| KFT | Calcium | 5,901 | NHANES BIOPRO_J `LBXSCA` (n=5,901) | 8.5 - 9.3 - 10.2 mg/dL | 0.00% |
| KFT | Chloride | 5,904 | NHANES BIOPRO_J `LBXSCLSI` (n=5,904) | 94 - 101 - 107 mmol/L | 0.00% |
| KFT | Creatinine | 6,901 | NHANES BIOPRO_J `LBXSCR` (n=5,903); UCI Chronic Kidney Disease (India) `sc` (n=383); UCI HCV data (Germany) `CREA` (n=615) | 0.45 - 0.83 - 5.2 mg/dL | 0.04% |
| KFT | eGFR | 5,154 | NHANES BIOPRO_J+DEMO_J (CKD-EPI 2021, adults) `LBXSCR,RIDAGEYR,RIAGENDR` (n=5,154) | 30.2 - 97.3 - 135 mL/min/1.73m² | 0.00% |
| KFT | Phosphorus | 5,901 | NHANES BIOPRO_J `LBXSPH` (n=5,901) | 2.4 - 3.6 - 5.3 mg/dL | 0.00% |
| KFT | Potassium | 6,211 | NHANES BIOPRO_J `LBXSKSI` (n=5,899); UCI Chronic Kidney Disease (India) `pot` (n=312) | 3.3 - 4.1 - 5.2 mmol/L | 0.03% |
| KFT | Sodium | 6,217 | NHANES BIOPRO_J `LBXSNASI` (n=5,904); UCI Chronic Kidney Disease (India) `sod` (n=313) | 132 - 140 - 147 mmol/L | 0.02% |
| KFT | Urea | 6,282 | NHANES BIOPRO_J `LBXSBU` (n=5,901); UCI Chronic Kidney Disease (India) `bu` (n=381) | 12.9 - 30 - 107 mg/dL | 0.00% |
| KFT | Uric Acid | 5,901 | NHANES BIOPRO_J `LBXSUA` (n=5,901) | 2.6 - 5.3 - 9.4 mg/dL | 0.00% |
| LFT | A/G Ratio | 579 | UCI ILPD Indian Liver Patient Dataset `A/G Ratio` (n=579) | 0.386 - 0.93 - 1.81 ratio | 0.00% |
| LFT | Albumin | 7,102 | NHANES BIOPRO_J `LBXSAL` (n=5,905); UCI ILPD Indian Liver Patient Dataset `ALB` (n=583); UCI HCV data (Germany) `ALB` (n=614) | 2.1 - 4.1 - 4.9 g/dL | 0.01% |
| LFT | Alkaline Phosphatase | 7,083 | NHANES BIOPRO_J `LBXSAPSI` (n=5,903); UCI ILPD Indian Liver Patient Dataset `Alkphos` (n=583); UCI HCV data (Germany) `ALP` (n=597) | 35 - 80 - 487 U/L | 0.00% |
| LFT | ALT (SGPT) | 7,099 | NHANES BIOPRO_J `LBXSATSI` (n=5,902); UCI ILPD Indian Liver Patient Dataset `Sgpt` (n=583); UCI HCV data (Germany) `ALT` (n=614) | 6 - 18 - 150 U/L | 0.01% |
| LFT | AST (SGOT) | 7,080 | NHANES BIOPRO_J `LBXSASSI` (n=5,882); UCI ILPD Indian Liver Patient Dataset `Sgot` (n=583); UCI HCV data (Germany) `AST` (n=615) | 11 - 20 - 187 U/L | 0.00% |
| LFT | Bilirubin, Direct | 583 | UCI ILPD Indian Liver Patient Dataset `DB` (n=583) | 0.1 - 0.3 - 13 mg/dL | 0.00% |
| LFT | Bilirubin, Total | 7,101 | NHANES BIOPRO_J `LBXSTB` (n=5,903); UCI ILPD Indian Liver Patient Dataset `TB` (n=583); UCI HCV data (Germany) `BIL` (n=615) | 0.1 - 0.4 - 6.96 mg/dL | 0.01% |
| LFT | Gamma GT (GGT) | 6,517 | NHANES BIOPRO_J `LBXSGTSI` (n=5,902); UCI HCV data (Germany) `CGT` (n=615) | 7 - 20 - 219 U/L | 0.00% |
| LFT | Globulin | 5,901 | NHANES BIOPRO_J `LBXSGB` (n=5,901) | 2.2 - 3.1 - 4.3 g/dL | 0.00% |
| LFT | LDH (Lactate Dehydrogenase) | 5,773 | NHANES BIOPRO_J `LBXSLDSI` (n=5,773) | 100 - 155 - 265 U/L | 0.00% |
| LFT | Total Protein | 7,098 | NHANES BIOPRO_J `LBXSTP` (n=5,901); UCI ILPD Indian Liver Patient Dataset `TP` (n=583); UCI HCV data (Germany) `PROT` (n=614) | 5.2 - 7.18 - 8.24 g/dL | 0.00% |
| LIPID | Total Cholesterol | 7,343 | NHANES TCHOL_J `LBXTC` (n=6,738); UCI HCV data (Germany) `CHOL` (n=605) | 106 - 178 - 299 mg/dL | 0.00% |
| LIPID | HDL Cholesterol | 6,738 | NHANES HDL_J `LBDHDD` (n=6,738) | 29 - 51 - 96 mg/dL | 0.00% |
| LIPID | LDL Cholesterol | 2,808 | NHANES TRIGLY_J `LBDLDL` (n=2,808) | 40.1 - 103 - 210 mg/dL | 0.00% |
| LIPID | Triglycerides | 2,834 | NHANES TRIGLY_J `LBXTR` (n=2,834) | 24 - 87 - 391 mg/dL | 0.00% |
| SUGAR | Glucose, Fasting | 2,891 | NHANES GLU_J `LBXGLU` (n=2,891) | 79 - 102 - 291 mg/dL | 0.00% |
| SUGAR | Glucose, Random | 6,257 | NHANES BIOPRO_J `LBXSGL` (n=5,901); UCI Chronic Kidney Disease (India) `bgr` (n=356) | 69 - 93 - 292 mg/dL | 0.00% |
| SUGAR | HbA1c | 6,045 | NHANES GHB_J `LBXGH` (n=6,045) | 4.6 - 5.5 - 10.4 % | 0.00% |
| THYROID | Anti-Thyroglobulin Antibodies | 1,956 | NHANES THYROD_G `LBXATG` (n=1,956) | 0.6 - 0.6 - 115 IU/mL | 0.00% |
| THYROID | Anti-TPO Antibodies | 1,953 | NHANES THYROD_G `LBXTPO` (n=1,953) | 0.18 - 0.5 - 508 IU/mL | 0.00% |
| THYROID | Free T3 | 1,965 | NHANES THYROD_G `LBXT3F` (n=1,965) | 2.35 - 3.2 - 4.49 pg/mL | 0.00% |
| THYROID | Free T4 | 1,970 | NHANES THYROD_G `LBXT4F` (n=1,970) | 0.57 - 0.83 - 1.34 ng/dL | 0.00% |
| THYROID | T3, Total | 1,969 | NHANES THYROD_G `LBXTT3` (n=1,969) | 68 - 116 - 196 ng/dL | 0.00% |
| THYROID | T4, Total | 1,964 | NHANES THYROD_G `LBXTT4` (n=1,964) | 4.92 - 7.91 - 12.6 µg/dL | 0.00% |
| THYROID | TSH | 1,970 | NHANES THYROD_G `LBXTSH1` (n=1,970) | 0.317 - 1.48 - 6.67 µIU/mL | 0.00% |
| VITAMIN_D | Vitamin D (25-OH) | 7,409 | NHANES VID_J `LBXVIDMS` (n=7,409) | 7.05 - 25.5 - 62.9 ng/mL | 0.00% |

Notes
- eGFR is calculated from NHANES creatinine, age and sex with the CKD-EPI 2021 equation (adults only).
- Urea is calculated from NHANES BUN (urea = BUN x 2.14); UCI CKD reports blood urea directly.
- NHANES vitamin D (nmol/L) is converted to ng/mL (/2.496); UCI HCV values in SI units are converted to FITSCAN units.
- CRP and hs-CRP share the NHANES high-sensitivity CRP measurement.
- ESR has no suitable public dataset; its bounds and benchmark values are set by hand.
