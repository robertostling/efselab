"""
Contains tools for converting corpus data to a format efselab can read, as well
as getting the datadir used to store models for pefselab
"""

from collections import defaultdict

from pathlib import Path
from os import getenv
from os.path import expanduser
import sys


def read_dict(
    filename: str | Path, token_field: int, tag_field: int
) -> tuple[set, defaultdict[str, set]]:
    """Read tagset + tag dictionary from corpus"""
    tags = set()
    norm_tags = defaultdict(set)
    max_field = max(token_field, tag_field)

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            fields = line.rstrip("\n").split("\t")
            if len(fields) > max_field:
                tags.add(fields[tag_field])
                norm_tags[fields[token_field].lower()].add(fields[tag_field])
    return tags, norm_tags


def conll2tab(lfp: list[Path], include_ne: bool = False) -> str:
    """reads a list of Path objects and converts to tab format, returns formatted string"""
    lines: list[str] = []
    for fp in lfp:
        with open(fp, "r") as f:
            lines += [x.rstrip() for x in f]
    result: str = ""
    for line in lines:
        fields = line.rstrip("\n").split("\t")
        if len(fields) >= 6:
            word = fields[1]
            pos = fields[3]
            if pos == "LE":
                pos = "IN"
            tag = pos + "|" + fields[5] if (fields[5] and fields[5] != "_") else pos
            if include_ne and len(fields) >= 12:
                ne = (
                    fields[10]
                    if fields[11] == "_"
                    else ("%s-%s" % (fields[10], fields[11]))
                )
                lemma = fields[2]
                result += word + "\t" + lemma + "\t" + tag + "\t" + ne + "\n"
            else:
                result += word + "\t" + tag + "\n"
        else:
            result += "\n"
    return result


def get_unique_tags(tags: list[str]) -> list:
    """given list of complex tags, return the simple POS
    e.g: VERB|Aspect=PErf|Mood=Ind|Number=Plur -> VERB
    """
    unique_tags: list = list()
    for t in tags:
        unique_tags.append(t.split("|")[0])
    return list(set(unique_tags))


def get_data_dir() -> Path:
    """returns the OS specific data directory; {data_dir}/{pefselab}"""
    os_path: str
    match sys.platform:
        case "win32":
            os_path = str(getenv("LOCALAPPDATA"))
        case "darwin":
            os_path = "~/Library/Application Support"
        case "linux":
            os_path = str(getenv("XDG_DATA_HOME", "~/.local/share"))
        case platform if platform.startswith("freebsd"):
            os_path = str(getenv("XDG_DATA_HOME", "~/.local/share"))
        case _:
            print("ERROR: Platform not recognized. Defaulting to ~/.local/share")
            os_path = "~/.local/share/"
    return Path(expanduser(os_path)).joinpath("pefselab")
