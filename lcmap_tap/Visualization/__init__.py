
# A dict used to reference the various products that were generated for LCMAP evaluations
PRODUCTS = {"Change DOY": {"type": "ChangeMaps",
                           "alias": "ChangeMap_color",
                           "root": ""},

            "Change Magnitude": {"type": "ChangeMaps",
                                 "alias": "ChangeMagMap_color",
                                 "root": ""},

            "Change QA": {"type": "ChangeMaps",
                          "alias": "QAMap_color",
                          "root": ""},

            "Segment Length": {"type": "ChangeMaps",
                               "alias": "SegLength_color",
                               "root": ""},

            "Time Since Last Change": {"type": "ChangeMaps",
                                       "alias": "LastChange_color",
                                       "root": ""},

            "Primary Land Cover": {"type": "CoverMaps",
                                   "alias": "CoverPrim_color",
                                   "root": ""},

            "Secondary Land Cover": {"type": "CoverMaps",
                                     "alias": "CoverSec_color",
                                     "root": ""},

            "Primary Land Cover Confidence": {"type": "CoverMaps",
                                              "alias": "CoverConfPrim_color",
                                              "root": ""},

            "Secondary Land Cover Confidence": {"type": "CoverMaps",
                                                "alias": "CoverConfSec_color",
                                                "root": ""}
            }

# A list of possible versions to look for
VERSIONS = ["v2017.08.18", "v2017.8.18",
            "v2017.6.20-a", "v2017.6.20",
            "v2017.06.20", "v2017.06.20b", "v2017.06.20-b",
            "v2017.6.8", "v1.4.0", "v1.4.0rc1"]
