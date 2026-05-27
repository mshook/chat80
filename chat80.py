#!/usr/bin/env python3
"""
chat80.py - A Python/NLTK reimplementation of Warren & Pereira's CHAT-80.

CHAT-80 (Warren & Pereira, 1982) was a Prolog system that answered
natural-language questions about world geography using a DCG that compiled
English into a logical query language, then evaluated those queries against
a small hand-built database of ~150 countries, their populations, areas,
capitals, neighbours, rivers and seas.

This file reproduces the *function* of CHAT-80 over its standard demo
question set.  The architecture mirrors the original:

    English question
       -> NLTK tokenisation / POS-tagging / lemmatisation
       -> normalisation (multi-word entities, adjectival forms, plurals)
       -> pattern-based parser yielding an abstract query
       -> evaluator against the in-memory geographic KB
       -> printed answer

The parser is rule-based rather than a DCG; that is the honest trade-off
for keeping the file small and dependency-light.  Coverage is the demo set
plus close variants, not arbitrary English.

Run:
    python3 chat80.py                 # interactive REPL
    python3 chat80.py --demo          # run the canonical demo questions
    python3 chat80.py "What is the capital of France?"
"""

from __future__ import annotations

import re
import sys
from functools import lru_cache
from typing import Any, Callable, Optional

import nltk
from nltk import pos_tag, word_tokenize
from nltk.stem import WordNetLemmatizer


# --------------------------------------------------------------------- #
#  NLTK bootstrap                                                       #
# --------------------------------------------------------------------- #
def _ensure_nltk() -> None:
    # Package names changed in NLTK 3.9+; detect which set to use.
    import nltk as _nltk
    ver = tuple(int(x) for x in _nltk.__version__.split(".")[:2])
    if ver >= (3, 9):
        pkgs = [
            ("punkt_tab", "tokenizers/punkt_tab"),
            ("averaged_perceptron_tagger_eng",
             "taggers/averaged_perceptron_tagger_eng"),
            ("wordnet", "corpora/wordnet"),
        ]
    else:
        pkgs = [
            ("punkt", "tokenizers/punkt"),
            ("averaged_perceptron_tagger", "taggers/averaged_perceptron_tagger"),
            ("wordnet", "corpora/wordnet"),
        ]
    for pkg, lookup in pkgs:
        try:
            nltk.data.find(lookup)
        except LookupError:
            nltk.download(pkg, quiet=True)


_ensure_nltk()
LEM = WordNetLemmatizer()


# ===================================================================== #
#  KNOWLEDGE BASE                                                       #
#  Names are lowercase, underscore-separated.                           #
#  Population is in thousands; area in km².                             #
#  Figures are approximate circa-1980 values, matching the originals    #
#  in chat80.pl.                                                        #
# ===================================================================== #

CONTINENTS = ("africa", "america", "asia", "australasia", "europe")

