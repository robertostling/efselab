"""Tokenize Swedish plain text data.

This was originally the pipeline by Filip Salomonsson for the Swedish
Treebank, later modified by Robert Östling to use Python 3.
"""

import re

__authors__ = """
Filip Salomonsson <filip.salomonsson@gmail.com>
Robert Östling <robert.ostling@helsinki.fi>
"""

ABBREVS = {
    ('Bl', '.', 'a', '.'): 'Bl.a.',
    ('Bl', 'a'): 'Bl.a',
    ('Bl.a', '.'): 'Bl.a.',
    ('D', 'v', 's'): 'D.v.s',
    ('Fr', 'o', 'm'): 'Fr.o.m',
    ('O', 's', 'v'): 'O.s.v',
    ('S', 'k'): 'S.k',
    ('T', '.', 'ex', '.'): 'T.ex.',
    ('T', 'ex'): 'T.ex',
    ('T', 'o', 'm'): 'T.o.m',
    ('bl', '.', 'a', '.'): 'bl.a.',
    ('bl', 'a'): 'bl.a.',
    ('bl.a', '.'): 'bl.a.',
    ('d', '.', 'v', '.', 's', '.'): 'd.v.s.',
    ('d', 'v', 's'): 'd.v.s.',
    ('d', 'y'): 'd.y',
    ('d.v.s',): 'd.v.s',
    ('dvs', '.'): 'dvs.',
    ('e', '.', 'd', '.'): 'e.d.',
    ('e', 'Kr'): 'e.Kr',
    ('e', 'd'): 'e.d',
    ('etc', '.'): 'etc.',
    ('f', '.', 'n', '.'): 'f.n.',
    ('f', 'Kr'): 'f.Kr',
    ('f', 'd'): 'f.d',
    ('f', 'n'): 'f.n',
    ('f', 'ö'): 'f.ö',
    ('fr', '.', 'o', '.', 'm', '.'): 'fr.o.m.',
    ('fr', 'o', 'm'): 'fr.o.m',
    ('i', 'st', 'f'): 'i.st.f',
    ('m', '.', 'fl', '.'): 'm.fl.',
    ('m', '.', 'm', '.'): 'm.m.',
    ('m', 'a', 'o'): 'm.a.o',
    ('m', 'fl'): 'm.fl',
    ('m', 'fl', '.'): 'm.fl.',
    ('m', 'm'): 'm.m',
    ('m', 'm', '.'): 'm.m.',
    ('m.fl', '.'): 'm.fl.',
    ('m.m', '.'): 'm.m.',
    ('o', '.', 's', '.', 'v', '.'): 'o.s.v.',
    ('o', 'dyl'): 'o.dyl',
    ('o', 's', 'v'): 'o.s.v',
    ('osv', '.'): 'osv.',
    ('p', 'g', 'a'): 'p.g.a',
    ('P', '.', 'g', '.', 'a'): 'P.g.a',
    ('p', '.', 'g', '.', 'a'): 'p.g.a',
    ('P.g.a', '.'): 'P.g.a.',
    ('p.g.a', '.'): 'p.g.a.',
    ('s', '.'): 's.',
    ('s', '.', 'k', '.'): 's.k.',
    ('s', 'a', 's'): 's.a.s',
    ('s', 'k'): 's.k',
    ('s.k', '.'): 's.k.',
    ('t', '.', 'ex'): 't.ex',
    ('t', '.', 'ex', '.'): 't.ex.',
    ('t', '.', 'h', '.'): 't.h.',
    ('t', '.', 'o', '.', 'm', '.'): 't.o.m.',
    ('t', '.', 'v', '.'): 't.v.',
    ('t', 'ex'): 't.ex',
    ('t', 'o', 'm'): 't.o.m',
    ('t', 'o', 'r'): 't.o.r',
    ('t', 'v'): 't.v',
    ('t.ex', '.'): 't.ex.'
}

