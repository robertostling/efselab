#ifndef __HASH_C__
#define __HASH_C__

#include <stdint.h>
#include <string.h>
#include <stddef.h>

// Code adapted from: http://bjoern.hoehrmann.de/utf-8/decoder/dfa/

#define UTF8_ACCEPT 0
#define UTF8_REJECT 12

static const uint8_t utf8d[] = {
  // The first part of the table maps bytes to character classes that
  // to reduce the size of the transition table and create bitmasks.
   0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
   0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
   0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
   0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
   1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,  9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,
   7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,  7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,
   8,8,2,2,2,2,2,2,2,2,2,2,2,2,2,2,  2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,
  10,3,3,3,3,3,3,3,3,3,3,3,3,4,3,3, 11,6,6,6,5,8,8,8,8,8,8,8,8,8,8,8,

  // The second part is a transition table that maps a combination
  // of a state of the automaton and a character class to a state.
   0,12,24,36,60,96,84,12,12,12,48,72, 12,12,12,12,12,12,12,12,12,12,12,12,
  12, 0,12,12,12,12,12, 0,12, 0,12,12, 12,24,12,12,12,12,12,24,12,24,12,12,
  12,12,12,12,12,12,12,24,12,12,12,12, 12,24,12,12,12,12,12,12,12,24,12,12,
  12,12,12,12,12,12,12,36,12,36,12,12, 12,36,12,12,12,12,12,36,12,36,12,12,
  12,36,12,12,12,12,12,12,12,12,12,12, 
};

static inline void utf8_step(uint32_t *state, uint32_t *codep, uint32_t byte) {
    const uint32_t type = utf8d[byte];
    
    *codep = (*state != UTF8_ACCEPT) ?
        (byte & 0x3fu) | (*codep << 6) :
        (0xff >> type) & (byte);
    *state = utf8d[256 + *state + type];
}

static inline int utf8_decode(
        uint32_t *dest,
        size_t *dest_len,
        const uint8_t *src,
        size_t src_len)
{
    size_t i;
    uint32_t state = 0;
    uint32_t codep;
    size_t j = 0;
    for (i=0; i<src_len; i++) {
        utf8_step(&state, &codep, src[i]);
        if (!state) {
            dest[j++] = codep;
            if (j >= *dest_len) return -1;
        }
    }
    *dest_len = j;
    if (state != UTF8_ACCEPT) return -1;
    return 0;
}

static inline uint32_t rotl32(uint32_t x, int r) {
    return (x << r) | (x >> (32 - r));
}

static inline uint64_t rotl64(uint64_t x, int r) {
    return (x << r) | (x >> (64 - r));
}

static inline uint32_t hash32_mix(uint32_t x, uint32_t y) {
    x = rotl32(x * 0xcc9e2d51, 15) * 0x1b873593;
    y = rotl32(y ^ x, 13) * 5 + 0xe6546b64;
    return y;
}

static inline uint64_t hash64_mix(uint64_t x, uint64_t y) {
    x = rotl64(x * 14029467366897019727ULL, 31) * 11400714785074694791ULL;
    y = rotl64(y ^ x, 31) * 5 + 0xbdef9f91b243c6e6ULL;
    return y;
}

static inline uint32_t hash32_mix_tail(uint32_t x, uint32_t y) {
    x = rotl32(x * 0xcc9e2d51, 15) * 0x1b873593;
    return y ^ x;
}

static inline uint64_t hash64_mix_tail(uint64_t x, uint64_t y) {
    x = rotl64(x * 14029467366897019727ULL, 31) * 11400714785074694791ULL;
    return y ^ x;
}

static inline uint32_t hash32_fmix(uint32_t x) {
    x = 0x85ebca6b * (x ^ (x >> 16));
    x = 0xc2b2ae35 * (x ^ (x >> 13));
    return x ^ (x >> 16);
}

static inline uint64_t hash64_fmix(uint64_t x) {
    x = (x ^ (x >> 33)) * 14029467366897019727ULL;
    x = (x ^ (x >> 29)) * 1609587929392839161ULL;
    return x ^ (x >> 32);
}

static inline uint32_t hash32_partial_unicode(
        const uint32_t *p,
        size_t len)
{
    if (len == 0) return 0x3a5c441;

    uint32_t h1 = p[0];
    size_t i;

    for (i=1; i<len; i++)
        h1 = hash32_mix(p[i], h1);

    return h1 ^ (uint32_t)len;
}