_COUNTRY_ROWS = [
    # name             capital           area km²    pop (k)   continent
    ("afghanistan",    "kabul",            647497,    18290,  "asia"),
    ("albania",        "tirana",            28748,     2350,  "europe"),
    ("algeria",        "algiers",         2381740,    17910,  "africa"),
    ("argentina",      "buenos_aires",    2776890,    25719,  "america"),
    ("australia",      "canberra",        7686850,    14000,  "australasia"),
    ("austria",        "vienna",             83871,    7520,  "europe"),
    ("bangladesh",     "dacca",             143998,   80000,  "asia"),
    ("belgium",        "brussels",           30528,    9890,  "europe"),
    ("bolivia",        "la_paz",           1098581,    5200,  "america"),
    ("botswana",       "gaborone",          581730,     750,  "africa"),
    ("brazil",         "brasilia",        8511965,   119000,  "america"),
    ("bulgaria",       "sofia",             110994,    8800,  "europe"),
    ("burma",          "rangoon",           676578,   32000,  "asia"),
    ("cameroon",       "yaounde",           475440,    6500,  "africa"),
    ("canada",         "ottawa",          9976140,    23500,  "america"),
    ("chad",           "ndjamena",         1284000,    4300,  "africa"),
    ("chile",          "santiago",          756950,   10500,  "america"),
    ("china",          "peking",          9596960,   866000,  "asia"),
    ("colombia",       "bogota",           1138910,   25800,  "america"),
    ("cuba",           "havana",            110860,    9500,  "america"),
    ("cyprus",         "nicosia",             9251,     640,  "europe"),
    ("czechoslovakia", "prague",            127870,   15000,  "europe"),
    ("denmark",        "copenhagen",         43094,    5100,  "europe"),
    ("east_germany",   "east_berlin",       108333,   16900,  "europe"),
    ("ecuador",        "quito",             283561,    7000,  "america"),
    ("egypt",          "cairo",            1001450,   38800,  "africa"),
    ("eire",           "dublin",             70280,    3160,  "europe"),
    ("ethiopia",       "addis_ababa",      1127127,   28700,  "africa"),
    ("finland",        "helsinki",          338145,    4700,  "europe"),
    ("france",         "paris",             547030,   52910,  "europe"),
    ("greece",         "athens",            131940,    9170,  "europe"),
    ("guatemala",      "guatemala_city",    108889,    6200,  "america"),
    ("hungary",        "budapest",           93030,   10500,  "europe"),
    ("iceland",        "reykjavik",         103000,     220,  "europe"),
    ("india",          "new_delhi",        3287590,  620700,  "asia"),
    ("indonesia",      "jakarta",          1919440,  136000,  "asia"),
    ("iran",           "teheran",          1648000,   33800,  "asia"),
    ("iraq",           "baghdad",           437072,   11500,  "asia"),
    ("israel",         "jerusalem",          20770,    3500,  "asia"),
    ("italy",          "rome",              301230,   56700,  "europe"),
    ("japan",          "tokyo",             377835,  112000,  "asia"),
    ("jordan",         "amman",              92300,    2700,  "asia"),
    ("kenya",          "nairobi",           582650,   13800,  "africa"),
    ("lebanon",        "beirut",             10400,    2960,  "asia"),
    ("libya",          "tripoli",          1759540,    2440,  "africa"),
    ("luxembourg",     "luxembourg",          2586,     360,  "europe"),
    ("malaysia",       "kuala_lumpur",      329750,   12300,  "asia"),
    ("mexico",         "mexico_city",      1972550,   62500,  "america"),
    ("mongolia",       "ulan_bator",       1565000,    1500,  "asia"),
    ("morocco",        "rabat",             446550,   18900,  "africa"),
    ("mozambique",     "maputo",            801590,    9500,  "africa"),
    ("nepal",          "kathmandu",         147181,   13200,  "asia"),
    ("netherlands",    "amsterdam",          41526,   13800,  "europe"),
    ("new_zealand",    "wellington",        268680,    3140,  "australasia"),
    ("nicaragua",      "managua",           129494,    2200,  "america"),
    ("nigeria",        "lagos",             923768,   66700,  "africa"),
    ("north_korea",    "pyongyang",         120540,   16700,  "asia"),
    ("norway",         "oslo",              323802,    4060,  "europe"),
    ("pakistan",       "islamabad",         803940,   71300,  "asia"),
    ("panama",         "panama_city",        78200,    1740,  "america"),
    ("peru",           "lima",             1285220,   15600,  "america"),
    ("philippines",    "manila",            300000,   43800,  "asia"),
    ("poland",         "warsaw",            312685,   34500,  "europe"),
    ("portugal",       "lisbon",             92391,    9450,  "europe"),
    ("romania",        "bucharest",         237500,   21400,  "europe"),
    ("saudi_arabia",   "riyadh",           2149690,    7300,  "asia"),
    ("senegal",        "dakar",             196190,    5100,  "africa"),
    ("somalia",        "mogadishu",         637657,    3170,  "africa"),
    ("south_africa",   "pretoria",         1219912,   26700,  "africa"),
    ("south_korea",    "seoul",              98480,   34700,  "asia"),
    ("south_yemen",    "aden",              336870,    1690,  "asia"),
    ("spain",          "madrid",            504782,   36000,  "europe"),
    ("sudan",          "khartoum",         2505813,   17900,  "africa"),
    ("sweden",         "stockholm",         449964,    8270,  "europe"),
    ("switzerland",    "bern",               41284,    6330,  "europe"),
    ("syria",          "damascus",          185180,    7600,  "asia"),
    ("taiwan",         "taipei",             35980,   16000,  "asia"),
    ("tanzania",       "dodoma",            945087,   15600,  "africa"),
    ("thailand",       "bangkok",           514000,   43300,  "asia"),
    ("tunisia",        "tunis",             163610,    5640,  "africa"),
    ("turkey",         "ankara",            780580,   41100,  "europe"),
    ("uganda",         "kampala",           236040,   12000,  "africa"),
    ("united_kingdom", "london",            244820,   55930,  "europe"),
    ("united_states",  "washington",       9629091,  215000,  "america"),
    ("upper_volta",    "ouagadougou",       274200,    6200,  "africa"),
    ("uruguay",        "montevideo",        176220,    3100,  "america"),
    ("ussr",           "moscow",          22402200,  255000,  "europe"),
    ("venezuela",      "caracas",           912050,   12200,  "america"),
    ("vietnam",        "hanoi",             329560,   49900,  "asia"),
    ("west_germany",   "bonn",              248577,   61500,  "europe"),
    ("yugoslavia",     "belgrade",          255800,   21800,  "europe"),
    ("zaire",          "kinshasa",         2345410,   25600,  "africa"),
    ("zambia",         "lusaka",            752614,    5300,  "africa"),
    ("zimbabwe",       "salisbury",         390580,    7100,  "africa"),
]

COUNTRIES: dict[str, dict[str, Any]] = {
    name: {"capital": cap, "area": area, "pop": pop, "continent": cont}
    for name, cap, area, pop, cont in _COUNTRY_ROWS
}

# --------------------------------------------------------------------- #
#  Borders: each entry lists a country followed by its neighbours.       #
#  Edges are stored symmetrically.  Restricted to countries in our KB.   #
# --------------------------------------------------------------------- #
_BORDER_LINES = [
    "afghanistan iran pakistan china ussr",
    "albania greece yugoslavia",
    "algeria libya morocco tunisia",
    "argentina bolivia brazil chile uruguay",
    "austria czechoslovakia hungary italy switzerland west_germany yugoslavia",
    "belgium france luxembourg netherlands west_germany",
    "bolivia argentina brazil chile peru",
    "brazil argentina bolivia colombia peru uruguay venezuela",
    "bulgaria greece romania turkey yugoslavia",
    "burma bangladesh china india thailand",
    "canada united_states",
    "chad cameroon libya nigeria sudan",
    "chile argentina bolivia peru",
    "china afghanistan burma india mongolia nepal north_korea pakistan ussr vietnam",
    "colombia brazil ecuador panama peru venezuela",
    "czechoslovakia austria east_germany hungary poland ussr west_germany",
    "denmark west_germany",
    "east_germany czechoslovakia poland west_germany",
    "egypt israel libya sudan",
    "eire united_kingdom",
    "ethiopia kenya somalia sudan",
    "finland norway sweden ussr",
    "france belgium italy luxembourg spain switzerland west_germany",
    "greece albania bulgaria turkey yugoslavia",
    "guatemala mexico nicaragua",
    "hungary austria czechoslovakia romania ussr yugoslavia",
    "india bangladesh burma china nepal pakistan",
    "iran afghanistan iraq pakistan turkey ussr",
    "iraq iran jordan saudi_arabia syria turkey",
    "israel egypt jordan lebanon syria",
    "italy austria france switzerland yugoslavia",
    "jordan iraq israel saudi_arabia syria",
    "kenya ethiopia somalia sudan tanzania uganda",
    "lebanon israel syria",
    "libya algeria chad egypt sudan tunisia",
    "luxembourg belgium france west_germany",
    "mexico guatemala united_states",
    "mongolia china ussr",
    "morocco algeria",
    "mozambique south_africa tanzania zambia zimbabwe",
    "nepal china india",
    "netherlands belgium west_germany",
    "nicaragua guatemala",
    "nigeria cameroon chad",
    "north_korea china south_korea ussr",
    "norway finland sweden ussr",
    "pakistan afghanistan china india iran",
    "panama colombia",
    "peru bolivia brazil chile colombia ecuador",
    "poland czechoslovakia east_germany ussr",
    "portugal spain",
    "romania bulgaria hungary ussr yugoslavia",
    "saudi_arabia iraq jordan south_yemen",
    "somalia ethiopia kenya",
    "south_africa botswana mozambique zimbabwe",
    "south_korea north_korea",
    "south_yemen saudi_arabia",
    "spain france portugal",
    "sudan chad egypt ethiopia kenya libya uganda zaire",
    "sweden finland norway",
    "switzerland austria france italy west_germany",
    "syria iraq israel jordan lebanon turkey",
    "tanzania kenya mozambique uganda zaire zambia",
    "thailand burma malaysia",
    "tunisia algeria libya",
    "turkey bulgaria greece iran iraq syria ussr",
    "uganda kenya sudan tanzania zaire",
    "united_kingdom eire",
    "united_states canada mexico",
    "upper_volta",  # neighbours (mali, niger, ghana, ivory_coast, togo, benin) not in KB
    "uruguay argentina brazil",
    "ussr afghanistan china czechoslovakia finland hungary iran mongolia "
        "north_korea norway poland romania turkey",
    "venezuela brazil colombia",
    "vietnam china thailand",
    "west_germany austria belgium czechoslovakia denmark east_germany "
        "france luxembourg netherlands switzerland",
    "yugoslavia albania austria bulgaria greece hungary italy romania",
    "zaire sudan tanzania uganda zambia cameroon",
    "zambia mozambique tanzania zaire zimbabwe",
    "zimbabwe botswana mozambique south_africa zambia",
]