def build_sentences(data, non_capitalized=False):
    data = data.strip()

    # Basic tokenization
    tokens = tokenize(data)

    # Handle sentences and abbreviations
    marked = join_abbrevs(ABBREVS, tokens, non_capitalized)

    # Chop it into sentences based on the markers that are left
    sentences = group_sentences(marked)

    return sentences

class PeekableIterator:
    def __init__(self, iterable):
        self._iterable = iter(iterable)
        self._cache = []

    def __iter__(self):
        return self

    def _fill_cache(self, n):
        if n is None:
            n = 1
        while len(self._cache) < n:
            self._cache.append(next(self._iterable))

    def __next__(self, n=None):
        self._fill_cache(n)
        if n is None:
            value = self._cache.pop(0)
        else:
            value = [self._cache.pop(0) for i in range(n)]
        return value

    def peek(self, n=None):
        self._fill_cache(n)
        if n is None:
            value = self._cache[0]
        else:
            value = [self._cache[i] for i in range(n)]
        return value

smiley_re = re.compile(r"(?:[:;]'?-?[()DS/])|(?:\^_\^)$")

# Define the tokenizer
tokenizer_re = re.compile(r"""
    [+.]?\d+(?:[ :/,.-]\d+)*   # numeric expressions
    |
    \w+(?:(?=[^/,;:])\S\w+)*-? # word-like stuff
    |                          # ...or...
    (?:[:;]'?-?[()DS/])|(?:\^_\^)
    |                          # ...or...
    (?P<para>\n(\s*\n)+)       # paragraph break
    |
    (?P<char>\S)(?P=char)+
    |
    \S                         # single non-space character
    """, re.UNICODE | re.VERBOSE)

def tokenize(data):
    for match in tokenizer_re.finditer(data):
        if match.group("para") is not None:
            yield None
        else:
            yield match.group(0)


def join_abbrevs(abbrevs, tokens, non_capitalized=False):
    abbrev_prefixes = set()
    for abbrev in abbrevs:
        for i in range(len(abbrev)):
            abbrev_prefixes.add(abbrev[:i + 1])

    if abbrevs:
        max_abbrev_length = max([len(abbrev) for abbrev in abbrevs])
    else:
        max_abbrev_length = 0
    tokens = PeekableIterator(tokens)
    was_abbrev = False

    for token in tokens:
        # Check if any abbreviations start with this token
        if (token,) in abbrev_prefixes:
            longest_candidate = None
            for i in range(max_abbrev_length):
                try:
                    # Peek ahead
                    candidate = (token,) + tuple(tokens.peek(i + 1))
                    if candidate not in abbrev_prefixes:
                        break
                    # Check if we've built a known abbrev.
                    if candidate in abbrevs:
                        # Exclude final "." if the sentence ends with this abbrev.
                        next_token = tokens.peek(i + 1)[-1]
                        if token == "." and next_token is None:
                            break

                        # Emit the normalized abbrev
                        longest_candidate = candidate
                        break
                except StopIteration:
                    # Tried to peek beyond EOF
                    break
            if longest_candidate:
                # Skip over the used tokens
                for _ in longest_candidate[:-1]:
                    next(tokens)
                yield abbrevs[longest_candidate]
                was_abbrev = True
            else:
                yield token
        else:
            # Token not known to start an abbr.; carry on.
            yield token
            # Aaand now for sentence segmentation.
            next_token = tokens.peek()
            if None not in (token, next_token) and \
                    (not was_abbrev) and \
                    (token[-1] in ".:!?" or smiley_re.match(token)) \
                    and (non_capitalized or next_token[0].isupper()):
                yield None
            was_abbrev = False

def group_sentences(tokens):
    """Group tokens into sentences, based on None tokens"""
    sentence = []
    for token in tokens:
        if token is None:
            if sentence:
                yield sentence
            sentence = []
        else:
            sentence.append(token)
    if sentence:
        yield sentence
