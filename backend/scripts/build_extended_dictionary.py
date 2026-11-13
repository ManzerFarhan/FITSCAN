"""Build data/dictionaries/parameters_extended.json - the extended lab-test dictionary (FR-LAB-5).

The core dictionary (parameters.json) covers the routine panels. This adds the next tier that Indian and
international labs commonly print:
- urine routine;
- blood gases;
- tumour markers;
- infection serology;
- autoimmune markers;
- vitamins and trace elements;
- more hormones, coagulation, kidney, liver, lipid and sugar tests.

Names and synonyms are the printed test names (as on LOINC "short name"/lab menus).
Plausible ranges are deliberately wide: they only catch OCR slips (lost decimal points), never "abnormal" values,
which always come from the lab's own range (BR-01).

A synonym already used by the core dictionary is dropped, and the dropped ones are printed, so a name can never
silently change meaning. Run:  python scripts/build_extended_dictionary.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "dictionaries" / "parameters_extended.json"
CORE = ROOT / "data" / "dictionaries" / "parameters.json"


def P(pid, name, cat, unit=None, lo=None, hi=None, syn=(), about=None):
    return {"parameter_id": pid, "canonical_name": name, "category": cat, "default_unit": unit,
            "plausible_min": lo, "plausible_max": hi, "synonyms": list(syn), "about": about}


def Q(pid, name, cat, syn=(), about=None):
    return P(pid, name, cat, syn=syn, about=about)


TESTS = [
    # ---------------- CBC / haematology ----------------
    P("blasts_pct", "Blasts", "CBC", "%", 0, 100, ["blast cells", "blasts %"], "immature white cells normally absent in blood"),
    P("promyelocytes_pct", "Promyelocytes", "CBC", "%", 0, 100, ["promyelocyte"]),
    P("myelocytes_pct", "Myelocytes", "CBC", "%", 0, 100, ["myelocyte"]),
    P("metamyelocytes_pct", "Metamyelocytes", "CBC", "%", 0, 100, ["metamyelocyte"]),
    P("atypical_lymphocytes_pct", "Atypical Lymphocytes", "CBC", "%", 0, 100, ["reactive lymphocytes", "atypical lymphs"]),
    P("retic_abs", "Reticulocyte Count, Absolute", "CBC", None, None, None,
      ["absolute reticulocyte count", "reticulocytes absolute", "retic absolute"]),
    P("ret_he", "Reticulocyte Haemoglobin (Ret-He)", "CBC", "pg", 5, 60,
      ["reticulocyte hemoglobin", "ret he", "chr", "reticulocyte hemoglobin content"]),
    P("irf", "Immature Reticulocyte Fraction", "CBC", "%", 0, 100, ["irf", "immature reticulocyte fraction irf"]),
    P("hb_a", "Haemoglobin A (HbA)", "CBC", "%", 0, 100, ["hba", "hb a", "hemoglobin a adult"]),
    P("hb_a2", "Haemoglobin A2 (HbA2)", "CBC", "%", 0, 100, ["hba2", "hb a2"], "a minor haemoglobin measured in thalassaemia screening"),
    P("hb_f", "Foetal Haemoglobin (HbF)", "CBC", "%", 0, 100, ["hbf", "hb f", "fetal hemoglobin", "foetal hemoglobin"]),
    P("hb_s", "Haemoglobin S (HbS)", "CBC", "%", 0, 100, ["hbs", "hb s", "sickle hemoglobin"]),
    P("g6pd", "G6PD Activity", "CBC", None, None, None,
      ["g6pd", "glucose 6 phosphate dehydrogenase", "g 6 pd", "g6pd quantitative"], "an enzyme that protects red cells"),
    Q("sickling_test", "Sickling Test", "CBC", ["sickling", "sickle cell test", "sickle cell solubility test"]),
    Q("coombs_direct", "Direct Coombs Test (DAT)", "CBC", ["direct coombs", "dat", "direct antiglobulin test"]),
    Q("coombs_indirect", "Indirect Coombs Test (ICT)", "CBC", ["indirect coombs", "ict", "indirect antiglobulin test"]),
    Q("blood_group", "Blood Group (ABO)", "CBC", ["abo group", "blood grouping", "abo", "blood group abo"]),
    Q("rh_type", "Rh Type", "CBC", ["rh", "rh factor", "rh d", "rh typing", "rhd"]),
    P("lymphocytes_atypical_abs", "Atypical Lymphocytes, Absolute", "CBC", "10^3/µL", 0, 100, ["absolute atypical lymphocytes"]),
    P("osmotic_fragility", "Osmotic Fragility", "CBC", "%", 0, 1, ["osmotic fragility test"]),
    P("mchc_ret", "Reticulocyte Production Index", "CBC", "ratio", 0, 20, ["rpi", "reticulocyte production index", "corrected reticulocyte"]),

    # ---------------- Coagulation ----------------
    P("thrombin_time", "Thrombin Time", "COAG", "sec", 1, 300, ["tt", "thrombin clotting time", "thrombin time tt"]),
    P("factor_viii", "Factor VIII Activity", "COAG", "%", 0, 1000, ["factor viii", "factor 8", "fviii", "factor viii assay"]),
    P("factor_ix", "Factor IX Activity", "COAG", "%", 0, 1000, ["factor ix", "factor 9", "fix assay", "factor ix assay"]),
    P("protein_c", "Protein C Activity", "COAG", "%", 0, 500, ["protein c", "protein c functional"]),
    P("protein_s", "Protein S Activity", "COAG", "%", 0, 500, ["protein s", "free protein s", "protein s free"]),
    P("antithrombin", "Antithrombin III", "COAG", "%", 0, 500, ["antithrombin", "at iii", "atiii", "antithrombin 3"]),
    Q("lupus_anticoagulant", "Lupus Anticoagulant", "COAG", ["lupus anticoagulant", "lac", "drvvt", "lupus anticoagulant drvvt"]),
    P("anti_xa", "Anti-Xa Level", "COAG", None, None, None, ["anti xa", "heparin anti xa", "anti factor xa"]),
    P("vwf_antigen", "von Willebrand Factor Antigen", "COAG", "%", 0, 1000, ["vwf antigen", "vwf ag", "von willebrand factor"]),
    P("fdp", "Fibrin Degradation Products", "COAG", None, None, None, ["fdp", "fibrin degradation product"]),
    P("pt_ratio", "PT Ratio", "COAG", "ratio", 0, 20, ["prothrombin ratio", "pt ratio"]),
    P("platelet_aggregation", "Platelet Aggregation", "COAG", "%", 0, 100, ["platelet aggregation study"]),

    # ---------------- Kidney, electrolytes, urine chemistry ----------------
    P("osmolality_serum", "Serum Osmolality", "KFT", "mOsm/kg", 150, 450, ["osmolality", "serum osmolality", "plasma osmolality"]),
    P("anion_gap", "Anion Gap", "KFT", "mEq/L", -20, 80, ["anion gap", "ag anion gap"]),
    P("urine_microalbumin", "Urine Microalbumin", "KFT", "mg/L", 0, 5000,
      ["microalbumin", "urine microalbumin", "micro albumin", "urinary microalbumin", "microalbumin urine"],
      "small amounts of albumin in urine, an early kidney marker"),
    P("urine_acr", "Urine Albumin/Creatinine Ratio", "KFT", "mg/g", 0, 10000,
      ["albumin creatinine ratio", "acr", "uacr", "urine acr", "microalbumin creatinine ratio",
       "urine albumin creatinine ratio", "albumin creatinine ratio urine"]),
    P("urine_pcr", "Urine Protein/Creatinine Ratio", "KFT", None, None, None,
      ["protein creatinine ratio", "upcr", "urine pcr", "urine protein creatinine ratio"]),
    P("urine_protein_24h", "24-Hour Urine Protein", "KFT", "mg/24h", 0, 30000,
      ["24 hour urine protein", "24 hr urine protein", "urine protein 24 hours", "24h urine protein", "total protein 24 hr urine"]),
    P("urine_creatinine_24h", "24-Hour Urine Creatinine", "KFT", None, None, None,
      ["24 hour urine creatinine", "24 hr urine creatinine", "urine creatinine 24 hours"]),
    P("urine_volume_24h", "24-Hour Urine Volume", "KFT", "mL", 0, 10000, ["24 hour urine volume", "24 hr urine volume", "urine volume"]),
    P("creatinine_clearance", "Creatinine Clearance", "KFT", "mL/min", 0, 300, ["creatinine clearance", "crcl", "creatinine clearance test"]),
    P("urine_creatinine", "Urine Creatinine", "KFT", None, None, None,
      ["urine creatinine", "creatinine urine", "spot urine creatinine", "urinary creatinine"]),
    P("urine_sodium", "Urine Sodium", "KFT", "mmol/L", 0, 500, ["urine sodium", "sodium urine", "urinary sodium", "spot urine sodium"]),
    P("urine_potassium", "Urine Potassium", "KFT", "mmol/L", 0, 500, ["urine potassium", "potassium urine", "urinary potassium"]),
    P("urine_chloride", "Urine Chloride", "KFT", "mmol/L", 0, 500, ["urine chloride", "chloride urine"]),
    P("urine_calcium", "Urine Calcium", "KFT", None, None, None, ["urine calcium", "calcium urine", "24 hour urine calcium"]),
    P("urine_uric_acid", "Urine Uric Acid", "KFT", None, None, None, ["urine uric acid", "uric acid urine"]),
    P("urine_phosphorus", "Urine Phosphorus", "KFT", None, None, None, ["urine phosphorus", "urine phosphate"]),
    P("beta2_microglobulin", "Beta-2 Microglobulin", "KFT", "mg/L", 0, 200, ["beta 2 microglobulin", "b2m", "beta2 microglobulin", "b2 microglobulin"]),
    P("fena", "Fractional Excretion of Sodium", "KFT", "%", 0, 100, ["fena", "fractional excretion of sodium"]),
    P("egfr_cystatin", "eGFR (Cystatin C)", "KFT", "mL/min/1.73m²", 0, 200, ["egfr cystatin c", "cystatin c egfr", "egfr cys"]),

    # ---------------- Urine routine & microscopy ----------------
    Q("urine_colour", "Urine Colour", "URINE", ["colour", "color", "urine color", "urine colour", "physical colour"]),
    Q("urine_appearance", "Urine Appearance", "URINE",
      ["appearance", "transparency", "clarity", "turbidity", "urine appearance", "urine clarity"]),
    P("urine_sg", "Urine Specific Gravity", "URINE", None, 1.0, 1.06,
      ["specific gravity", "sp gravity", "sp gr", "urine specific gravity", "urine sp gravity", "s g", "sg"]),
    P("urine_ph", "Urine pH", "URINE", None, 3, 10, ["urine ph", "ph urine", "reaction ph", "reaction", "urine reaction"]),
    Q("urine_protein", "Urine Protein", "URINE", ["urine protein", "protein urine", "urine albumin", "albumin urine", "urinary protein"]),
    Q("urine_glucose", "Urine Glucose", "URINE", ["urine glucose", "urine sugar", "glucose urine", "sugar urine", "urinary glucose"]),
    Q("urine_ketones", "Urine Ketones", "URINE", ["ketone bodies", "ketones", "urine ketones", "acetone", "ketone"]),
    Q("urine_bilirubin", "Urine Bilirubin", "URINE", ["urine bilirubin", "bilirubin urine", "bile pigments", "bile pigment"]),
    Q("urine_bile_salts", "Bile Salts", "URINE", ["bile salts", "bile salt"]),
    Q("urobilinogen", "Urobilinogen", "URINE", ["urobilinogen", "urine urobilinogen", "urobilinogen urine"]),
    Q("urine_nitrite", "Nitrite", "URINE", ["nitrite", "nitrites", "urine nitrite"]),
    Q("leukocyte_esterase", "Leukocyte Esterase", "URINE", ["leukocyte esterase", "leucocyte esterase", "leukocytes esterase", "urine leukocytes"]),
    Q("urine_blood", "Urine Blood", "URINE", ["urine blood", "occult blood urine", "blood urine", "urine occult blood", "haemoglobin urine"]),
    P("pus_cells", "Pus Cells", "URINE", "/hpf", 0, 500,
      ["pus cells", "pus cell", "wbc urine", "urine wbc", "leucocytes urine", "pus cells hpf", "urine pus cells"]),
    P("urine_rbc", "Urine Red Blood Cells", "URINE", "/hpf", 0, 1000, ["urine rbc", "rbc urine", "red blood cells urine", "urine red cells", "rbcs hpf"]),
    P("epithelial_cells", "Epithelial Cells", "URINE", "/hpf", 0, 500,
      ["epithelial cells", "epithelial cell", "squamous epithelial cells", "epithelial cells hpf"]),
    Q("urine_casts", "Casts", "URINE", ["casts", "cast", "urine casts", "hyaline casts", "granular casts"]),
    Q("urine_crystals", "Crystals", "URINE", ["crystals", "crystal", "urine crystals", "calcium oxalate crystals", "uric acid crystals"]),
    Q("urine_bacteria", "Bacteria", "URINE", ["bacteria", "urine bacteria"]),
    Q("urine_yeast", "Yeast Cells", "URINE", ["yeast cells", "yeast", "budding yeast"]),
    Q("mucus_threads", "Mucus Threads", "URINE", ["mucus threads", "mucus", "mucous threads"]),
    Q("amorphous_deposits", "Amorphous Deposits", "URINE", ["amorphous deposits", "amorphous material", "amorphous"]),
    Q("urine_pregnancy", "Urine Pregnancy Test", "URINE", ["urine pregnancy test", "upt", "urine hcg", "pregnancy test urine"]),
    Q("stool_occult_blood", "Stool Occult Blood", "URINE", ["stool occult blood", "occult blood stool", "fobt", "faecal occult blood"]),
    Q("stool_ova_cysts", "Stool Ova & Cysts", "URINE", ["ova", "cysts", "ova and cysts", "ova cysts", "stool ova", "parasites stool"]),
    P("stool_calprotectin", "Faecal Calprotectin", "INFLAMMATION", "µg/g", 0, 10000,
      ["calprotectin", "fecal calprotectin", "faecal calprotectin", "stool calprotectin"]),
    P("urine_amylase", "Urine Amylase", "OTHER", "U/L", 0, 20000, ["urine amylase", "amylase urine"]),

    # ---------------- Liver & proteins ----------------
    P("five_nucleotidase", "5'-Nucleotidase", "LFT", "U/L", 0, 500, ["5 nucleotidase", "5 nt", "five nucleotidase", "5 nucleotidase 5nt"]),
    P("ceruloplasmin", "Ceruloplasmin", "LFT", "mg/dL", 0, 200, ["ceruloplasmin", "caeruloplasmin"]),
    P("alpha1_antitrypsin", "Alpha-1 Antitrypsin", "LFT", "mg/dL", 0, 1000, ["alpha 1 antitrypsin", "a1at", "aat", "alpha1 antitrypsin"]),
    P("bile_acids", "Total Bile Acids", "LFT", "µmol/L", 0, 1000, ["bile acids", "total bile acids", "serum bile acids"]),
    P("prealbumin", "Prealbumin", "LFT", "mg/dL", 0, 100, ["prealbumin", "transthyretin"]),
    P("spep_albumin", "Albumin Fraction (Electrophoresis)", "LFT", "g/dL", 0, 10, ["albumin fraction", "albumin electrophoresis"]),
    P("alpha1_globulin", "Alpha-1 Globulin", "LFT", "g/dL", 0, 5, ["alpha 1 globulin", "alpha1 globulin", "a1 globulin"]),
    P("alpha2_globulin", "Alpha-2 Globulin", "LFT", "g/dL", 0, 5, ["alpha 2 globulin", "alpha2 globulin", "a2 globulin"]),
    P("beta_globulin", "Beta Globulin", "LFT", "g/dL", 0, 5, ["beta globulin", "beta 1 globulin", "beta 2 globulin"]),
    P("gamma_globulin", "Gamma Globulin", "LFT", "g/dL", 0, 10, ["gamma globulin", "gamma globulins"]),
    P("m_spike", "M-Spike (Paraprotein)", "LFT", "g/dL", 0, 15, ["m spike", "m band", "paraprotein", "monoclonal band"]),
    P("free_light_kappa", "Free Kappa Light Chains", "LFT", "mg/L", 0, 10000, ["kappa free light chain", "free kappa", "kappa light chain"]),
    P("free_light_lambda", "Free Lambda Light Chains", "LFT", "mg/L", 0, 10000, ["lambda free light chain", "free lambda", "lambda light chain"]),
    P("kappa_lambda_ratio", "Kappa/Lambda Ratio", "LFT", "ratio", 0, 1000, ["kappa lambda ratio", "k l ratio", "flc ratio"]),
    P("cholinesterase", "Cholinesterase", "LFT", "U/L", 0, 30000, ["cholinesterase", "pseudocholinesterase", "serum cholinesterase"]),

    # ---------------- Lipids ----------------
    P("sdldl", "Small Dense LDL", "LIPID", "mg/dL", 0, 300, ["small dense ldl", "sd ldl", "sdldl"]),
    P("remnant_cholesterol", "Remnant Cholesterol", "LIPID", "mg/dL", 0, 500, ["remnant cholesterol", "remnant lipoprotein cholesterol"]),
    P("tg_hdl_ratio", "Triglyceride/HDL Ratio", "LIPID", "ratio", 0, 100, ["tg hdl ratio", "triglyceride hdl ratio", "tg/hdl ratio"]),
    P("lp_pla2", "Lp-PLA2", "LIPID", None, None, None, ["lp pla2", "lipoprotein associated phospholipase a2"]),
    P("apo_e", "Apolipoprotein E", "LIPID", "mg/dL", 0, 100, ["apo e", "apolipoprotein e"]),

    # ---------------- Sugar / diabetes ----------------
    P("fructosamine", "Fructosamine", "SUGAR", "µmol/L", 50, 2000, ["fructosamine", "serum fructosamine"]),
    P("glucose_1h_ogtt", "Glucose 1 Hour (OGTT)", "SUGAR", "mg/dL", 10, 1000,
      ["glucose 1 hour", "1 hour glucose", "glucose 1 hr", "1 hr glucose", "ogtt 1 hour", "plasma glucose 1 hour"]),
    P("glucose_2h_ogtt", "Glucose 2 Hour (OGTT)", "SUGAR", "mg/dL", 10, 1000,
      ["glucose 2 hour", "2 hour glucose", "glucose 2 hr", "2 hr glucose", "ogtt 2 hour", "plasma glucose 2 hour", "2 hrs glucose"]),
    P("glucose_3h_ogtt", "Glucose 3 Hour (OGTT)", "SUGAR", "mg/dL", 10, 1000, ["glucose 3 hour", "3 hour glucose", "glucose 3 hr"]),
    P("gct_50g", "Glucose Challenge Test (50 g)", "SUGAR", "mg/dL", 10, 1000, ["gct", "glucose challenge test", "50 g gct", "glucose challenge"]),
    P("insulin_random", "Insulin, Random", "SUGAR", "µIU/mL", 0, 3000, ["insulin random", "random insulin", "insulin"]),
    P("c_peptide_pp", "C-Peptide, Post-Meal", "SUGAR", "ng/mL", 0, 100, ["c peptide pp", "c peptide post prandial", "post prandial c peptide"]),
    P("homa_b", "HOMA-B", "SUGAR", "%", 0, 2000, ["homa b", "homa beta", "beta cell function"]),
    P("anti_gad", "Anti-GAD Antibodies", "SUGAR", None, None, None, ["anti gad", "gad 65 antibody", "gad antibody", "gad65"]),
    P("insulin_antibody", "Insulin Antibodies", "SUGAR", None, None, None, ["insulin antibodies", "anti insulin antibody"]),
    P("beta_hydroxybutyrate", "Beta-Hydroxybutyrate", "SUGAR", "mmol/L", 0, 50, ["beta hydroxybutyrate", "bhb", "blood ketones", "serum ketones"]),

    # ---------------- Thyroid ----------------
    P("thyroglobulin", "Thyroglobulin", "THYROID", "ng/mL", 0, 100000, ["thyroglobulin", "tg thyroglobulin", "serum thyroglobulin"]),
    P("trab", "TSH Receptor Antibody (TRAb)", "THYROID", "IU/L", 0, 1000,
      ["trab", "tsh receptor antibody", "anti tsh receptor", "tsi", "thyroid stimulating immunoglobulin"]),
    P("reverse_t3", "Reverse T3", "THYROID", "ng/dL", 0, 500, ["reverse t3", "rt3"]),
    P("calcitonin", "Calcitonin", "THYROID", "pg/mL", 0, 100000, ["calcitonin", "serum calcitonin"]),
    P("tbg", "Thyroxine-Binding Globulin", "THYROID", "µg/mL", 0, 200, ["tbg", "thyroxine binding globulin"]),

    # ---------------- Hormones ----------------
    P("shbg", "SHBG", "HORMONE", "nmol/L", 0, 1000, ["shbg", "sex hormone binding globulin"]),
    P("free_testosterone", "Free Testosterone", "HORMONE", "pg/mL", 0, 1000, ["free testosterone", "testosterone free"]),
    P("bioavailable_testosterone", "Bioavailable Testosterone", "HORMONE", "ng/dL", 0, 2000, ["bioavailable testosterone"]),
    P("androstenedione", "Androstenedione", "HORMONE", "ng/mL", 0, 100, ["androstenedione", "a4"]),
    P("oh_progesterone_17", "17-OH Progesterone", "HORMONE", "ng/mL", 0, 500,
      ["17 oh progesterone", "17 hydroxyprogesterone", "17 ohp", "17 alpha hydroxyprogesterone"]),
    P("acth", "ACTH", "HORMONE", "pg/mL", 0, 5000, ["acth", "adrenocorticotropic hormone", "corticotropin"]),
    P("aldosterone", "Aldosterone", "HORMONE", "ng/dL", 0, 500, ["aldosterone", "serum aldosterone", "plasma aldosterone"]),
    P("renin", "Plasma Renin Activity", "HORMONE", None, None, None, ["renin", "plasma renin activity", "pra", "direct renin"]),
    P("arr", "Aldosterone/Renin Ratio", "HORMONE", "ratio", 0, 10000, ["aldosterone renin ratio", "arr"]),
    P("igf1", "IGF-1", "HORMONE", "ng/mL", 0, 3000, ["igf 1", "igf1", "insulin like growth factor 1", "somatomedin c"]),
    P("igfbp3", "IGFBP-3", "HORMONE", None, None, None, ["igfbp 3", "igfbp3", "igf binding protein 3"]),
    P("inhibin_b", "Inhibin B", "HORMONE", "pg/mL", 0, 5000, ["inhibin b"]),
    P("inhibin_a", "Inhibin A", "HORMONE", "pg/mL", 0, 5000, ["inhibin a", "dimeric inhibin a"]),
    P("estriol", "Estriol (uE3)", "HORMONE", None, None, None, ["estriol", "oestriol", "ue3", "unconjugated estriol"]),
    P("papp_a", "PAPP-A", "HORMONE", None, None, None, ["papp a", "pregnancy associated plasma protein a"]),
    P("free_beta_hcg", "Free Beta hCG", "HORMONE", None, None, None, ["free beta hcg", "free b hcg", "free beta human chorionic gonadotropin"]),
    P("metanephrines", "Plasma Metanephrines", "HORMONE", "pg/mL", 0, 100000, ["metanephrine", "metanephrines", "plasma metanephrines"]),
    P("normetanephrines", "Plasma Normetanephrines", "HORMONE", "pg/mL", 0, 100000, ["normetanephrine", "normetanephrines"]),
    P("osteocalcin", "Osteocalcin", "HORMONE", "ng/mL", 0, 500, ["osteocalcin", "bone gla protein"]),
    P("ctx", "Beta-CrossLaps (CTX)", "HORMONE", "pg/mL", 0, 10000, ["beta crosslaps", "ctx", "c telopeptide", "beta ctx"]),
    P("p1np", "P1NP", "HORMONE", "ng/mL", 0, 2000, ["p1np", "total p1np", "procollagen type 1 n propeptide"]),
    P("cortisol_pm", "Cortisol, Evening", "HORMONE", "µg/dL", 0, 200, ["cortisol evening", "evening cortisol", "cortisol pm", "cortisol 4 pm"]),
    P("cortisol_urine_24h", "24-Hour Urine Free Cortisol", "HORMONE", None, None, None, ["urine free cortisol", "24 hour urine cortisol", "ufc"]),
    P("vasopressin", "ADH (Vasopressin)", "HORMONE", "pg/mL", 0, 1000, ["adh", "vasopressin", "antidiuretic hormone"]),
    P("leptin", "Leptin", "HORMONE", "ng/mL", 0, 1000, ["leptin"]),

    # ---------------- Heart ----------------
    P("bnp", "BNP", "CARDIAC", "pg/mL", 0, 100000, ["bnp", "b type natriuretic peptide", "brain natriuretic peptide"]),
    P("myoglobin", "Myoglobin", "CARDIAC", "ng/mL", 0, 100000, ["myoglobin", "serum myoglobin"]),
    P("ck_mb_mass", "CK-MB Mass", "CARDIAC", "ng/mL", 0, 1000, ["ck mb mass", "cpk mb mass"]),
    P("st2", "Soluble ST2", "CARDIAC", "ng/mL", 0, 1000, ["st2", "soluble st2"]),

    # ---------------- Inflammation & immunity ----------------
    P("complement_c3", "Complement C3", "INFLAMMATION", "mg/dL", 0, 1000, ["c3", "complement c3", "c3 complement"]),
    P("complement_c4", "Complement C4", "INFLAMMATION", "mg/dL", 0, 500, ["c4", "complement c4", "c4 complement"]),
    P("igg", "Immunoglobulin G (IgG)", "INFLAMMATION", "mg/dL", 0, 10000, ["igg", "immunoglobulin g", "total igg", "serum igg"]),
    P("iga", "Immunoglobulin A (IgA)", "INFLAMMATION", "mg/dL", 0, 5000, ["iga", "immunoglobulin a", "total iga", "serum iga"]),
    P("igm", "Immunoglobulin M (IgM)", "INFLAMMATION", "mg/dL", 0, 5000, ["igm", "immunoglobulin m", "total igm", "serum igm"]),
    P("ige_total", "Total IgE", "INFLAMMATION", "IU/mL", 0, 100000, ["ige", "total ige", "immunoglobulin e", "serum ige", "ige total"]),
    P("serum_amyloid_a", "Serum Amyloid A", "INFLAMMATION", "mg/L", 0, 5000, ["serum amyloid a", "saa"]),
    P("ace", "ACE (Angiotensin Converting Enzyme)", "INFLAMMATION", "U/L", 0, 1000, ["ace", "angiotensin converting enzyme", "serum ace"]),
    P("cd4", "CD4 Count", "INFLAMMATION", "/µL", 0, 5000, ["cd4", "cd4 count", "absolute cd4", "cd4 absolute", "cd4 t cells"]),
    P("cd8", "CD8 Count", "INFLAMMATION", "/µL", 0, 10000, ["cd8", "cd8 count", "absolute cd8"]),
    P("cd4_cd8_ratio", "CD4/CD8 Ratio", "INFLAMMATION", "ratio", 0, 50, ["cd4 cd8 ratio", "cd4/cd8 ratio"]),
    P("cd4_pct", "CD4 Percentage", "INFLAMMATION", "%", 0, 100, ["cd4 percentage", "cd4 %", "cd4 percent"]),

    # ---------------- Iron ----------------
    P("stfr", "Soluble Transferrin Receptor", "IRON", "mg/L", 0, 100, ["stfr", "soluble transferrin receptor"]),
    P("hepcidin", "Hepcidin", "IRON", "ng/mL", 0, 1000, ["hepcidin"]),

    # ---------------- Vitamins & trace elements ----------------
    P("vitamin_a", "Vitamin A (Retinol)", "VITAMINS", None, None, None, ["vitamin a", "retinol", "serum retinol"]),
    P("vitamin_e", "Vitamin E (Tocopherol)", "VITAMINS", None, None, None, ["vitamin e", "tocopherol", "alpha tocopherol"]),
    P("vitamin_k", "Vitamin K1", "VITAMINS", None, None, None, ["vitamin k", "vitamin k1", "phylloquinone"]),
    P("vitamin_c", "Vitamin C (Ascorbic Acid)", "VITAMINS", "mg/dL", 0, 20, ["vitamin c", "ascorbic acid", "ascorbate"]),
    P("vitamin_b2", "Vitamin B2 (Riboflavin)", "VITAMINS", None, None, None, ["vitamin b2", "riboflavin"]),
    P("vitamin_b3", "Vitamin B3 (Niacin)", "VITAMINS", None, None, None, ["vitamin b3", "niacin", "nicotinic acid"]),
    P("vitamin_b5", "Vitamin B5 (Pantothenic Acid)", "VITAMINS", None, None, None, ["vitamin b5", "pantothenic acid"]),
    P("vitamin_b7", "Vitamin B7 (Biotin)", "VITAMINS", None, None, None, ["vitamin b7", "biotin"]),
    P("vitamin_d_125", "1,25-Dihydroxy Vitamin D", "VITAMINS", "pg/mL", 0, 1000,
      ["1 25 dihydroxy vitamin d", "1 25 oh 2 vitamin d", "calcitriol", "1 25 dihydroxyvitamin d", "vitamin d 1 25 dihydroxy"]),
    P("vitamin_d2", "Vitamin D2", "VITAMINS", "ng/mL", 0, 500, ["vitamin d2", "25 oh vitamin d2", "ergocalciferol"]),
    P("rbc_folate", "RBC Folate", "VITAMINS", "ng/mL", 0, 5000, ["rbc folate", "red cell folate", "folate rbc"]),
    P("holotc", "Active B12 (Holotranscobalamin)", "VITAMINS", "pmol/L", 0, 1000,
      ["holotranscobalamin", "active b12", "holotc", "active vitamin b12"]),
    P("mma", "Methylmalonic Acid", "VITAMINS", None, None, None, ["methylmalonic acid", "mma"]),
    P("selenium", "Selenium", "VITAMINS", "µg/L", 0, 2000, ["selenium", "serum selenium"]),
    P("manganese", "Manganese", "VITAMINS", "µg/L", 0, 500, ["manganese"]),
    P("chromium", "Chromium", "VITAMINS", "µg/L", 0, 500, ["chromium"]),
    P("iodine", "Iodine", "VITAMINS", "µg/L", 0, 5000, ["iodine", "serum iodine", "urine iodine"]),
    P("lead", "Lead (Blood)", "VITAMINS", "µg/dL", 0, 500, ["lead", "blood lead", "lead level"]),
    P("mercury", "Mercury (Blood)", "VITAMINS", "µg/L", 0, 1000, ["mercury", "blood mercury"]),
    P("arsenic", "Arsenic", "VITAMINS", "µg/L", 0, 5000, ["arsenic"]),
    P("cobalt", "Cobalt", "VITAMINS", "µg/L", 0, 500, ["cobalt"]),
    P("coq10", "Coenzyme Q10", "VITAMINS", "µg/mL", 0, 20, ["coenzyme q10", "coq10", "ubiquinone"]),
    P("omega3_index", "Omega-3 Index", "VITAMINS", "%", 0, 30, ["omega 3 index"]),
    P("carnitine", "Carnitine", "VITAMINS", "µmol/L", 0, 500, ["carnitine", "total carnitine", "free carnitine"]),

    # ---------------- Blood gas ----------------
    P("blood_ph", "pH (Blood Gas)", "BLOOD_GAS", None, 6.5, 8.0, ["blood ph", "arterial ph", "ph arterial", "venous ph", "ph blood"]),
    P("pco2", "pCO2", "BLOOD_GAS", "mmHg", 5, 200, ["pco2", "paco2", "partial pressure of carbon dioxide", "pco2 arterial"]),
    P("po2", "pO2", "BLOOD_GAS", "mmHg", 5, 700, ["po2", "pao2", "partial pressure of oxygen", "po2 arterial"]),
    P("hco3_actual", "HCO3 (Actual)", "BLOOD_GAS", "mmol/L", 0, 80, ["hco3 actual", "actual bicarbonate", "hco3 act", "achco3"]),
    P("hco3_std", "HCO3 (Standard)", "BLOOD_GAS", "mmol/L", 0, 80, ["standard bicarbonate", "hco3 std", "sbc", "hco3 standard"]),
    P("base_excess", "Base Excess", "BLOOD_GAS", "mmol/L", -40, 40, ["base excess", "be", "beecf", "be ecf", "be b", "base deficit"]),
    P("so2", "Oxygen Saturation (sO2)", "BLOOD_GAS", "%", 0, 100, ["so2", "sao2", "oxygen saturation", "o2 saturation", "o2 sat"]),
    P("lactate", "Lactate", "BLOOD_GAS", "mmol/L", 0, 40, ["lactate", "lactic acid", "serum lactate", "blood lactate"]),
    P("fio2", "FiO2", "BLOOD_GAS", "%", 0, 100, ["fio2", "fraction of inspired oxygen"]),
    P("pf_ratio", "PaO2/FiO2 Ratio", "BLOOD_GAS", "ratio", 0, 800, ["pao2 fio2 ratio", "p f ratio", "pf ratio"]),
    P("carboxyhemoglobin", "Carboxyhaemoglobin", "BLOOD_GAS", "%", 0, 100, ["carboxyhemoglobin", "cohb", "co hb"]),
    P("methemoglobin", "Methaemoglobin", "BLOOD_GAS", "%", 0, 100, ["methemoglobin", "methb", "met hb"]),
    P("a_a_gradient", "A-a Gradient", "BLOOD_GAS", "mmHg", -50, 700, ["a a gradient", "alveolar arterial gradient", "a a do2"]),

    # ---------------- Tumour markers ----------------
    P("cea", "CEA", "TUMOR_MARKER", "ng/mL", 0, 100000, ["cea", "carcinoembryonic antigen"]),
    P("afp", "AFP (Alpha-Fetoprotein)", "TUMOR_MARKER", "ng/mL", 0, 1000000, ["afp", "alpha fetoprotein", "alpha feto protein"]),
    P("ca125", "CA 125", "TUMOR_MARKER", "U/mL", 0, 100000, ["ca 125", "ca125", "cancer antigen 125"]),
    P("ca199", "CA 19-9", "TUMOR_MARKER", "U/mL", 0, 1000000, ["ca 19 9", "ca19 9", "ca199", "cancer antigen 19 9"]),
    P("ca153", "CA 15-3", "TUMOR_MARKER", "U/mL", 0, 100000, ["ca 15 3", "ca15 3", "ca153", "cancer antigen 15 3"]),
    P("ca724", "CA 72-4", "TUMOR_MARKER", "U/mL", 0, 100000, ["ca 72 4", "ca72 4", "ca724"]),
    P("nse", "Neuron-Specific Enolase", "TUMOR_MARKER", "ng/mL", 0, 10000, ["nse", "neuron specific enolase"]),
    P("chromogranin_a", "Chromogranin A", "TUMOR_MARKER", "ng/mL", 0, 100000, ["chromogranin a", "cga", "chromogranin"]),
    P("cyfra211", "CYFRA 21-1", "TUMOR_MARKER", "ng/mL", 0, 10000, ["cyfra 21 1", "cyfra21 1", "cyfra"]),
    P("he4", "HE4", "TUMOR_MARKER", "pmol/L", 0, 100000, ["he4", "human epididymis protein 4"]),
    P("scc_antigen", "SCC Antigen", "TUMOR_MARKER", "ng/mL", 0, 10000, ["scc antigen", "squamous cell carcinoma antigen", "scc ag"]),
    P("psa_ratio", "Free/Total PSA Ratio", "TUMOR_MARKER", "%", 0, 100,
      ["free psa ratio", "psa ratio", "free to total psa ratio", "free total psa ratio", "percent free psa", "f t psa ratio"]),
    P("roma", "ROMA Index", "TUMOR_MARKER", "%", 0, 100, ["roma", "roma index", "roma score"]),
    P("pivka2", "PIVKA-II", "TUMOR_MARKER", None, None, None, ["pivka ii", "pivka 2", "des gamma carboxy prothrombin", "dcp"]),

    # ---------------- Infection serology & viral load ----------------
    Q("hiv", "HIV 1 & 2 Antibody", "INFECTION",
      ["hiv", "hiv 1 2", "hiv i ii", "hiv 1 and 2 antibody", "hiv antibody", "anti hiv", "hiv 1 2 antibodies", "hiv duo", "hiv screening", "hiv i ii antibody", "hiv 1 2 antibody", "hiv i ii antibodies"]),
    Q("hbsag", "HBsAg (Hepatitis B Surface Antigen)", "INFECTION",
      ["hbsag", "hepatitis b surface antigen", "australia antigen", "hbs ag", "hbsag rapid", "hbsag elisa"]),
    Q("anti_hcv", "Anti-HCV (Hepatitis C Antibody)", "INFECTION", ["anti hcv", "hcv antibody", "hepatitis c antibody", "hcv", "hcv ab"]),
    P("anti_hbs", "Anti-HBs (Hepatitis B Surface Antibody)", "INFECTION", "mIU/mL", 0, 100000,
      ["anti hbs", "hbsab", "hepatitis b surface antibody", "anti hbs titre", "anti hbs titer", "hbs antibody"]),
    Q("anti_hbc_total", "Anti-HBc Total", "INFECTION", ["anti hbc", "anti hbc total", "hbc antibody", "hepatitis b core antibody"]),
    Q("anti_hbc_igm", "Anti-HBc IgM", "INFECTION", ["anti hbc igm", "hbc igm"]),
    Q("hbeag", "HBeAg", "INFECTION", ["hbeag", "hepatitis b e antigen", "hbe ag"]),
    Q("anti_hbe", "Anti-HBe", "INFECTION", ["anti hbe", "hbe antibody"]),
    Q("hav_igm", "Hepatitis A IgM", "INFECTION", ["hav igm", "anti hav igm", "hepatitis a igm", "hepatitis a virus igm"]),
    Q("hev_igm", "Hepatitis E IgM", "INFECTION", ["hev igm", "anti hev igm", "hepatitis e igm", "hepatitis e virus igm"]),
    P("hbv_dna", "HBV DNA Viral Load", "INFECTION", "IU/mL", 0, 1e12, ["hbv dna", "hbv viral load", "hepatitis b viral load", "hbv dna quantitative"]),
    P("hcv_rna", "HCV RNA Viral Load", "INFECTION", "IU/mL", 0, 1e12, ["hcv rna", "hcv viral load", "hepatitis c viral load", "hcv rna quantitative"]),
    P("hiv_viral_load", "HIV-1 Viral Load", "INFECTION", "copies/mL", 0, 1e9, ["hiv viral load", "hiv 1 rna", "hiv rna", "hiv 1 viral load"]),
    Q("vdrl", "VDRL", "INFECTION", ["vdrl", "rpr", "syphilis screen", "vdrl test"]),
    Q("tpha", "TPHA", "INFECTION", ["tpha", "treponema pallidum hemagglutination", "treponema antibody"]),
    Q("widal_o", "Widal S. Typhi O", "INFECTION", ["s typhi o", "salmonella typhi o", "typhi o", "widal o"]),
    Q("widal_h", "Widal S. Typhi H", "INFECTION", ["s typhi h", "salmonella typhi h", "typhi h", "widal h"]),
    Q("widal_ah", "Widal S. Paratyphi AH", "INFECTION", ["s paratyphi ah", "paratyphi ah", "salmonella paratyphi a h"]),
    Q("widal_bh", "Widal S. Paratyphi BH", "INFECTION", ["s paratyphi bh", "paratyphi bh", "salmonella paratyphi b h"]),
    Q("typhidot_igm", "Typhoid IgM (Typhidot)", "INFECTION", ["typhidot igm", "typhidot", "salmonella typhi igm", "typhoid igm"]),
    Q("dengue_ns1", "Dengue NS1 Antigen", "INFECTION", ["dengue ns1", "ns1 antigen", "dengue ns1 antigen", "ns1 ag"]),
    Q("dengue_igm", "Dengue IgM", "INFECTION", ["dengue igm", "dengue igm antibody"]),
    Q("dengue_igg", "Dengue IgG", "INFECTION", ["dengue igg", "dengue igg antibody"]),
    Q("malaria_antigen", "Malaria Antigen", "INFECTION",
      ["malaria antigen", "malaria parasite antigen", "malaria rapid", "pf pv antigen", "plasmodium falciparum antigen", "plasmodium vivax antigen"]),
    Q("malaria_smear", "Malaria Parasite (Smear)", "INFECTION", ["malaria parasite", "mp", "smear for malaria parasite", "mp smear", "malarial parasite"]),
    Q("chikungunya_igm", "Chikungunya IgM", "INFECTION", ["chikungunya igm", "chikungunya"]),
    Q("leptospira_igm", "Leptospira IgM", "INFECTION", ["leptospira igm", "leptospira", "leptospirosis igm"]),
    Q("scrub_typhus_igm", "Scrub Typhus IgM", "INFECTION", ["scrub typhus igm", "scrub typhus", "orientia tsutsugamushi"]),
    Q("cmv_igg", "CMV IgG", "INFECTION", ["cmv igg", "cytomegalovirus igg"]),
    Q("cmv_igm", "CMV IgM", "INFECTION", ["cmv igm", "cytomegalovirus igm"]),
    Q("rubella_igg", "Rubella IgG", "INFECTION", ["rubella igg"]),
    Q("rubella_igm", "Rubella IgM", "INFECTION", ["rubella igm"]),
    Q("toxo_igg", "Toxoplasma IgG", "INFECTION", ["toxoplasma igg", "toxo igg"]),
    Q("toxo_igm", "Toxoplasma IgM", "INFECTION", ["toxoplasma igm", "toxo igm"]),
    Q("hsv_igg", "HSV 1 & 2 IgG", "INFECTION", ["hsv igg", "hsv 1 2 igg", "herpes simplex igg"]),
    Q("hsv_igm", "HSV 1 & 2 IgM", "INFECTION", ["hsv igm", "hsv 1 2 igm", "herpes simplex igm"]),
    Q("ebv_vca_igm", "EBV VCA IgM", "INFECTION", ["ebv vca igm", "ebv igm", "epstein barr virus igm"]),
    Q("h_pylori", "H. pylori Antibody/Antigen", "INFECTION",
      ["h pylori", "helicobacter pylori", "h pylori antibody", "h pylori igg", "h pylori stool antigen"]),
    Q("igra", "TB Interferon Gamma Release Assay", "INFECTION",
      ["quantiferon", "quantiferon tb gold", "igra", "tb gold", "interferon gamma release assay", "tb quantiferon"]),
    Q("covid_antibody", "SARS-CoV-2 Antibody", "INFECTION", ["covid antibody", "sars cov 2 antibody", "covid 19 antibody", "sars cov 2 igg"]),
    Q("covid_rtpcr", "SARS-CoV-2 RT-PCR", "INFECTION", ["covid rt pcr", "sars cov 2 rt pcr", "covid 19 rt pcr"]),
    Q("brucella", "Brucella Antibody", "INFECTION", ["brucella", "brucella igm", "brucella igg", "brucella antibody"]),
    Q("urine_culture", "Urine Culture", "INFECTION", ["urine culture", "culture urine", "urine culture sensitivity"]),
    Q("blood_culture", "Blood Culture", "INFECTION", ["blood culture", "culture blood"]),

    # ---------------- Autoimmune ----------------
    Q("ana", "ANA (Antinuclear Antibody)", "AUTOIMMUNE",
      ["ana", "antinuclear antibody", "anti nuclear antibody", "ana ifa", "ana elisa", "ana hep 2", "antinuclear antibodies"]),
    P("anti_dsdna", "Anti-dsDNA", "AUTOIMMUNE", "IU/mL", 0, 10000, ["anti dsdna", "anti ds dna", "ds dna antibody", "dsdna"]),
    P("anti_ccp", "Anti-CCP", "AUTOIMMUNE", "U/mL", 0, 10000,
      ["anti ccp", "ccp antibody", "anti cyclic citrullinated peptide", "acpa", "cyclic citrullinated peptide antibody"]),
    P("anti_ttg_iga", "Anti-tTG IgA", "AUTOIMMUNE", "U/mL", 0, 10000,
      ["anti ttg iga", "ttg iga", "tissue transglutaminase iga", "anti tissue transglutaminase iga", "ttg"]),
    P("anti_ttg_igg", "Anti-tTG IgG", "AUTOIMMUNE", "U/mL", 0, 10000, ["anti ttg igg", "ttg igg", "tissue transglutaminase igg"]),
    Q("p_anca", "p-ANCA (MPO)", "AUTOIMMUNE", ["p anca", "panca", "mpo antibody", "anti mpo", "myeloperoxidase antibody"]),
    Q("c_anca", "c-ANCA (PR3)", "AUTOIMMUNE", ["c anca", "canca", "pr3 antibody", "anti pr3", "proteinase 3 antibody"]),
    Q("anti_sm", "Anti-Smith (Sm)", "AUTOIMMUNE", ["anti sm", "anti smith", "sm antibody"]),
    Q("anti_ssa", "Anti-SSA (Ro)", "AUTOIMMUNE", ["anti ssa", "anti ro", "ssa ro", "ss a ro"]),
    Q("anti_ssb", "Anti-SSB (La)", "AUTOIMMUNE", ["anti ssb", "anti la", "ssb la", "ss b la"]),
    Q("anti_centromere", "Anti-Centromere", "AUTOIMMUNE", ["anti centromere", "centromere antibody", "cenp b"]),
    Q("anti_scl70", "Anti-Scl-70", "AUTOIMMUNE", ["anti scl 70", "scl 70", "anti topoisomerase"]),
    Q("anti_jo1", "Anti-Jo-1", "AUTOIMMUNE", ["anti jo 1", "jo 1"]),
    Q("anti_rnp", "Anti-U1 RNP", "AUTOIMMUNE", ["anti rnp", "u1 rnp", "anti u1 rnp", "nrnp sm"]),
    P("acl_igg", "Anti-Cardiolipin IgG", "AUTOIMMUNE", None, None, None, ["anti cardiolipin igg", "acl igg", "cardiolipin igg"]),
    P("acl_igm", "Anti-Cardiolipin IgM", "AUTOIMMUNE", None, None, None, ["anti cardiolipin igm", "acl igm", "cardiolipin igm"]),
    P("b2gp1_igg", "Beta-2 Glycoprotein I IgG", "AUTOIMMUNE", None, None, None, ["beta 2 glycoprotein igg", "b2gp1 igg", "anti beta 2 glycoprotein i igg"]),
    P("b2gp1_igm", "Beta-2 Glycoprotein I IgM", "AUTOIMMUNE", None, None, None, ["beta 2 glycoprotein igm", "b2gp1 igm", "anti beta 2 glycoprotein i igm"]),
    Q("ama", "Anti-Mitochondrial Antibody", "AUTOIMMUNE", ["anti mitochondrial antibody", "ama", "ama m2", "mitochondrial antibody"]),
    Q("asma", "Anti-Smooth Muscle Antibody", "AUTOIMMUNE", ["anti smooth muscle antibody", "asma", "smooth muscle antibody"]),
    Q("anti_lkm", "Anti-LKM-1", "AUTOIMMUNE", ["anti lkm", "anti lkm 1", "lkm 1"]),
    Q("parietal_cell_ab", "Anti-Parietal Cell Antibody", "AUTOIMMUNE", ["parietal cell antibody", "anti parietal cell", "apca"]),
    Q("intrinsic_factor_ab", "Intrinsic Factor Antibody", "AUTOIMMUNE", ["intrinsic factor antibody", "anti intrinsic factor", "ifab"]),
    Q("hla_b27", "HLA-B27", "AUTOIMMUNE", ["hla b27", "hla b 27", "hlab27"]),
    Q("endomysial_ab", "Anti-Endomysial Antibody", "AUTOIMMUNE", ["anti endomysial antibody", "ema", "endomysial antibody"]),
    P("anti_dgp", "Anti-Deamidated Gliadin Peptide", "AUTOIMMUNE", None, None, None, ["anti dgp", "deamidated gliadin peptide", "dgp iga", "dgp igg"]),

    # ---------------- Other chemistry & drug levels ----------------
    P("aldolase", "Aldolase", "OTHER", "U/L", 0, 1000, ["aldolase"]),
    P("osmolality_urine", "Urine Osmolality", "OTHER", "mOsm/kg", 0, 2000, ["urine osmolality", "osmolality urine"]),
    P("lithium", "Lithium", "OTHER", "mmol/L", 0, 10, ["lithium", "serum lithium"]),
    P("valproate", "Valproic Acid", "OTHER", "µg/mL", 0, 1000, ["valproic acid", "valproate", "sodium valproate"]),
    P("phenytoin", "Phenytoin", "OTHER", "µg/mL", 0, 200, ["phenytoin", "dilantin"]),
    P("carbamazepine", "Carbamazepine", "OTHER", "µg/mL", 0, 100, ["carbamazepine", "tegretol"]),
    P("phenobarbitone", "Phenobarbitone", "OTHER", "µg/mL", 0, 300, ["phenobarbitone", "phenobarbital"]),
    P("levetiracetam", "Levetiracetam", "OTHER", "µg/mL", 0, 300, ["levetiracetam"]),
    P("digoxin", "Digoxin", "OTHER", "ng/mL", 0, 20, ["digoxin"]),
    P("tacrolimus", "Tacrolimus", "OTHER", "ng/mL", 0, 200, ["tacrolimus", "fk506"]),
    P("cyclosporine", "Cyclosporine", "OTHER", "ng/mL", 0, 5000, ["cyclosporine", "ciclosporin", "cyclosporin"]),
    P("vancomycin", "Vancomycin", "OTHER", "µg/mL", 0, 200, ["vancomycin", "vancomycin trough"]),
    P("methotrexate", "Methotrexate", "OTHER", "µmol/L", 0, 1000, ["methotrexate"]),
    P("paracetamol", "Paracetamol Level", "OTHER", "µg/mL", 0, 1000, ["paracetamol", "acetaminophen"]),
    P("ethanol", "Blood Alcohol", "OTHER", "mg/dL", 0, 1000, ["ethanol", "blood alcohol", "alcohol level"]),
    P("serotonin", "Serotonin", "OTHER", "ng/mL", 0, 5000, ["serotonin"]),
    P("histamine", "Histamine", "OTHER", "ng/mL", 0, 1000, ["histamine"]),
    P("tryptase", "Tryptase", "OTHER", "µg/L", 0, 1000, ["tryptase", "serum tryptase", "mast cell tryptase"]),
    P("ldh_isoenzymes", "LDH Isoenzymes", "OTHER", "%", 0, 100, ["ldh isoenzymes", "ldh 1", "ldh 2"]),
    P("haptoglobin", "Haptoglobin", "OTHER", "mg/dL", 0, 1000, ["haptoglobin"]),
    P("plasma_hb", "Plasma Free Haemoglobin", "OTHER", "mg/dL", 0, 2000, ["plasma free hemoglobin", "free hemoglobin"]),
    P("csf_protein", "CSF Protein", "OTHER", "mg/dL", 0, 5000, ["csf protein", "protein csf"]),
    P("csf_glucose", "CSF Glucose", "OTHER", "mg/dL", 0, 1000, ["csf glucose", "csf sugar", "glucose csf"]),
    P("csf_cells", "CSF Cell Count", "OTHER", "/µL", 0, 100000, ["csf cell count", "csf cells", "csf total cells"]),
    P("ada", "Adenosine Deaminase (ADA)", "OTHER", "U/L", 0, 1000, ["ada", "adenosine deaminase"]),
    P("semen_volume", "Semen Volume", "OTHER", "mL", 0, 20, ["semen volume", "volume semen"]),
    P("sperm_count", "Sperm Count", "OTHER", None, None, None, ["sperm count", "sperm concentration", "total sperm count"]),
    P("sperm_motility", "Sperm Motility", "OTHER", "%", 0, 100, ["sperm motility", "total motility", "progressive motility", "motile sperms"]),
    P("sperm_morphology", "Normal Sperm Morphology", "OTHER", "%", 0, 100, ["normal morphology", "normal forms", "sperm morphology"]),
    P("sweat_chloride", "Sweat Chloride", "OTHER", "mmol/L", 0, 300, ["sweat chloride"]),
    P("bicarb_urine", "Urine Bicarbonate", "OTHER", "mmol/L", 0, 300, ["urine bicarbonate"]),
]


# Plain-language "what it measures" for the commonest new tests; the rest get a truthful category description.
ABOUT = {
    "g6pd": "an enzyme that protects red blood cells from damage",
    "blood_group": "your ABO blood group", "rh_type": "whether your red cells carry the Rh(D) antigen",
    "hb_a2": "a minor type of haemoglobin, measured when screening for thalassaemia",
    "hb_f": "foetal haemoglobin, the type made before birth", "thrombin_time": "how quickly a clot forms once thrombin is added",
    "urine_microalbumin": "small amounts of albumin protein in urine, an early kidney marker",
    "urine_acr": "albumin in urine compared with creatinine, a kidney marker",
    "creatinine_clearance": "how well the kidneys clear creatinine from the blood",
    "pus_cells": "white blood cells seen in urine under a microscope", "urine_sg": "how concentrated the urine is",
    "urine_ph": "how acidic or alkaline the urine is", "urine_ketones": "ketones, made when the body burns fat for energy",
    "urobilinogen": "a breakdown product of bilirubin found in urine",
    "fructosamine": "average blood sugar over roughly the past 2-3 weeks",
    "thyroglobulin": "a protein made by the thyroid gland", "trab": "antibodies that act on the thyroid's TSH receptor",
    "shbg": "a protein that carries sex hormones in the blood", "acth": "the pituitary hormone that tells the adrenal glands to make cortisol",
    "igf1": "a growth factor made mainly in response to growth hormone", "bnp": "a hormone released by the heart when it is under strain",
    "complement_c3": "a protein of the immune system's complement pathway", "complement_c4": "a protein of the immune system's complement pathway",
    "ige_total": "the antibody type involved in allergies", "cd4": "the number of CD4 helper T-cells, a type of white blood cell",
    "vitamin_a": "vitamin A, needed for vision and the immune system", "vitamin_e": "vitamin E, an antioxidant vitamin",
    "vitamin_c": "vitamin C, needed for healthy skin, gums and healing", "selenium": "selenium, a trace mineral",
    "pco2": "carbon dioxide in the blood", "po2": "oxygen in the blood", "lactate": "lactate, made when cells work without enough oxygen",
    "so2": "how much of the haemoglobin is carrying oxygen",
    "cea": "a protein that can be raised in some cancers and other conditions, used mainly to follow treatment",
    "afp": "alpha-fetoprotein, a protein made by the liver and the developing baby",
    "ca125": "a protein used mainly to follow ovarian conditions", "ca199": "a protein used mainly to follow pancreas and bile-duct conditions",
    "hiv": "an HIV screening test", "hbsag": "the hepatitis B surface antigen, a sign of hepatitis B virus",
    "anti_hcv": "antibodies to the hepatitis C virus", "anti_hbs": "protective antibodies to hepatitis B (after vaccination or infection)",
    "vdrl": "a screening test for syphilis", "dengue_ns1": "a part of the dengue virus, found early in the illness",
    "malaria_antigen": "parts of the malaria parasite in the blood", "widal_o": "antibodies to typhoid bacteria",
    "ana": "antibodies against the body's own cell nuclei", "anti_ccp": "antibodies linked to rheumatoid arthritis",
    "anti_ttg_iga": "antibodies linked to coeliac disease", "hla_b27": "a gene marker linked to some joint conditions",
    "lithium": "the level of lithium medicine in the blood", "digoxin": "the level of digoxin medicine in the blood",
}
CATEGORY_ABOUT = {
    "CBC": "a blood cell or haemoglobin test", "COAG": "a blood clotting test", "KFT": "a kidney, salt or urine chemistry test",
    "URINE": "a routine urine or stool test result", "LFT": "a liver or blood protein test", "LIPID": "a blood fat (lipid) test",
    "SUGAR": "a blood sugar or diabetes-related test", "THYROID": "a thyroid test", "HORMONE": "a hormone test",
    "CARDIAC": "a heart marker test", "INFLAMMATION": "an immune system or inflammation test", "IRON": "an iron test",
    "VITAMINS": "a vitamin, mineral or trace element level", "BLOOD_GAS": "a blood gas test (oxygen, carbon dioxide and acid balance)",
    "TUMOR_MARKER": "a tumour marker, used mainly to follow known conditions rather than to diagnose",
    "INFECTION": "an infection test (antibody, antigen, culture or viral load)",
    "AUTOIMMUNE": "an autoimmune antibody test", "OTHER": "a laboratory test",
}


def main() -> None:
    from app.pipelines.lab_report.normalizer import _strip_filler, normalize_key

    core = json.loads(CORE.read_text(encoding="utf-8"))["parameters"]
    taken: dict[str, str] = {}
    for p in core:
        for s in [p["canonical_name"], *p["synonyms"]]:
            k = normalize_key(s)
            taken.setdefault(k, p["parameter_id"])
            taken.setdefault(_strip_filler(k), p["parameter_id"])
    core_ids = {p["parameter_id"] for p in core}
    out, dropped = [], []
    for t in TESTS:
        if t["parameter_id"] in core_ids:
            raise SystemExit(f"duplicate parameter_id {t['parameter_id']}")
        keep = []
        for s in [t["canonical_name"], *t["synonyms"]]:
            k = normalize_key(s)
            owner = taken.get(k) or taken.get(_strip_filler(k))
            if owner and owner != t["parameter_id"]:
                dropped.append(f"{t['parameter_id']}: '{s}' already means {owner}")
                continue
            taken.setdefault(k, t["parameter_id"])
            taken.setdefault(_strip_filler(k), t["parameter_id"])
            if s != t["canonical_name"]:
                keep.append(s)
        about = t["about"] or ABOUT.get(t["parameter_id"]) or CATEGORY_ABOUT[t["category"]]
        out.append({k: v for k, v in {**t, "synonyms": keep, "about": about}.items() if v is not None})
    OUT.write_text(json.dumps({
        "_comment": "Extended lab-test dictionary, generated by scripts/build_extended_dictionary.py - edit the script, "
                    "not this file. Merged after parameters.json; core names always win.",
        "parameters": out,
    }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(out)} tests, {sum(len(p['synonyms']) for p in out)} synonyms -> {OUT.name}")
    for d in dropped:
        print("  dropped", d)


if __name__ == "__main__":
    main()