def _build_borders() -> dict[str, set[str]]:
    b: dict[str, set[str]] = {c: set() for c in COUNTRIES}
    for line in _BORDER_LINES:
        words = line.split()
        a, neighbours = words[0], words[1:]
        for n in neighbours:
            if a in b and n in b:
                b[a].add(n)
                b[n].add(a)
    return b

BORDERS = _build_borders()


# --------------------------------------------------------------------- #
#  Sea / ocean borders                                                  #
# --------------------------------------------------------------------- #
OCEANS = ("atlantic", "pacific", "indian_ocean", "arctic", "southern_ocean")
SEAS = ("baltic", "mediterranean", "black_sea", "red_sea", "north_sea",
        "caspian", "adriatic", "aegean", "persian_gulf", "english_channel",
        "irish_sea")
WATERS = OCEANS + SEAS  # what a country can "border"

_SEA_LINES = [
    "albania mediterranean adriatic",
    "algeria mediterranean",
    "argentina atlantic",
    "australia indian_ocean pacific",
    "bangladesh indian_ocean",
    "belgium north_sea",
    "brazil atlantic",
    "bulgaria black_sea",
    "burma indian_ocean",
    "cameroon atlantic",
    "canada atlantic pacific arctic",
    "chile pacific",
    "china pacific",
    "colombia atlantic pacific",
    "cuba atlantic",
    "cyprus mediterranean",
    "denmark baltic north_sea",
    "east_germany baltic",
    "ecuador pacific",
    "egypt mediterranean red_sea",
    "eire atlantic irish_sea",
    "finland baltic",
    "france atlantic mediterranean english_channel",
    "greece mediterranean aegean",
    "guatemala atlantic pacific",
    "iceland atlantic",
    "india indian_ocean",
    "indonesia indian_ocean pacific",
    "iran caspian persian_gulf",
    "iraq persian_gulf",
    "israel mediterranean red_sea",
    "italy mediterranean adriatic",
    "japan pacific",
    "kenya indian_ocean",
    "lebanon mediterranean",
    "libya mediterranean",
    "malaysia indian_ocean pacific",
    "mexico atlantic pacific",
    "morocco atlantic mediterranean",
    "mozambique indian_ocean",
    "netherlands north_sea",
    "new_zealand pacific",
    "nicaragua atlantic pacific",
    "nigeria atlantic",
    "north_korea pacific",
    "norway atlantic north_sea arctic",
    "pakistan indian_ocean",
    "panama atlantic pacific",
    "peru pacific",
    "philippines pacific",
    "poland baltic",
    "portugal atlantic",
    "romania black_sea",
    "saudi_arabia red_sea persian_gulf",
    "senegal atlantic",
    "somalia indian_ocean",
    "south_africa atlantic indian_ocean",
    "south_korea pacific",
    "south_yemen indian_ocean",
    "spain atlantic mediterranean",
    "sudan red_sea",
    "sweden baltic",
    "syria mediterranean",
    "taiwan pacific",
    "tanzania indian_ocean",
    "thailand indian_ocean pacific",
    "tunisia mediterranean",
    "turkey mediterranean aegean black_sea",
    "united_kingdom atlantic north_sea english_channel irish_sea",
    "united_states atlantic pacific arctic",
    "uruguay atlantic",
    "ussr arctic baltic black_sea caspian pacific",
    "venezuela atlantic",
    "vietnam pacific",
    "west_germany baltic north_sea",
    "yugoslavia adriatic mediterranean",
]

def _build_sea_borders() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    by_country: dict[str, set[str]] = {c: set() for c in COUNTRIES}
    by_water: dict[str, set[str]] = {w: set() for w in WATERS}
    for line in _SEA_LINES:
        words = line.split()
        country, waters = words[0], words[1:]
        for w in waters:
            by_country[country].add(w)
            by_water[w].add(country)
    return by_country, by_water

SEA_BORDERS_OF, COUNTRIES_ON = _build_sea_borders()


