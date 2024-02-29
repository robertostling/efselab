#ifndef __TAG_C__
#define __TAG_C__

static int tag(
        FILE *infile,
        const real *weights,
        size_t weights_len,
        FILE *outfile,
        size_t n_fields,
        double *error_rate)
{
    size_t i;

    const size_t max_items = 0x400;
    const size_t max_fields = max_items*n_fields;
    size_t max_len = 0x10000;

    uint8_t *field_buf[max_fields];
    size_t field_len[max_fields];
    size_t n_items;
    uint8_t buf[max_len];

    size_t n_total = 0, n_errors = 0;

    for (;;) {
        n_items = max_items;
        size_t buf_len = max_len;
        const int rv = read_sequence(
                infile, field_buf, field_len, n_fields, &n_items,
                buf, &buf_len);
        if (rv < 0) {
            if (!feof(infile)) {
                fprintf(stderr, "Error at %ld!\n", ftell(infile));
                return -1;
            }
            break;
        }

        label result[n_items];
        beam_search(
                (const uint8_t**)field_buf, field_len, n_fields,
                n_items, weights, weights_len, 1, 0, 0, result);

        if (outfile != NULL) {
            for (i=0; i<n_items; i++) {
                size_t j;
                for (j=0; j<N_TRAIN_FIELDS; j++) {
                    if (j == COL_TAG)
                        fputs((char*)tag_str[result[i]], outfile);
                    else if (j < COL_TAG)
                        fputs((char*)field_buf[i*n_fields+j], outfile);
                    else
                        fputs((char*)field_buf[i*n_fields+j-1], outfile);
                    if (j < N_TRAIN_FIELDS-1)
                        fputc('\t', outfile);
                }
                fputc('\n', outfile);
            }
            fputc('\n', outfile);
        }

        if (error_rate != NULL) {
            for (i=0; i<n_items; i++) {
                const int tag = tagset_from_str(
                        (const char*)field_buf[i*n_fields + COL_TAG]);
                if (tag < 0) {
                    fprintf(stderr, "Invalid tag: '%s'\n",
                            field_buf[i*n_fields + COL_TAG]);
                }
                if (result[i] != tag) n_errors++;
                n_total++;
            }
        }

    }

    if (error_rate != NULL) {
        if (n_total > 0) *error_rate = (double)n_errors / (double)n_total;
        else *error_rate = -1.0;
    }

    fflush(outfile);

    return 0;
}

#endif

