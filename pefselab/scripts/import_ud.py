import sys

for line in sys.stdin:
    line = line.rstrip("\n")
    if line.startswith("#"):
        pass
    elif not line:
        print()
    else:
        fields = line.split("\t")
        print("\t".join([fields[2], fields[4].split("|", 1)[0], fields[4], fields[3]]))