# --------------------------------------------------------------------- #
#  Rivers                                                               #
# --------------------------------------------------------------------- #
RIVERS: dict[str, dict[str, Any]] = {
    "amazon":      {"length": 6437, "flows_through":
                    ["peru", "colombia", "brazil"]},
    "congo":       {"length": 4700, "flows_through":
                    ["zaire", "zambia"]},
    "danube":      {"length": 2850, "flows_through":
                    ["west_germany", "austria", "czechoslovakia", "hungary",
                     "yugoslavia", "bulgaria", "romania", "ussr"]},
    "ganges":      {"length": 2510, "flows_through":
                    ["india", "bangladesh"]},
    "indus":       {"length": 3180, "flows_through":
                    ["china", "india", "pakistan"]},
    "irrawaddy":   {"length": 2090, "flows_through":
                    ["burma"]},
    "mekong":      {"length": 4500, "flows_through":
                    ["china", "burma", "thailand", "vietnam"]},
    "mississippi": {"length": 6020, "flows_through":
                    ["united_states"]},
    "niger":       {"length": 4180, "flows_through":
                    ["nigeria"]},
    "nile":        {"length": 6650, "flows_through":
                    ["sudan", "egypt", "uganda"]},
    "parana":      {"length": 4880, "flows_through":
                    ["brazil", "argentina", "uruguay"]},
    "rhine":       {"length": 1320, "flows_through":
                    ["switzerland", "west_germany", "netherlands"]},
    "rio_grande":  {"length": 3060, "flows_through":
                    ["united_states", "mexico"]},
    "volga":       {"length": 3690, "flows_through":
                    ["ussr"]},
    "yangtze":     {"length": 6300, "flows_through":
                    ["china"]},
    "yenisei":     {"length": 5540, "flows_through":
                    ["ussr"]},
    "zambezi":     {"length": 2740, "flows_through":
                    ["zambia", "zimbabwe", "mozambique"]},
}


# --------------------------------------------------------------------- #
#  Cities (a small set, sufficient for population-based queries)        #
# --------------------------------------------------------------------- #
CITIES: dict[str, dict[str, Any]] = {
    "london":         {"country": "united_kingdom", "pop": 7028},
    "paris":          {"country": "france",         "pop": 8424},
    "new_york":       {"country": "united_states",  "pop": 7895},
    "tokyo":          {"country": "japan",          "pop": 11695},
    "moscow":         {"country": "ussr",           "pop": 8011},
    "peking":         {"country": "china",          "pop": 7570},
    "bombay":         {"country": "india",          "pop": 5981},
    "calcutta":       {"country": "india",          "pop": 7031},
    "shanghai":       {"country": "china",          "pop": 10820},
    "seoul":          {"country": "south_korea",    "pop": 6889},
    "mexico_city":    {"country": "mexico",         "pop": 14000},
    "sao_paulo":      {"country": "brazil",         "pop": 8732},
    "rio_de_janeiro": {"country": "brazil",         "pop": 5093},
    "cairo":          {"country": "egypt",          "pop": 5715},
    "buenos_aires":   {"country": "argentina",      "pop": 9927},
    "chicago":        {"country": "united_states",  "pop": 3099},
    "los_angeles":    {"country": "united_states",  "pop": 2967},
    "osaka":          {"country": "japan",          "pop": 2779},
    "rome":           {"country": "italy",          "pop": 2868},
    "madrid":         {"country": "spain",          "pop": 3201},
    "sydney":         {"country": "australia",      "pop": 3193},
    "jakarta":        {"country": "indonesia",      "pop": 6503},
    "tehran":         {"country": "iran",           "pop": 4496},
    "teheran":        {"country": "iran",           "pop": 4496},
    "bangkok":        {"country": "thailand",       "pop": 4702},
    "berlin":         {"country": "east_germany",   "pop": 3074},
    "vienna":         {"country": "austria",        "pop": 1614},
    "kabul":          {"country": "afghanistan",    "pop": 1036},
    "vatican_city":   {"country": "italy",          "pop": 1},
}


# ===================================================================== #
#  LEXICON                                                              #
# ===================================================================== #

# Adjectival forms of continents
ADJ_TO_CONTINENT = {
    "european":      "europe",
    "african":       "africa",
    "asian":         "asia",
    "american":      "america",
    "australasian":  "australasia",
}

# Multi-word names that must be glued into single tokens before parsing.
# Order matters: longer phrases first.
MULTIWORD = [
    ("united kingdom",     "united_kingdom"),
    ("united states",      "united_states"),
    ("upper volta",        "upper_volta"),
    ("saudi arabia",       "saudi_arabia"),
    ("south africa",       "south_africa"),
    ("south korea",        "south_korea"),
    ("north korea",        "north_korea"),
    ("south yemen",        "south_yemen"),
    ("east germany",       "east_germany"),
    ("west germany",       "west_germany"),
    ("new zealand",        "new_zealand"),
    ("soviet union",       "ussr"),
    ("indian ocean",       "indian_ocean"),
    ("pacific ocean",      "pacific"),
    ("atlantic ocean",     "atlantic"),
    ("arctic ocean",       "arctic"),
    ("black sea",          "black_sea"),
    ("red sea",            "red_sea"),
    ("north sea",          "north_sea"),
    ("baltic sea",         "baltic"),
    ("mediterranean sea",  "mediterranean"),
    ("caspian sea",        "caspian"),
    ("adriatic sea",       "adriatic"),
    ("aegean sea",         "aegean"),
    ("persian gulf",       "persian_gulf"),
    ("english channel",    "english_channel"),
    ("irish sea",          "irish_sea"),
    ("new york",           "new_york"),
    ("mexico city",        "mexico_city"),
    ("sao paulo",          "sao_paulo"),
    ("rio de janeiro",     "rio_de_janeiro"),
    ("buenos aires",       "buenos_aires"),
    ("los angeles",        "los_angeles"),
    ("vatican city",       "vatican_city"),
    ("rio grande",         "rio_grande"),
]

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}


# ===================================================================== #
#  DISPLAY HELPERS                                                       #
# ===================================================================== #

DISPLAY_OVERRIDES = {
    "ussr":           "USSR",
    "united_kingdom": "United Kingdom",
    "united_states":  "United States",
    "north_sea":      "North Sea",
    "black_sea":      "Black Sea",
    "red_sea":        "Red Sea",
    "indian_ocean":   "Indian Ocean",
    "persian_gulf":   "Persian Gulf",
    "english_channel": "English Channel",
    "irish_sea":      "Irish Sea",
    "eire":           "Eire",
}

def show(name: Optional[str]) -> str:
    if name is None:
        return "(unknown)"
    if name in DISPLAY_OVERRIDES:
        return DISPLAY_OVERRIDES[name]
    return name.replace("_", " ").title()

