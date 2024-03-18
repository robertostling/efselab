# pefselab

[![pypi](https://img.shields.io/pypi/v/pefselab.svg)](https://pypi.org/pypi/pefselab)
![build status](https://github.com/skogsgren/pefselab/workflows/Testkit/badge.svg)

P[yPi]ackaged Efficient Sequence Labeling

A packaged version of [`efselab`](https://github.com/robertostling/efselab),
intentionally scaled down in terms of available options in order to be more
easily downloaded and accessed without manual intervention and compilation.

## Requirements

A C-compiler:

- **Windows**: Install WSL[^1] (instructions [here](https://learn.microsoft.com/en-us/windows/wsl/install))
- **Mac**: Install XCode  (instructions [here](https://developer.apple.com/support/xcode/))
- **Linux**: `gcc` is already installed. You're good.

[^1]: This is seriously the most widely recommended way from what I could gather.
      Kind of ironic if you ask me.

## Installation

`pip3 install pefselab`

## Usage

Running `python3 -m pefselab` prints information relevant to `pefselab`,
including the data directory where models are stored as well as the available
models for use. This can also be accessed programmatically (along with the
variables used to print it; for example if one is writing code to test all the
models currently trained) using the following code:

```python
from pefselab.wrappers import Info

pefselab_info: Info = Info()
```

If more customized models are required than the ways detailed below then I
refer to the original `efselab` to create them. If those models are then copied
to the model directory (see `python3 -m pefselab` for where it's located) then
they should become available in `pefselab` as well.

### Universal Dependency (UD) Part-of-Speech (POS) Tagger

To create a UD POS tagger the following code deals with both downloading UD
Treebanks, preprocessing, building and training. Let's pick
[`UD_French_GSD`](https://universaldependencies.org/treebanks/fr_gsd/).

```python
from pefselab.train_udt import udt_pipeline

udt_pipeline("UD_French_GSD")
```

This trains the model and puts it in the model directory. Then we can access it
through the `Model` wrapper. Note that the `Model` wrapper uses the UD
langcode, which we can get programmatically using the `pefselab.Info` wrapper,
or manually by running `python3 -m pefselab` and looking under available
models.

```python
from pefselab.wrappers import Model

french_pos_tagger: Model = Model("udfr_gsd")
french_pos_tagger.tag("""
Au milieu de la rue Saint-Denis, presque au coin de la
rue du Petit-Lion, existait naguère une de ces maisons précieuses qui donnent
aux historiens la facilité de reconstruire par analogie l'ancien Paris.
""")
```

Which produces the following output:

```
('_', 'NOUN|Gender=Masc|Number=Sing', 'ADP',
'DET|Definite=Def|Gender=Fem|Number=Sing|PronType=Art',
'NOUN|Gender=Fem|Number=Sing', 'PROPN', 'ADV', '_',
'NOUN|Gender=Masc|Number=Sing', 'ADP',
'DET|Definite=Def|Gender=Fem|Number=Sing|PronType=Art',
'NOUN|Gender=Fem|Number=Sing',
'DET|Definite=Ind|Gender=Masc|Number=Sing|PronType=Art',
'NOUN|Gender=Masc|Number=Sing',
'VERB|Mood=Ind|Number=Sing|Person=3|Tense=Imp|VerbForm=Fin', 'ADV',
'PRON|Gender=Fem|Number=Sing|Person=3|PronType=Ind', 'ADP',
'DET|Number=Plur|PronType=Dem', 'NOUN|Gender=Fem|Number=Plur',
'ADJ|Gender=Fem|Number=Plur', 'PRON|PronType=Rel',
'VERB|Mood=Ind|Number=Plur|Person=3|Tense=Pres|VerbForm=Fin', '_',
'NOUN|Gender=Masc|Number=Plur',
'DET|Definite=Def|Gender=Fem|Number=Sing|PronType=Art',
'NOUN|Gender=Fem|Number=Sing', 'ADP', 'VERB|VerbForm=Inf', 'ADP',
'NOUN|Gender=Fem|Number=Sing', 'ADJ|Gender=Fem|Number=Sing', 'PROPN')
```

### Swedish Pipeline

To run the Swedish pipeline on two text-files, `file1.txt` and `file2.txt`, one
can use the following code:

```python
from pefselab.train_swe_pipeline import create_pipeline
from pefselab.swe_pipeline import SwedishPipeline, pipeline_available

if not pipeline_available():
    create_pipeline()

nlp: SwedishPipeline = SwedishPipeline(
    ["file1.txt", "file2.txt"]
)
```

This automatically downloads the Swedish pipeline to the datadirectory, builds
it and trains it. The tagged data is then available in the SwedishPipeline
object in the `documents` class variable, which is a dataclass with the
following variables:

```
path:       path to file
tokens:     list of tokens
ud_tags:    list of universal dependency tags (index matches with tokens above)
suc_tags:   list of SUC tags (index matches with tokens above)
ner_tags:   list of NER tags (index matches with tokens above)
```

The different components of the pipeline can be switched on and off depending
on ones needs. By default it uses the following flags. Disable/enable at your
own whim.

```python
nlp: SwedishPipeline = SwedishPipeline(
    ["file1.txt", "file2.txt"],
    tagger=True,
    ner_tagger=True,
    ud_tagger=True,
    lemmatizer=True,
    skip_tokenization=False,
    skip_segmentation=False,
    non_capitalization=False,
)
```

One can also save all document results to json files using
`SwedishPipelineObject.save()` with an optional parameter for where to save
them. For the example above we could write the following code to save it to a
folder called "results":

```python
nlp.save("results")
```

This would create two files inside `./results`: `file1.json` and `file2.json`.

### Parsing

Adding parsing would require some hefty dependencies (most notably `pytorch`)
so I opted to remove the parsing capability in `efselab`; however, if it is
needed one can easily convert the handled documents in `SwedishPipeline`
objects through the `as_stanza_parse_struct` method. For example, if I wanted
to parse `file1.txt` above, then I would use this code (after installing
`stanza` using `pip3 install stanza`):

```python
import stanza
from stanza.models.common.doc import Document
from pefselab.swe_pipeline import SwedishPipeline

nlp: SwedishPipeline = SwedishPipeline(
    ["file1.txt", "file2.txt"]
)

stanza_pipeline: stanza.Pipeline = stanza.Pipeline(
    lang='sv',
    processors='depparse',
    depparse_pretagged=True
)

pretagged_doc: Document = Document([nlp.as_stanza_parse_struct("file1.txt")])
parsed_doc: Document = nlp(pretagged_doc)
```

## Future work

The code for the Swedish pipeline could easily be rewritten in a way so that
it's universally applicable rather than specific to Swedish, but I didn't have
the time.

Pull requests are welcome!
