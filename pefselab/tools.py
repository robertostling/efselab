from collections import defaultdict

def read_dict(filename, token_field, tag_field):
    """Read tagset + tag dictionary from corpus"""
    tags = set()
    norm_tags = defaultdict(set)
    max_field = max(token_field, tag_field)

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            fields = line.rstrip('\n').split('\t')
            if len(fields) > max_field:
                tags.add(fields[tag_field])
                norm_tags[fields[token_field].lower()].add(fields[tag_field])
    return tags, norm_tags