def show_list(items, sep: str = ", ", last: str = " and ") -> str:
    items = [show(x) for x in items]
    if not items:
        return "none"
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return items[0] + last + items[1]
    return sep.join(items[:-1]) + last + items[-1]


# ===================================================================== #
#  QUERY PRIMITIVES                                                     #
# ===================================================================== #

def country_attr(country: str, attr: str) -> Any:
    if country not in COUNTRIES:
        raise KeyError(country)
    return COUNTRIES[country][attr]

def in_continent(continent: str) -> list[str]:
    return sorted(c for c, d in COUNTRIES.items() if d["continent"] == continent)

def borders_of(country: str) -> list[str]:
    return sorted(BORDERS.get(country, set()))

def countries_on_water(water: str) -> list[str]:
    return sorted(COUNTRIES_ON.get(water, set()))

def waters_of(country: str) -> list[str]:
    return sorted(SEA_BORDERS_OF.get(country, set()))

def has_coastline(country: str) -> bool:
    return bool(SEA_BORDERS_OF.get(country))

def landlocked(country: str) -> bool:
    return country in COUNTRIES and not has_coastline(country)

def rivers_through(country: str) -> list[str]:
    return sorted(r for r, d in RIVERS.items()
                  if country in d["flows_through"])

def cities_in(country: str) -> list[str]:
    return sorted(c for c, d in CITIES.items() if d["country"] == country)


# ===================================================================== #
#  NORMALISATION                                                        #
# ===================================================================== #

PUNCT_RE = re.compile(r"[?!.,;:]")
WS_RE = re.compile(r"\s+")
ARTICLE_RE = re.compile(r"\b(?:the|a|an)\b\s*")
APOS_RE = re.compile(r"['\u2019]s\b")          # 's, ’s
CONTRACTIONS = [
    (r"\bwhat's\b",    "what is"),
    (r"\bwhere's\b",   "where is"),
    (r"\bwho's\b",     "who is"),
    (r"\bwhich's\b",   "which is"),
    (r"\bthat's\b",    "that is"),
    (r"\bdon't\b",     "do not"),
    (r"\bdoesn't\b",   "does not"),
    (r"\bisn't\b",     "is not"),
]

def _expand_contractions(text: str) -> str:
    for pat, repl in CONTRACTIONS:
        text = re.sub(pat, repl, text)
    return text

def _strip_genitive(text: str) -> str:
    """`country's` -> `country`, handles both straight and curly apostrophes."""
    text = APOS_RE.sub("", text)
    text = text.replace("'", " ").replace("\u2019", " ")
    return text

def _glue_multiword(text: str) -> str:
    for phrase, token in MULTIWORD:
        text = re.sub(rf"\b{re.escape(phrase)}\b", token, text)
    return text

def _expand_adjectivals(text: str) -> str:
    # "european" -> "in_europe", "african country" -> "in_africa country"
    for adj, cont in ADJ_TO_CONTINENT.items():
        text = re.sub(rf"\b{adj}\b", f"in_{cont}", text)
    return text

def _strip_articles(text: str) -> str:
    return ARTICLE_RE.sub("", text)

def _lemmatise_plurals(text: str) -> str:
    """countries -> country, cities -> city, rivers -> river, etc."""
    tokens = text.split()
    out = []
    for t in tokens:
        if t in ("countries", "cities", "rivers", "oceans", "seas",
                 "continents", "neighbours", "neighbors", "borders",
                 "capitals", "populations", "areas"):
            out.append(LEM.lemmatize(t, "n"))
        else:
            out.append(t)
    return " ".join(out)

def normalize(question: str) -> str:
    s = question.lower().strip()
    s = _expand_contractions(s)
    s = _strip_genitive(s)
    s = PUNCT_RE.sub(" ", s)
    s = WS_RE.sub(" ", s).strip()
    s = _glue_multiword(s)              # before article stripping, so
    s = _strip_articles(s)              #   "the united states" -> "united_states"
    s = _expand_adjectivals(s)
    s = _lemmatise_plurals(s)
    s = WS_RE.sub(" ", s).strip()
    return s


