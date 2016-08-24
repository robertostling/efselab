#ifndef __TRAIN_C__
#define __TRAIN_C__

#include <stdlib.h>
#include <errno.h>

static void shuffle(size_t *items, size_t len) {
    size_t i;
    for (i=0; i<len; i++) {
        size_t j = random() % len;
        size_t t = items[i];
        items[i] = items[j];
        items[j] = t;
    }
}

static int train(
        const char *train_filename,
        const char *tune_filename,
        const char *model_filename)
{
    FILE *train_file = fopen(train_filename, "rb");
    FILE *tune_file = fopen(tune_filename, "rb");
    const int use_dropout = DROPOUT_RATE != 0;

    if (train_file == NULL) {
        perror("unable to open training data file");
        exit(1);
    }

    if (tune_file == NULL) {
        perror("unable to open tuning data file");
        exit(1);
    }

    size_t i;

    const size_t max_items = 0x400;
    const size_t max_fields = max_items*N_TRAIN_FIELDS;
    const size_t max_len = 0x10000;
    
    double best_error_ever = 1.0;

    FILE *model = NULL;

    feat_hash_t dropout_seed = 1;

    uint8_t *field_buf[max_fields];
    size_t field_len[max_fields];
    size_t n_items;
    uint8_t buf[max_len];

    // First, get file offsets of sentence starts
    size_t max_sents = 0x100000;
    size_t n_sents;
    long *sent_offsets = malloc(sizeof(long)*max_sents);

    for (n_sents=0; ; n_sents++) {
        if (n_sents >= max_sents) {
            return 1;
        }
        sent_offsets[n_sents] = ftell(train_file);
        n_items = max_items;
        size_t buf_len = max_len;
        const int rv = read_sequence(
                train_file, field_buf, field_len, N_TRAIN_FIELDS, &n_items,
                buf, &buf_len);
        if (rv < 0) {
            if (!feof(train_file)) {
                fprintf(stderr, "Error at %s:%ld (bytes)!\n",
                        train_filename, ftell(train_file));
                return 1;
            }
            rewind(train_file);
            break;
        }
    }

    sent_offsets = realloc(sent_offsets, sizeof(long)*n_sents);
    size_t sent_order[n_sents];
    for (i=0; i<n_sents; i++) sent_order[i] = i;

    fprintf(stderr, "Training data contains %zd sentences\n", n_sents);

    size_t weights_len;
    for (weights_len=MIN_WEIGHTS_LEN;
         weights_len<=MAX_WEIGHTS_LEN;
         weights_len*=2)
    {
        fprintf(stderr, "Trying weight vector of size 0x%zx\n", weights_len);
        real *weights = malloc(sizeof(real)*weights_len);
        // Even elements contain averages of the weights vector,
        // odd elements contain the time (i.e. value of t) of the last update
        // of the average.
        // This is less elegant, but good for cache locality since these values
        // are accessed randomly at the same time.
        // TODO: might also want to get the weight vector itself into the same
        // area.
        double *average_weights = malloc(sizeof(double)*weights_len*2);
        double t = 0.0;

        for (i=0; i<weights_len; i++) weights[i] = (real)0.0;
        for (i=0; i<weights_len*2; i++) average_weights[i] = 0.0;

        size_t iter;
        double tune_error_avg = 1.0;
        double best_error = 1.0;

        const int max_patience = 5;
        int patience_left = max_patience;

        double tune_error = 1.0;
        for (iter=0; ; iter++) {
            shuffle(sent_order, n_sents);

            fprintf(stderr, "Iteration %zd...\n", iter+1);
            size_t n_errs = 0;
            size_t n_total = 0;
            size_t sent;
            for (sent=0; sent<n_sents; sent++) {
                fseek(train_file, sent_offsets[sent_order[sent]], SEEK_SET);

                n_items = max_items;
                size_t buf_len = max_len;
                const int rv = read_sequence(
                        train_file, field_buf, field_len, N_TRAIN_FIELDS,
                        &n_items, buf, &buf_len);
                if (rv < 0) {
                    fprintf(stderr, "Error at %s:%ld (bytes)!\n",
                            train_filename, ftell(train_file));
                    return 1;
                }

                label gold[n_items];
                for (i=0; i<n_items; i++) {
                    const int tag = tagset_from_str(
                            (const char*)field_buf[i*N_TRAIN_FIELDS + COL_TAG]);
                    if (tag < 0) {
                        fprintf(stderr, "Invalid tag: '%s'\n",
                                field_buf[i*N_TRAIN_FIELDS + COL_TAG]);
                    }
                    gold[i] = tag;
                }

                n_total += n_items;
                n_errs += train_sequence(
                        (const uint8_t**)field_buf, field_len, N_TRAIN_FIELDS,
                        n_items, weights, weights_len, gold,
                        t, average_weights,
                        use_dropout, dropout_seed);
                t += 1.0;
                dropout_seed++;
            }

            fprintf(stderr, "  Training error: %.2f%%\n",
                    100.0*(double)n_errs/(double)n_total);

            for (i=0; i<weights_len; i++) {
                average_weights[i*2] +=
                    (t - average_weights[i*2+1]) * (double)weights[i];
                average_weights[i*2+1] = t;
            }

            tune_error = 1.0;

            real *real_average_weights = malloc(sizeof(real)*weights_len);
            for (i=0; i<weights_len; i++)
                real_average_weights[i] = (real)average_weights[i*2];
            tag(tune_file, real_average_weights, weights_len, NULL, 
                N_TRAIN_FIELDS, &tune_error);
            rewind(tune_file);

            fprintf(stderr, "  Tuning error:   %.2f%%\n", 100.0*tune_error);

            if (tune_error < best_error_ever) {
                best_error_ever = tune_error;

                fprintf(stderr, "  Best so far, writing...\n");

                model = fopen(model_filename, "wb");
                if (model == NULL) {
                    perror("unable to open model file for writing");
                    exit(1);
                }
                fwrite(real_average_weights, sizeof(real), weights_len, model);
                fclose(model);
            }

            free(real_average_weights);

            if (tune_error < best_error) {
                best_error = tune_error;
                patience_left = max_patience;
            }
            if (iter == 0) {
                tune_error_avg = tune_error;
            } else {
                if (tune_error > 0.99*tune_error_avg) {
                    if (! (--patience_left)) break;
                }
                tune_error_avg = tune_error_avg*0.5 + tune_error*0.5;
            }
        }

        for (i=0; i<weights_len; i++)
            weights[i] = (real)average_weights[i*2];

        free(average_weights);

#ifdef POST_TRAINING_COMPRESSION
        fprintf(stderr, "Finding optimal feature compression...\n");

        model = fopen(model_filename, "rb");
        if (model == NULL) {
            perror("unable to open model file for reading");
            exit(1);
        }
        fread(weights, sizeof(real), weights_len, model);
        fclose(model);

        size_t compressed_len = weights_len;
        size_t compression;
        for (compression=2; ; compression*=2) {
            compressed_len /= 2;
            real *folded_weights = malloc(sizeof(real)*compressed_len);
            for (i=0; i<compressed_len; i++)
                folded_weights[i] = weights[i] + weights[compressed_len+i];
            tune_error = 1.0;
            tag(tune_file, folded_weights, compressed_len, NULL, N_TRAIN_FIELDS,
                &tune_error);
            rewind(tune_file);
            fprintf(stderr, "  %zdx compression tuning error: %.2f%%\n",
                    compression, 100.0*tune_error);
            if (tune_error > 1.0025 * best_error) {
                free(folded_weights);
                fprintf(stderr, "Selected %zdx compression: 0x%zx features\n",
                        compression/2, compressed_len*2);
                compressed_len *= 2;
                break;
            }
            free(weights);
            weights = folded_weights;
            if (tune_error < best_error) best_error = tune_error;
            if (tune_error < best_error_ever) best_error_ever = tune_error;
        }

        model = fopen(model_filename, "wb");
        if (model == NULL) {
            perror("unable to open model file for writing");
            exit(1);
        }
        fwrite(weights, sizeof(real), compressed_len, model);
        fclose(model);
#endif

        free(weights);

        if (best_error > best_error_ever*1.0025) {
            fprintf(stderr, "Error no longer decreasing with compression.\n");
            break;
        }
    }

    fclose(train_file);
    fclose(tune_file);

    return 0;
}

#endif