static inline uint64_t hash64_partial_unicode(
        const uint32_t *p,
        size_t len)
{
    if (len == 0) return 0x7fb838a8a0a95046ULL;

    uint64_t h1 = (len == 1)? (uint64_t)p[0] :
                              ((uint64_t)p[0] | ((uint64_t)p[1] << 32));
    size_t i;

    for (i=1; i<len/2; i++)
        h1 = hash64_mix((uint64_t)p[i*2] | ((uint64_t)p[i*2+1] << 32), h1);

    if (len % 2)
        h1 = hash64_mix((uint64_t)p[len-1], h1);

    return h1 ^ (uint64_t)len;
}

static inline uint32_t hash32_partial_unicode_suffix(
        const uint32_t *p,
        size_t len,
        size_t suffix_len,
        size_t min_stem)
{
    if (min_stem + suffix_len > len) return 0x34b020cc;
    return hash32_partial_unicode(p+(len-suffix_len), suffix_len);
}

static inline uint64_t hash64_partial_unicode_suffix(
        const uint32_t *p,
        size_t len,
        size_t suffix_len,
        size_t min_stem)
{
    if (min_stem + suffix_len > len) return 0xb9d9d9fb4440f7bbULL;
    return hash64_partial_unicode(p+(len-suffix_len), suffix_len);
}

static inline uint32_t hash32_partial_unicode_prefix(
        const uint32_t *p,
        size_t len,
        size_t prefix_len,
        size_t min_stem)
{
    if (min_stem + prefix_len > len) return 0x719986aa;
    return hash32_partial_unicode(p, prefix_len);
}

static inline uint64_t hash64_partial_unicode_prefix(
        const uint32_t *p,
        size_t len,
        size_t prefix_len,
        size_t min_stem)
{
    if (min_stem + prefix_len > len) return 0xc1a7bd3b4e853fc9ULL;
    return hash64_partial_unicode(p, prefix_len);
}

static inline uint32_t read32(const void *p) {
    uint32_t x;
    memcpy(&x, p, sizeof(x));
    return x;
}

static inline uint64_t read64(const void *p) {
    uint64_t x;
    memcpy(&x, p, sizeof(x));
    return x;
}

static inline uint32_t read32_part(const void *p, size_t len) {
    const uint8_t *b = p;
    if (len == 3) return b[0] | (b[1] << 8) | (b[2] << 16);
    else if (len == 2) return b[0] | (b[1] << 8);
    return b[0];
}

static inline uint64_t read64_part(const void *p, size_t len) {
    const uint8_t *b = p;
    uint64_t x = b[0];
    switch (len) {
        case 6: x |= (uint64_t)b[6] << 48;
        case 5: x |= (uint64_t)b[5] << 40;
        case 4: x |= (uint64_t)b[4] << 32;
        case 3: x |= (uint64_t)b[3] << 24;
        case 2: x |= (uint64_t)b[2] << 16;
        case 1: x |= (uint64_t)b[1] << 8;
    }
    return x;
}

static uint32_t hash32_data(uint32_t seed, const void *ptr, size_t len) {
    uint32_t h1 = seed;
    size_t i;

    for (i=0; i+4<=len; i+=4)
        h1 = hash32_mix(read32(ptr+i), h1);

    if (len-i)
        h1 = hash32_mix_tail(read32_part(ptr+i, len-i), h1);

    return hash32_fmix(h1 ^ (uint32_t)len);
}

static uint64_t hash64_data(uint64_t seed, const void *ptr, size_t len) {
    uint64_t h1 = seed;
    size_t i;

    for (i=0; i+8<=len; i+=4)
        h1 = hash64_mix(read64(ptr+i), h1);

    if (len-i)
        h1 = hash64_mix_tail(read64_part(ptr+i, len-i), h1);

    return hash64_fmix(h1 ^ (uint64_t)len);
}

// TODO: less naive implementation, if necessary
static uint32_t hash32_utf8_prefix(
        const void *p,
        size_t len,
        size_t prefix_len,
        size_t min_stem)
{
    uint32_t buf[len];
    size_t buf_len = len;
    utf8_decode(buf, &buf_len, p, len);
    return hash32_fmix(
            hash32_partial_unicode_prefix(buf, buf_len, prefix_len, min_stem));
}

// TODO: less naive implementation, if necessary
static uint32_t hash32_utf8_suffix(
        const void *p,
        size_t len,
        size_t suffix_len,
        size_t min_stem)
{
    uint32_t buf[len];
    size_t buf_len = len;
    utf8_decode(buf, &buf_len, p, len);
    return hash32_fmix(
            hash32_partial_unicode_suffix(buf, buf_len, suffix_len, min_stem));
}

#endif

