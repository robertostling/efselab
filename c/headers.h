#ifndef __HEADERS_H__
#define __HEADERS_H__

// Using branching hints gives a significant (~10%) speed improvement on my
// system since the innermost loop uses plenty of them.
#define likely(x)       __builtin_expect((x),1)
#define unlikely(x)     __builtin_expect((x),0)

#define MAX_STR         0x1000

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <float.h>

// Uncomment this to do perform separate training over a number of weight
// vector lengths, choosing the best model (on the dev set):
//#define MIN_WEIGHTS_LEN     0x40000
//#define MAX_WEIGHTS_LEN     0x4000000

// Or just fix the length:
#define MIN_WEIGHTS_LEN     0x4000000
#define MAX_WEIGHTS_LEN     0x4000000

// Uncomment this to compress the weight vector after training:
#define POST_TRAINING_COMPRESSION

// A non-zero value means dropout is used, but empirically this doesn't seem
// to help
#define DROPOUT_RATE        0
#define DROPOUT_CONSTANT    ((uint32_t)((double)DROPOUT_RATE*4294967296.0))

typedef float real;
#define REAL_MAX        FLT_MAX

typedef struct {
    uint32_t hash;
    const void *value;
} hash32_kv;

typedef struct {
    uint64_t hash;
    const void *value;
} hash64_kv;

typedef struct {
    uint32_t hash;
    label value;
} hash32_kv_label;

typedef struct {
    uint64_t hash;
    label value;
} hash64_kv_label;

static inline real get_score(
        const feat_hash_t *hashes,
        size_t len,
        const real *weights,
        size_t weights_len,
        int use_dropout,
        feat_hash_t dropout_seed)
{
    size_t i;
    const feat_hash_t mask = (feat_hash_t)weights_len - 1;
    if (use_dropout) {
        real sum = (real)0.0;
        for (i=0; i<len; i++) {
            const feat_hash_t h = hashes[i];
            if (hash32_mix(dropout_seed, h) >= DROPOUT_CONSTANT)
                sum += weights[h & mask];
        }
        // NOTE: since the scale of the feature vector does not matter, we do
        //       not scale the sum here.
        return sum;
    } else {
        real sum = weights[hashes[0] & mask];
        for (i=1; i<len; i++) sum += weights[hashes[i] & mask];
        return sum;
    }
}


#endif

