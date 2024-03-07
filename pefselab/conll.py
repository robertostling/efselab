def tagged_to_tagged_conll(annotated_sentences, tagged_conll):
    for line in annotated_sentences:
        for t_id, (word, lemma, ud_tags, suc_tags) in enumerate(line):
            ud_tag, ud_features = ud_tags.split("|", maxsplit=1)

            print(
                "\t".join([str(t_id), word, lemma, ud_tag, suc_tags, ud_features]),
                file=tagged_conll,
            )

        print(file=tagged_conll)