def tokens_and_tags(question: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Tokenise and POS-tag the *original* question (kept for reference /
    introspection)."""
    toks = word_tokenize(question)
    return toks, pos_tag(toks)


# ===================================================================== #
#  PATTERN BUILDING BLOCKS                                              #
# ===================================================================== #

def _alt(items) -> str:
    """Build a regex alternation from longest-first sorted items."""
    return "|".join(re.escape(x) for x in sorted(items, key=lambda s: -len(s)))

COUNTRY_RE = _alt(COUNTRIES.keys())
WATER_RE = _alt(WATERS)
RIVER_RE = _alt(RIVERS.keys())
CONTINENT_RE = _alt(CONTINENTS)
IN_CONTINENT_RE = _alt(f"in_{c}" for c in CONTINENTS)
CITY_RE = _alt(CITIES.keys())
CAPITAL_RE = _alt(d["capital"] for d in COUNTRIES.values())

# Used in number parsing: "10 million", "two", "1500000"
NUM_RE = r"(?:\d+(?:\.\d+)?|" + "|".join(NUMBER_WORDS) + r")"

def parse_number_word(s: str) -> float:
    s = s.strip().lower()
    if s in NUMBER_WORDS:
        return float(NUMBER_WORDS[s])
    return float(s)

def parse_amount(text: str) -> Optional[float]:
    """Parse '10 million' / '500 thousand' / '1500000' into a thousands count
    (we store population in thousands).  Returns thousands."""
    text = text.strip().lower()
    m = re.fullmatch(rf"({NUM_RE})\s*million", text)
    if m:
        return parse_number_word(m.group(1)) * 1_000
    m = re.fullmatch(rf"({NUM_RE})\s*billion", text)
    if m:
        return parse_number_word(m.group(1)) * 1_000_000
    m = re.fullmatch(rf"({NUM_RE})\s*thousand", text)
    if m:
        return parse_number_word(m.group(1))
    m = re.fullmatch(NUM_RE, text)
    if m:
        return parse_number_word(text)
    return None


# ===================================================================== #
#  PATTERN HANDLERS                                                     #
#                                                                       #
#  Each handler takes a regex match (after normalisation) and returns   #
#  a string answer.  Patterns are tried in order; the first match wins. #
# ===================================================================== #

# A small ontology used in answers.
def _continent_name(cstr: str) -> str:
    """Accepts either 'europe' or 'in_europe' and returns 'europe'."""
    return cstr.replace("in_", "")


# ---- 1. Capital lookups ---------------------------------------------- #

def h_capital_of(m):
    country = m.group("country")
    return show(country_attr(country, "capital"))

def h_country_whose_capital(m):
    cap = m.group("capital")
    for name, d in COUNTRIES.items():
        if d["capital"] == cap:
            return show(name)
    return "I don't know of such a country."


# ---- 2. Membership / listing ----------------------------------------- #

def h_countries_in_continent(m):
    cont = _continent_name(m.group("cont"))
    cs = in_continent(cont)
    return show_list(cs)

def h_count_countries(m):
    region = m.groupdict().get("cont")
    if region:
        cs = in_continent(_continent_name(region))
        return str(len(cs))
    return str(len(COUNTRIES))

def h_count_rivers(m):
    return str(len(RIVERS))

def h_list_rivers(m):
    return show_list(sorted(RIVERS))


# ---- 3. Borders ------------------------------------------------------ #

def h_borders_of(m):
    c = m.group("country")
    bs = borders_of(c)
    return show_list(bs) if bs else f"{show(c)} has no neighbours in this database."

def h_does_border(m):
    a, b = m.group("a"), m.group("b")
    return "yes" if b in BORDERS.get(a, set()) else "no"

def h_countries_on_water(m):
    w = m.group("water")
    cs = countries_on_water(w)
    return show_list(cs)

def h_capitals_of_bordering_water(m):
    w = m.group("water")
    cs = countries_on_water(w)
    caps = [country_attr(c, "capital") for c in cs]
    return show_list(caps)

def h_countries_bordered_by_n_seas(m):
    n_str = m.group("n")
    n = int(NUMBER_WORDS.get(n_str, n_str))
    result = sorted(c for c, ws in SEA_BORDERS_OF.items() if len(ws) == n)
    return show_list(result)


# ---- 4. Rivers ------------------------------------------------------- #

def h_river_flows(m):
    r = m.group("river")
    if r not in RIVERS:
        return "I don't know that river."
    return show_list(RIVERS[r]["flows_through"])

def h_count_river_countries(m):
    r = m.group("river")
    if r not in RIVERS:
        return "I don't know that river."
    return str(len(RIVERS[r]["flows_through"]))

def h_rivers_through(m):
    c = m.group("country")
    rs = rivers_through(c)
    return show_list(rs) if rs else f"No rivers in this database flow through {show(c)}."


# ---- 5. Attribute lookups -------------------------------------------- #

def h_population_of(m):
    c = m.group("country")
    pop = country_attr(c, "pop")
    return f"{pop * 1000:,} (approx., circa 1980)"

def h_area_of(m):
    c = m.group("country")
    a = country_attr(c, "area")
    return f"{a:,} sq km"


# ---- 6. Superlatives ------------------------------------------------- #

ATTR_OF = {"area": "area", "population": "pop", "pop": "pop"}

def _superlative(scope: list[str], attr: str, *, biggest: bool) -> Optional[str]:
    if not scope:
        return None
    key = ATTR_OF.get(attr, attr)
    return (max if biggest else min)(scope, key=lambda c: COUNTRIES[c][key])

def h_largest_country(m):
    cont = m.groupdict().get("cont")
    if cont:
        scope = in_continent(_continent_name(cont))
    else:
        scope = list(COUNTRIES)
    c = _superlative(scope, "area", biggest=True)
    return show(c) if c else "no result"

def h_smallest_country(m):
    cont = m.groupdict().get("cont")
    if cont:
        scope = in_continent(_continent_name(cont))
    else:
        scope = list(COUNTRIES)
    c = _superlative(scope, "area", biggest=False)
    return show(c) if c else "no result"

def h_how_large_smallest(m):
    cont = m.groupdict().get("cont")
    if cont:
        scope = in_continent(_continent_name(cont))
    else:
        scope = list(COUNTRIES)
    c = _superlative(scope, "area", biggest=False)
    if c is None:
        return "no result"
    return f"{show(c)} - {country_attr(c, 'area'):,} sq km"

def h_how_large_largest(m):
    cont = m.groupdict().get("cont")
    if cont:
        scope = in_continent(_continent_name(cont))
    else:
        scope = list(COUNTRIES)
    c = _superlative(scope, "area", biggest=True)
    if c is None:
        return "no result"
    return f"{show(c)} - {country_attr(c, 'area'):,} sq km"

def h_longest_river(m):
    cont = m.groupdict().get("cont")
    if cont:
        cont = _continent_name(cont)
        scope_countries = set(in_continent(cont))
        scope = [r for r, d in RIVERS.items()
                 if any(c in scope_countries for c in d["flows_through"])]
    else:
        scope = list(RIVERS)
    if not scope:
        return "no result"
    r = max(scope, key=lambda x: RIVERS[x]["length"])
    return f"{show(r)} ({RIVERS[r]['length']} km)"


# ---- 7. Aggregates --------------------------------------------------- #

def h_total_area_continent(m):
    cont = _continent_name(m.group("cont"))
    cs = in_continent(cont)
    total = sum(COUNTRIES[c]["area"] for c in cs)
    return f"{total:,} sq km"

def h_total_pop_continent(m):
    cont = _continent_name(m.group("cont"))
    cs = in_continent(cont)
    total = sum(COUNTRIES[c]["pop"] for c in cs) * 1000
    return f"{total:,}"

def h_avg_area_per_continent(m):
    lines = []
    for cont in CONTINENTS:
        cs = in_continent(cont)
        if cs:
            avg = sum(COUNTRIES[c]["area"] for c in cs) / len(cs)
            lines.append(f"  {show(cont):<14} {avg:>12,.0f} sq km")
    return "\n" + "\n".join(lines)

def h_more_than_one_per_continent(m):
    lines = []
    for cont in CONTINENTS:
        n = len(in_continent(cont))
        lines.append(f"  {show(cont):<14} {n} ({'yes' if n > 1 else 'no'})")
    return "\n" + "\n".join(lines)


# ---- 8. Filtered queries (population threshold etc.) ----------------- #

def h_countries_pop_exceeding(m):
    amt = parse_amount(m.group("amount"))
    if amt is None:
        return "I couldn't parse that number."
    cs = sorted(c for c, d in COUNTRIES.items() if d["pop"] > amt)
    return show_list(cs)

def h_countries_pop_exceeding_bordering(m):
    amt = parse_amount(m.group("amount"))
    water = m.group("water")
    if amt is None:
        return "I couldn't parse that number."
    on_water = set(countries_on_water(water))
    cs = sorted(c for c in on_water if COUNTRIES[c]["pop"] > amt)
    return show_list(cs)

def h_countries_pop_exceeding_in_continent(m):
    amt = parse_amount(m.group("amount"))
    cont = _continent_name(m.group("cont"))
    if amt is None:
        return "I couldn't parse that number."
    cs = sorted(c for c in in_continent(cont)
                if COUNTRIES[c]["pop"] > amt)
    return show_list(cs)


# ---- 9. Set operations on waters ------------------------------------- #

def h_ocean_borders_two_continents(m):
    """Find an ocean that borders countries in continent A and in continent B.
    Looks at OCEANS only."""
    a = _continent_name(m.group("ca"))
    b = _continent_name(m.group("cb"))
    a_set = set(in_continent(a))
    b_set = set(in_continent(b))
    results = []
    for ocean in OCEANS:
        on = COUNTRIES_ON.get(ocean, set())
        if on & a_set and on & b_set:
            results.append(ocean)
    return show_list(results) if results else "none"


# ---- 10. Landlocked / coastline -------------------------------------- #

def h_landlocked_countries(m):
    cs = sorted(c for c in COUNTRIES if landlocked(c))
    return show_list(cs)

def h_does_have_coastline(m):
    c = m.group("country")
    return "yes" if has_coastline(c) else "no"


# ===================================================================== #
#  PATTERN TABLE                                                        #
#  Order matters: more specific patterns come first.                    #
# ===================================================================== #

PATTERNS: list[tuple[str, Callable]] = [

    # -------- aggregates that must beat 'what is the area of X' -------- #
    (rf"what is total area of (?P<cont>{IN_CONTINENT_RE}) country",
        h_total_area_continent),
    (rf"what is total population of (?P<cont>{IN_CONTINENT_RE}) country",
        h_total_pop_continent),
    (rf"what is average area of (?P<cont>{IN_CONTINENT_RE}) country",
        h_avg_area_per_continent),
    (r"what is average area of country in each continent",
        h_avg_area_per_continent),
    (r"is there more than one country in each continent",
        h_more_than_one_per_continent),

    # -------- superlatives --------------------------------------------- #
    (rf"what is largest (?P<cont>{IN_CONTINENT_RE}) country",
        h_largest_country),
    (rf"which is largest (?P<cont>{IN_CONTINENT_RE}) country",
        h_largest_country),
    (rf"what is largest country (?P<cont>{IN_CONTINENT_RE})",
        h_largest_country),
    (r"what is largest country",                h_largest_country),
    (r"which is largest country",               h_largest_country),
    (rf"what is smallest (?P<cont>{IN_CONTINENT_RE}) country",
        h_smallest_country),
    (rf"which is smallest (?P<cont>{IN_CONTINENT_RE}) country",
        h_smallest_country),
    (r"what is smallest country",               h_smallest_country),
    (rf"how large is smallest (?P<cont>{IN_CONTINENT_RE}) country",
        h_how_large_smallest),
    (r"how large is smallest country",          h_how_large_smallest),
    (rf"how large is largest (?P<cont>{IN_CONTINENT_RE}) country",
        h_how_large_largest),
    (r"how large is largest country",           h_how_large_largest),
    (rf"what is longest river (?P<cont>{IN_CONTINENT_RE})",
        h_longest_river),
    (rf"which is longest (?P<cont>{IN_CONTINENT_RE}) river",
        h_longest_river),
    (r"what is longest river",                  h_longest_river),
    (r"which is longest river",                 h_longest_river),

    # -------- filtered population queries ------------------------------ #
    (rf"which (?P<cont>{IN_CONTINENT_RE}) country have population "
     rf"(?:exceeding|over|of more than|greater than|of over) "
     rf"(?P<amount>[\w. ]+)",
        h_countries_pop_exceeding_in_continent),
    (rf"which country with population "
     rf"(?:exceeding|over|of more than|greater than) "
     rf"(?P<amount>[\w. ]+?) border (?P<water>{WATER_RE})",
        h_countries_pop_exceeding_bordering),
    (rf"which country have population "
     rf"(?:exceeding|over|of more than|greater than|of over) "
     rf"(?P<amount>[\w. ]+)",
        h_countries_pop_exceeding),

    # -------- ocean / sea border queries ------------------------------- #
    (rf"what is ocean that border (?P<ca>{IN_CONTINENT_RE}) country and "
     rf"that border (?P<cb>{IN_CONTINENT_RE}) country",
        h_ocean_borders_two_continents),
    (rf"which ocean border (?P<ca>{IN_CONTINENT_RE}) country and "
     rf"(?P<cb>{IN_CONTINENT_RE}) country",
        h_ocean_borders_two_continents),
    (rf"what country are bordered by (?P<water>{WATER_RE})",
        h_countries_on_water),
    (rf"which country are bordered by (?P<water>{WATER_RE})",
        h_countries_on_water),
    (rf"what country border (?P<water>{WATER_RE})",
        h_countries_on_water),
    (rf"which country border (?P<water>{WATER_RE})",
        h_countries_on_water),
    (rf"what country are bordered by (?P<n>\d+|one|two|three|four|five) sea",
        h_countries_bordered_by_n_seas),
    (rf"which country are bordered by (?P<n>\d+|one|two|three|four|five) sea",
        h_countries_bordered_by_n_seas),
    (rf"what (?:is|are) capital of country bordering (?P<water>{WATER_RE})",
        h_capitals_of_bordering_water),

    # -------- river queries -------------------------------------------- #
    (rf"how many country does (?P<river>{RIVER_RE}) flow through",
        h_count_river_countries),
    (rf"what country does (?P<river>{RIVER_RE}) flow through",
        h_river_flows),
    (rf"which country does (?P<river>{RIVER_RE}) flow through",
        h_river_flows),
    (rf"where does (?P<river>{RIVER_RE}) flow",
        h_river_flows),
    (rf"what river flow through (?P<country>{COUNTRY_RE})",
        h_rivers_through),
    (rf"which river flow through (?P<country>{COUNTRY_RE})",
        h_rivers_through),
    (r"how many river are there",               h_count_rivers),
    (r"what river are there",                   h_list_rivers),
    (r"which river are there",                  h_list_rivers),

    # -------- borders -------------------------------------------------- #
    (rf"does (?P<a>{COUNTRY_RE}) border (?P<b>{COUNTRY_RE})",
        h_does_border),
    (rf"what country border (?P<country>{COUNTRY_RE})",
        h_borders_of),
    (rf"which country border (?P<country>{COUNTRY_RE})",
        h_borders_of),

    # -------- continent listing / counting ----------------------------- #
    (rf"how many country are there (?P<cont>{IN_CONTINENT_RE})",
        h_count_countries),
    (rf"how many country are there in (?P<cont>{CONTINENT_RE})",
        h_count_countries),
    (r"how many country are there",             h_count_countries),
    (rf"which country are (?P<cont>{IN_CONTINENT_RE})",
        h_countries_in_continent),
    (rf"what country are (?P<cont>{IN_CONTINENT_RE})",
        h_countries_in_continent),
    (rf"which country are in (?P<cont>{CONTINENT_RE})",
        h_countries_in_continent),
    (rf"what country are in (?P<cont>{CONTINENT_RE})",
        h_countries_in_continent),

    # -------- landlocked / coastline ----------------------------------- #
    (r"which country are landlocked",           h_landlocked_countries),
    (r"what country are landlocked",            h_landlocked_countries),
    (rf"does (?P<country>{COUNTRY_RE}) have coastline",
        h_does_have_coastline),

    # -------- single-attribute lookups (run late) ---------------------- #
    (rf"what is capital of (?P<country>{COUNTRY_RE})",
        h_capital_of),
    (rf"which country(?: s)? capital is (?P<capital>{CAPITAL_RE})",
        h_country_whose_capital),
    (rf"which country has capital (?P<capital>{CAPITAL_RE})",
        h_country_whose_capital),
    (rf"what is population of (?P<country>{COUNTRY_RE})",
        h_population_of),
    (rf"what is area of (?P<country>{COUNTRY_RE})",
        h_area_of),
    (rf"how large is (?P<country>{COUNTRY_RE})",
        h_area_of),
    (rf"how big is (?P<country>{COUNTRY_RE})",
        h_area_of),
]


# ===================================================================== #
#  TOP-LEVEL ASK                                                        #
# ===================================================================== #

def ask(question: str, verbose: bool = False) -> str:
    text = normalize(question)
    if verbose:
        print(f"  normalised: {text!r}")
        # tokens, tags = tokens_and_tags(question)
        # print(f"  POS-tagged: {tags}")
    for pat, handler in PATTERNS:
        m = re.fullmatch(pat, text)
        if m:
            if verbose:
                print(f"  matched:    {pat}")
            try:
                return handler(m)
            except KeyError as e:
                return f"I have no data for {show(e.args[0])}."
    return "I don't understand that question."


# ===================================================================== #
#  DEMO                                                                 #
# ===================================================================== #

DEMO_QUESTIONS = [
    "What rivers are there?",
    "Does Afghanistan border China?",
    "What is the capital of Upper Volta?",
    "Which countries are European?",
    "Which country's capital is London?",
    "Which is the largest African country?",
    "How large is the smallest American country?",
    "What is the ocean that borders African countries and that borders Asian countries?",
    "What are the capitals of the countries bordering the Baltic?",
    "Which countries are bordered by two seas?",
    "How many countries does the Danube flow through?",
    "What is the total area of African countries?",
    "What is the average area of the countries in each continent?",
    "Is there more than one country in each continent?",
    "Which countries have a population exceeding 100 million?",
    "Which countries with a population exceeding 10 million border the Atlantic?",
    "What is the population of Japan?",
    "What countries border Denmark?",
    "What is the longest river?",
    "Which countries are landlocked?",
    "What is the capital of France?",
    "What is the area of the United States?",
    "How many countries are there?",
    "How many countries are there in Africa?",
]

def run_demo() -> None:
    print("=" * 70)
    print("CHAT-80 demo")
    print("=" * 70)
    for q in DEMO_QUESTIONS:
        print(f"\n? {q}")
        a = ask(q)
        if a.startswith("\n"):
            print(a)
        else:
            print(f"  {a}")


def repl() -> None:
    print("Chat-80 (Python/NLTK).  Type 'quit' to exit, 'demo' to run the demo,")
    print("'help' for what I can answer.")
    while True:
        try:
            q = input("\n? ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        if q.lower() in ("quit", "exit", "bye"):
            break
        if q.lower() == "demo":
            run_demo()
            continue
        if q.lower() == "help":
            print(_HELP)
            continue
        if q.lower().startswith("debug "):
            print(ask(q[6:], verbose=True))
            continue
        print(ask(q))


_HELP = """\
I answer geography questions in roughly the style of Chat-80.  Examples:

  What is the capital of France?
  Which countries are European?
  Which countries border Denmark?
  How many countries are there in Africa?
  Which is the largest African country?
  How large is the smallest American country?
  How many countries does the Danube flow through?
  What rivers flow through Brazil?
  Which countries are bordered by two seas?
  What countries border the Baltic?
  Which countries have a population exceeding 50 million?
  What is the population of Japan?
  Does Afghanistan border China?

Names follow circa-1980 usage (USSR, Upper Volta, East/West Germany, etc.).
Prefix a question with 'debug ' to see how it is normalised and matched.
"""


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            run_demo()
        else:
            print(ask(" ".join(sys.argv[1:])))
    else:
        repl()
