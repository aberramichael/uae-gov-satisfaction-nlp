"""Project configuration: paths, constants, seeds, and reference data.

All paths are resolved relative to the repository root so the project can be
cloned and run from any location without editing hard-coded paths.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
ANNOTATIONS_DIR = DATA_DIR / "annotations"

NOTEBOOKS_DIR = REPO_ROOT / "notebooks"
MODELS_DIR = REPO_ROOT / "models"

RESULTS_DIR = REPO_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR = RESULTS_DIR / "tables"
PREDICTIONS_DIR = RESULTS_DIR / "predictions"
METRICS_FILE = RESULTS_DIR / "metrics.json"

DOCS_DIR = REPO_ROOT / "docs"

# Canonical file names produced by each stage
RAW_FILE = RAW_DIR / "reviews_dataset.csv"
CLEAN_FILE = INTERIM_DIR / "reviews_clean.parquet"
FUNNEL_FILE = INTERIM_DIR / "cleaning_funnel.csv"
MODELLING_FILE = PROCESSED_DIR / "modelling_set.parquet"
SPLIT_FILES = {s: PROCESSED_DIR / f"{s}.parquet" for s in ("train", "val", "test")}
ANNOTATION_SAMPLE = ANNOTATIONS_DIR / "sample_400.csv"
ANNOTATION_FILE = ANNOTATIONS_DIR / "annotations_400.csv"
REANNOTATION_FILE = ANNOTATIONS_DIR / "reannotation_80.csv"

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
RANDOM_SEED = 42
N_BOOT = 2000          # bootstrap replicates for confidence intervals
ALPHA = 0.05

# ---------------------------------------------------------------------------
# Labelling
# ---------------------------------------------------------------------------
# Weak supervision maps star ratings to a binary satisfaction label.
# 3-star reviews are treated as neutral and excluded from the modelling set.
SATISFIED_LABEL = "Satisfied"
DISSATISFIED_LABEL = "Dissatisfied"
NEUTRAL_LABEL = "Neutral"
NEUTRAL_STAR = 3

STAR_TO_LABEL = {
    1: DISSATISFIED_LABEL,
    2: DISSATISFIED_LABEL,
    3: None,  # neutral, excluded from the binary modelling set
    4: SATISFIED_LABEL,
    5: SATISFIED_LABEL,
}
# Positive class for recall / ROC reporting: the operationally critical one.
POSITIVE_CLASS = DISSATISFIED_LABEL

# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------
MIN_WORDS = 6                 # substantive-review threshold
MIXED_THRESHOLD = 0.15        # minority-script share needed to call a review mixed
LENGTH_BANDS = [(0, 2), (3, 5), (6, 10), (11, 25), (26, None)]

# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------
SPLIT_FRACTIONS = {"train": 0.70, "val": 0.15, "test": 0.15}

# ---------------------------------------------------------------------------
# Languages / platforms
# ---------------------------------------------------------------------------
LANGUAGES = ["Arabic", "English"]
PLATFORMS = ["Google Play", "App Store"]

# ---------------------------------------------------------------------------
# Models (names used consistently in results/predictions/<key>_test.csv)
# ---------------------------------------------------------------------------
CLASSICAL_MODELS = {
    "tfidf_lr": "TF-IDF + logistic regression",
    "tfidf_svm": "TF-IDF + linear SVM",
    "tfidf_nb": "TF-IDF + multinomial naive Bayes",
}
TRANSFORMER_MODELS = {
    "xlmr": ("XLM-RoBERTa (base)", "xlm-roberta-base", "bilingual"),
    "mbert": ("Multilingual BERT", "bert-base-multilingual-cased", "bilingual"),
    "arabert": ("AraBERT", "aubmindlab/bert-base-arabertv2", "arabic"),
    "marbert": ("MARBERT", "UBC-NLP/MARBERT", "arabic"),
}
MODEL_DISPLAY = {**CLASSICAL_MODELS, **{k: v[0] for k, v in TRANSFORMER_MODELS.items()}}

# Pre-registered paired comparisons for McNemar (Table 14)
MCNEMAR_PAIRS = [
    ("xlmr", "best_classical", "full", "XLM-RoBERTa vs best classical baseline, full test set"),
    ("xlmr", "best_classical", "Arabic", "XLM-RoBERTa vs best classical baseline, Arabic subset"),
    ("xlmr", "mbert", "full", "XLM-RoBERTa vs multilingual BERT, full test set"),
    ("marbert", "arabert", "Arabic", "MARBERT vs AraBERT, Arabic subset"),
]

# ---------------------------------------------------------------------------
# App list (Appendix B). (app_name, Google Play package, App Store id)
# None means the app is not published on that store.
# ---------------------------------------------------------------------------

APP_LIST = [
    # ---- Federal ----
    ("UAE PASS",                "ae.uaepass.mainapp",                    "1377158818"),
    ("UAEICP",                  "com.echannels.moismartservices",        "1374301965"),
    ("UAE Fast Track",          "com.fasttrack.uae.icp",                 "6476561074"),
    ("MOI UAE",                 "com.uaemoi.smartservices",              "768665731"),
    ("MOHRE",                   "ae.gov.mol",                            "807379317"),
    ("MOHRE G2G",               "ae.gov.mol.g2g",                        "1175881857"),
    ("MOHAP",                   "com.gov.uae.mohap",                     "1462565560"),
    ("Emirates Health Services", "com.mohgov.uae.MOHAPPP",               "1163379015"),
    ("MOE UAE",                 "ae.gov.moe.mobileservices",             "1475400660"),
    ("MOHESR UAE",              "ae.gov.mohesr.app",                     "6737803244"),
    ("MoET UAE",                "ae.economy.MOEDashboards",              "1458324701"),
    ("Ministry of Justice",     "com.timeline.mojmobile.ae",             "1163580188"),
    ("UAE Public Prosecution",  "com.pp_smart_services_app",             "1568248550"),
    ("UAE MOFA",                "com.mob.uae",                           "540714559"),
    ("MOFUAE (Finance)",        "ae.gov.mofuae",                         "981612710"),
    ("Ministry of Energy & Infra", "com.moenr.gov.ae",                   "892396014"),
    ("MOEI Wallet",             "com.stg.moei_wallet",                   "6670192941"),
    ("MOCE Employees",          "com.mocd.mocdapp",                      "1490376957"),
    ("EMARATAX",                "ae.gov.emaratax",                       "1660371526"),
    ("FTA Excise Connect",      "com.exciseconnect.eca.ae",              "1488610662"),
    ("Maskan - FTA",            "maskanrefund.tax.gov.ae",               "6478710219"),
    ("Tajneed (MOD)",           "ae.mod.tajneed",                        "6517355120"),
    ("AWQAF UAE",               "com.awqafuae.android",                  "1499083710"),
    ("UAE Weather (NCM)",       "com.uae.ncms",                          "497964984"),
    ("World Weather (NCM)",     "ae.ncm.android.worldweather",           None),
    ("UAE-Laws",                None,                                    "364916105"),
    ("InvestUAE Connect",       "ae.gov.invest.moiuae",                  "6759544509"),
    ("Etihad WE (FEWA)",        "com.fewa.eService",                     "880606146"),
    ("Etihad WE Consultant",    "com.etihadwe.consultant",               "1609231811"),
    ("Sanadak (Central Bank)",  "com.sanadak.sanadak",                   "6480274912"),

    # ---- Dubai ----
    ("DubaiNow",                "com.deg.mdubai",                        "619712783"),
    ("Dubai Police",            "com.dubaipolice.app",                   "384374316"),
    ("Esaad Card",              "dubaipolice.esaad.ae.esaad_dubaipolice", "1475890066"),
    ("RTA Dubai",               "com.rta.rtadubai",                      "426109507"),
    ("nol Pay",                 "com.snowballtech.rta",                  "1541976471"),
    ("S'hail",                  "com.rta.suhail",                        "1214681230"),
    ("RTA Smart Drive",         "com.mireo.rtasmartdrive",               "926094022"),
    ("DEWA",                    "com.dewa.application",                  "364928325"),
    ("Dubai Municipality",      "ae.gov.dm.uma",                         "1504636184"),
    ("Destinations and more",   "ae.dubaipublicparks.prod",              "6450247865"),
    ("Build In Dubai",          "io.ionic.BPS",                          "1318091114"),
    ("Dubai Health (DAHC)",     "ae.gov.dha.flagship",                   "1437186269"),
    ("DHA",                     "ae.gov.dhamobile",                      "6471334093"),
    ("Dubai Courts",            "ae.gov.dcpetitions.mobile.iphone",      "946033161"),
    ("Dubai Public Prosecution", "ae.gov.dxbpp.smartprosecution",        None),
    ("Al Munasiq (Customs)",    "ae.gov.dubaicustoms.mobile",            "6504709282"),
    ("IDeclare",                "ae.dubaicustoms.ideclare",              "1542187927"),
    ("Dubai Trade",             "ae.dubaitrade.dtmobile",                "6503691030"),
    ("Dubai REST (DLD)",        "ae.gov.dubailand.selfregistration",     "1437805105"),
    ("RDC (DLD)",               "ae.gov.dubailand.rdc",                  "6469329089"),
    ("Smart Salik",             "com.salik.smartsalik",                  "912158362"),
    ("GDRFA DXB",               "ae.dnrd.gdrfad",                        "1625664521"),
    ("KHDA",                    "ae.gov.khda",                           "510571246"),
    ("KHDA SmartApp",           None,                                    "6753711684"),
    ("KHDA Wayfinding",         "com.khda_rtls",                         "6759160840"),
    ("Dubai Civil Defence",     "ae.gov.dcd.dlsp",                       "1255827772"),
    ("DCD Readiness",           "dcd.gov.ae.dcd_readiness",              "6443470364"),
    ("Dubai Reads",             None,                                    "1662905021"),
    ("Dubai Ambulance",         "com.dcas.app",                          "1165959800"),
    ("ESEFNI DCAS",             "dcas.esefni.app",                       "6464299386"),
    ("CDA Dubai",               "com.ionicframework.cdaapp133108",       "923357002"),
    ("CDA Sanad Relay",         "se.nwise.mmxtc.cda.sanadrelay",         "1504690367"),
    ("My Rights CDA",           None,                                    "1103161209"),
    ("Dubai Culture",           "com.dubaiculture",                      "926793557"),
    ("Dubai Library",           "com.dcaa.aas",                          "921365930"),
    ("Visit Dubai (DET)",       "com.dtcm.dubaitourism",                 "925400191"),
    ("Dubai Calendar (DET)",    None,                                    "501018460"),
    ("Dubai Sports Council",    "ae.gov.dsc",                            "6469217591"),
    ("IACAD Prayer Timings",    "ae.gov.iacad.salahtimingapp",           "1331933253"),

    # ---- Abu Dhabi ----
    ("TAMM",                    "abudhabi.tamm.live",                    "1435485576"),
    ("We Are All Police",       "wrplc.adpmb.com.weareallpolice",        "1151447936"),
    ("SEHA",                    "com.linkdev.seha",                      "436297690"),
    ("Sahatna (DOH)",           "com.doh.sahatna",                       "6472413092"),
    ("Healthcare Facility Audit", "com.accela.acam_doh",                 "6471409247"),
    ("Abu Dhabi DOH TA",        "ae.gov.doh.stmobile",                   None),
    ("TAQA Distribution AD",    "com.addc.utilityapp",                   "1045166599"),
    ("TAQA Distribution Al Ain", "com.aadcsmartapp",                     "944770796"),
    ("DARB",                    "com.qmobility.darbx",                   "1509721720"),
    ("Darbi (ITC)",             "com.dot.darbmobile",                    "840100351"),
    ("Abu Dhabi Link",          None,                                    "1505305887"),
    ("AD Judicial",             "com.ADJD",                              "6450068280"),
    ("ADJD Auctions",           "gov.adjd.Auctions",                     "1614141284"),
    ("ADJD Complaints",         "gov.adjd.complaints",                   None),
    ("Balligh Al Niyaba",       None,                                    "1359049958"),
    ("Iskan Abu Dhabi",         "iskan.abudhabi.gov.ae",                 "6443846523"),
    ("Smart Makani",            "com.smartmakani.dmt",                   "1506588280"),
    ("OnwaniClick",             "com.onwaniclick.dpm",                   "1397189133"),
    ("MyLand Abu Dhabi",        "com.myland.dpm",                        "1459796069"),
    ("ADAFSA Self Inspection",  "com.selfinspection",                    "6443712930"),
    ("ADAFSA learning",         None,                                    "6467007675"),
    ("ADAFSA Water Allocation", None,                                    "6755325632"),
    ("ADCDA Community Responder", "com.adcda.communityresponder",        "6751804876"),
    ("Abu Dhabi 360 (ADSC)",    "com.adsc.abudhabi360",                  "6444888839"),
    ("AD DOF",                  "com.dof.app",                           "1463564835"),
    ("Bayaan (SCAD)",           "ae.gov.scad.bayaan.open",               "6499339305"),
    ("Tomouh (DGE)",            "com.dge.academy",                       "6736364399"),
    ("CCAO",                    None,                                    "960254035"),
    ("AUH Guest",               "ae.abudhabiairport.welcome",            "6468561918"),
    ("Experience Abu Dhabi",    "com.visitabudhabi.android",             "721678554"),

    # ---- Sharjah ----
    ("Digital Sharjah",         "ae.sharjah.ds",                         "1569055813"),
    ("RTA Sharjah",             "com.sharjahrta",                        "1187003188"),
    ("Baladiyati Sharjah",      "com.sharjah.municipality",              "1584782736"),
    ("Mawqef Sharjah",          "shj.municipality.parking",              "6739573568"),
    ("SEWA",                    "com.sewa",                              "721507762"),
    ("SEWA MGR",                "com.sewa.sewamgr",                      "6461600959"),
    ("Sharjah Public Prosecution", "com.sharjah_pp_mobile_app",          None),
    ("Sharjah Social Services", None,                                    "1439799709"),
    ("Dawaei",                  None,                                    "1191274022"),
    ("DIAS (Islamic Affairs)",  "com.islamicaffairssharjah",             None),
    ("TAHSEEL Sharjah",         "gov.sfd.tahseelapp",                    "1493421998"),
    ("Bus On Demand Sharjah",   "com.liftango.busondemandsharjah",       "6654901688"),
    ("SAIF ZONE",               "com.saifzone.app",                      "1502229321"),
    ("SEDD Sharjah",            "ae.gov.sedd",                           None),

    # ---- Ajman ----
    ("Ajman Police",            "ae.gov.ajmanpolice.ajmanpolice",        "979481467"),
    ("Ajman Police Club",       "com.vowalaa.ajman_app",                 "6463653002"),
    ("AjmanOne",                "com.Ajec",                              "1163528416"),
    ("MPDA Ajman",              "am.gov.ae.smartservices",               "731268814"),
    ("Ajman DED Inspection",    "si.ajman.ded.ae.siaded",                None),
    ("MAWARED Ajman",           "com.ajmanhrd",                          "6443741454"),
    ("Ajman Rulers Court",      "ae.ajman.rulerscourt",                  "6756175120"),
    ("Ajman VOD",               "ajman.rider",                           "1538316788"),
    ("Ajman Sewerage",          "com.moalajah.ajmansewerageutility",     "1158776017"),

    # ---- Ras Al Khaimah ----
    ("RAK Police",              None,                                    "1312657404"),
    ("mRAK",                    "ae.rak.ega.mrak",                       "767865884"),
    ("Sayr by RAKTA",           "ae.rakta.alhamrabus",                   "1525073858"),
    ("Albosala (RAKTA)",        "com.rakta.albosala",                    "1553878430"),
    ("RAKEZ",                   "com.rakez",                             "1581786595"),

    # ---- Fujairah ----
    ("smartFUJAIRAH",           "gov.ae.fujmun.smartfujairah",           "1373129135"),
    ("IFujairah",               "gov.ae.ifujairah",                      "1178522130"),
    ("Digital Fujairah",        "com.egov.digitalfujairahapp",           "6744321237"),
    ("Fujairah Innovate",       "com.fuj_innovate",                      "1453851153"),
    ("Fujairah Police",         "com.FujairahPolice",                    "1555994726"),

    # ---- Umm Al Quwain ----
    ("DigitalUAQ",              "uae.gov.smartuaq",                      "1063110068"),
    ("UAQ DED Inspection",      "com.ded.inspection",                    None),

    # ---- Semi-Government ----
    ("Emirates Post",           "ae.emiratespost.retailapp",             "6449459572"),
    ("EMX Express",             "ae.emiratespost.app",                   "1511692321"),
    ("Emirates Red Crescent",   "ae.rcuae.rcuae_app",                    "979176387"),
    ("Emirates Transport Booking", "dt.ptsfleetman.ftsservicepro.et",    "6504665528"),
    ("Emirates Transport UTS",  "com.emiratestransport.uts",             "1541525393"),
    ("ArKaNy (ET)",             "ae.et.HrMobApp",                        "1558147844"),
    ("Etihad Rail",             "com.etihadrail.app_prod_sds",           "6751881671"),
    ("Parkin",                  "parkin.ae.dev",                         "6657993734"),
    ("My DTC (Dubai Taxi)",     "com.dtc.mydtc",                         "6448499928"),
    ("Fazaa",                   "ae.fazaa",                              "1049790992"),
    ("DIFC+",                   "com.difc",                              "1282901202"),
    ("DIFC Family Wealth Centre", "com.mightybell.difc",                 "6758109642"),
    ("DFM",                     "com.DFM",                               "997641752"),
    ("ADX Mobile",              "ae.adx.mobile",                         "6504854914"),
    ("ADX Investor",            "com.directfn.universal_adx",            "1487431314"),
    ("iVestor (DFM)",           "ae.dfm.ivestorapp",                     "1628119841"),
    ("Dubai Chambers",          "com.app.dubaichamber",                  "780502711"),
    ("Ajman Chamber",           "ae.ajmanchamber.eservices",             "1591298239"),
    ("Sharjah Chamber",         None,                                    "922421821"),
    ("Sharjah Promotions",      "com.app.sharjahpromotions",             "6748413650"),
    ("Volunteers.ae",           "ae.emiratesfoundation.volunteer",       "1287025745"),
]

APP_NAMES = [a[0] for a in APP_LIST]
