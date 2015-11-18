#ifndef __SEARCH_C__
#define __SEARCH_C__

#include <string.h>

static void adjust_weights(
        const uint8_t **field_buf,
        const size_t *field_len,
        size_t n_fields,
        size_t n_items,
        real *weights,
        size_t weights_len,
        const label *labels,
        real weight_diff,
        double t,
        double *average_weights)
{
    size_t i, j;
    feat_hash_t invariant_hashes[N_INVARIANTS*n_items];
    feat_hash_t feature_hashes[N_FEATURES];
    feat_hash_t mask = (feat_hash_t)weights_len - 1;

    extract_invariant(
            field_buf, field_len, n_fields, n_items, invariant_hashes);

    for (i=0; i<n_items; i++) {
        extract_features(
                labels, labels[i], i, n_items,
                invariant_hashes, feature_hashes);
        for (j=0; j<N_FEATURES; j++) {
            const size_t idx = feature_hashes[j] & mask;
            average_weights[idx*2] +=
                (t - average_weights[idx*2+1]) * (double)weights[idx];
            average_weights[idx*2+1] = t;
            weights[idx] += weight_diff;
        }
    }
}

static size_t train_sequence(
        const uint8_t **field_buf,
        const size_t *field_len,
        size_t n_fields,
        size_t n_items,
        real *weights,
        size_t weights_len,
        const label *gold,
        double t,
        double *average_weights)
{
    label crap[n_items];
    greedy_search(field_buf, field_len, n_fields, n_items,
                  weights, weights_len, 0, crap);
    if (!memcmp(crap, gold, n_items*sizeof(label))) return 0;
    size_t n_errs = 0;
    size_t i;
    for (i=0; i<n_items; i++)
        n_errs += (gold[i] != crap[i]);
    adjust_weights(field_buf, field_len, n_fields, n_items,
                   weights, weights_len, gold, (real)1.0, t, average_weights);
    adjust_weights(field_buf, field_len, n_fields, n_items,
                   weights, weights_len, crap, (real)(-1.0), t, average_weights);
    return n_errs;
}

#endif

