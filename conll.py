suc2ufeat = {
    "AKT": ["Voice=Act"],
    "DEF": ["Definite=Def"],
    "GEN": ["Case=Gen"],
    "IND": ["Definite=Ind"],
    "INF": ["VerbForm=Inf"],
    "IMP": ["VerbForm=Fin", "Mood=Imp"],
    "KOM": ["Degree=Cmp"],
    "KON": ["Mood=Sub"],
    "NEU": ["Gender=Neut"],
    "NOM": ["Case=Nom"],
    "MAS": ["Gender=Masc"],
    "OBJ": ["Case=Acc"],
    "PLU": ["Number=Plur"],
    "POS": ["Degree=Pos"],
    "PRF": ["VerbForm=Part", "Tense=Past"],
    "PRT": ["VerbForm=Fin", "Tense=Past"],
    "PRS": ["VerbForm=Fin", "Tense=Pres"],
    "SFO": ["Voice=Pass"],
    "SIN": ["Number=Sing"],
    "SMS": [],
    "SUB": ["Case=Nom"],
    "SUP": ["VerbForm=Sup"],
    "SUV": ["Degree=Sup"],
    "UTR": ["Gender=Com"],
    "AN": [],
    "-": [],
}


def tagged_to_tagged_conll(tagged, tagged_conll):
    """Read a .tag file and write to the corresponding .tagged.conll file"""
    s_id = 1
    t_id = 1
    for line in tagged:
        line = line.strip()
        if not line:
            print(line, file=tagged_conll)
            s_id += 1
            t_id = 1
            continue
        fields = line.split('\t')
        token = fields[0]
        suc_tags = fields[1]
        ud_tag = suc_tags if len(fields) < 4 else fields[2]
        lemma = '_' if len(fields) < 4 else fields[3]
        ud_features = '_'

        if "|" not in suc_tags:
            print("%s\t%s\t%s\t%s\t%s\t%s" % (
                "%d" % t_id,
                token,
                lemma,
                ud_tag,
                suc_tags,
                ud_features), file=tagged_conll)
            t_id += 1
            continue

        suc_tag, suc_features = suc_tags.split("|", 1)
        ud_feature_list = []
        for suc_feature in suc_features.split("|"):
            # Don't include suc_features with multiple options in the UD suc_features
            if "/" not in suc_feature:
                ud_feature_list += suc2ufeat[suc_feature]

        if "VerbForm=Fin" in ud_feature_list and "Mood=Imp" not in ud_feature_list and "Mood=Sub" not in ud_feature_list:
            ud_feature_list += ["Mood=Ind"]

        if suc_tag in ["HA", "HD", "HP", "HS"]:
            ud_feature_list += ["PronType=Int,Rel"]

        if suc_tag in ["HS", "PS"]:
            ud_feature_list += ["Poss=Yes"]  # Test this!

        ud_features = "|".join(sorted(ud_feature_list)) or "_"

        print("%s\t%s\t%s\t%s\t%s\t%s" % (
            "%d" % t_id,
            token,
            lemma,
            ud_tag,
            suc_tags,
            ud_features), file=tagged_conll)
        t_id += 1
