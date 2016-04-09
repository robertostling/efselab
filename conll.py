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
        tag = fields[1]
        ud_tag = tag if len(fields) < 4 else fields[2]
        lemma = '_' if len(fields) < 4 else fields[3]
        ud_morph = '_'
        if "|" in tag:
            pos, morph = tag.split("|", 1)
            ufeats = []
            feats = morph.split("|")
            for f in feats:
                if "/" in f:
                    uf = "" # don't include feats with multiple options in the UD feats
                else:
                    uf = suc2ufeat[f]
                if uf != "":
                    ufeats = ufeats + suc2ufeat[f]
            if "VerbForm=Fin" in ufeats and not "Mood=Imp" in ufeats and not "Mood=Sub" in ufeats:
                ufeats = ufeats + ["Mood=Ind"]
            if pos in ["HA", "HD", "HP", "HS"]:
                ufeats = ufeats + ["PronType=Int,Rel"]
            if pos in ["HS", "PS"]:
                ufeats = ufeats + ["Poss=Yes"] # Test this!
            ufeat_string = "|".join(sorted(ufeats))
            if ufeat_string != "":
                ud_morph = ufeat_string
        else:
            pos = tag
            morph = "_"
        print("%s\t%s\t%s\t%s\t%s\t%s" % (
            "%d" % t_id,
            token,
            lemma,
            ud_tag,
            tag,
            ud_morph), file=tagged_conll)
        t_id += 1
