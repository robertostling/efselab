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
        size_t weights_len)
{
    size_t i;
    const feat_hash_t mask = (feat_hash_t)weights_len - 1;
    real sum = weights[hashes[0] & mask];
    for (i=1; i<len; i++) sum += weights[hashes[i] & mask];
    return sum;
}


#endif

