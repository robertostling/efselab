#ifndef __SEQ_C__
#define __SEQ_C__

// If the output should be aligned, set this to 1.
#define ALIGN_FIELDS    0
#define ALIGNMENT       (sizeof(size_t))

// If fields should be zero-terminated, set this to 1.
#define ZERO_TERMINATE  1

static int read_sequence(
        FILE *file,
        uint8_t **field_buf,
        size_t *field_len,
        size_t n_fields,
        size_t *n_items,
        uint8_t *buf,
        size_t *buf_len)
{
    const size_t max_items = *n_items;
    size_t field, item, field_p = 0, buf_p = 0;
    const size_t max_len = *buf_len;

    for (item=0; item<max_items; item++) {
        for (field=0; field<n_fields; field++) {
#if ALIGN_FIELDS
            while (buf_p % ALIGNMENT) buf[buf_p++] = 0;
            if (unlikely(buf_p >= max_len)) return -1;
#endif
            const size_t buf_p_start = buf_p;
            for (;;) {
                const int c = getc_unlocked(file);
                if (likely(c > '\n')) {
                    if (unlikely(buf_p >= max_len)) return -1;
                    buf[buf_p++] = c;
                } else if (unlikely(c == '\t')) {
                    if (unlikely(field == n_fields-1)) return -1;
                    field_buf[field_p] = buf + buf_p_start;
                    if ((field_len[field_p] = buf_p - buf_p_start) >= MAX_STR) {
                        field_len[field_p] = MAX_STR-1;
                        buf[buf_p_start + MAX_STR-1] = 0;
                    }
                    field_p++;
#if ZERO_TERMINATE
                    if (unlikely(buf_p >= max_len)) return -1;
                    buf[buf_p++] = 0;
#endif
                    break;
                } else if (unlikely(c == '\n')) {
                    if (unlikely(field == 0 && buf_p == buf_p_start)) {
                        *n_items = item;
                        *buf_len = buf_p;
                        return 0;
                    }
                    if (unlikely(field != n_fields-1)) return -1;
                    field_buf[field_p] = buf + buf_p_start;
                    if ((field_len[field_p] = buf_p - buf_p_start) >= MAX_STR) {
                        field_len[field_p] = MAX_STR-1;
                        buf[buf_p_start + MAX_STR-1] = 0;
                    }
                    field_p++;
#if ZERO_TERMINATE
                    if (unlikely(buf_p >= max_len)) return -1;
                    buf[buf_p++] = 0;
#endif
                    break;
                } else if (unlikely(c == EOF)) return -1;
                // For the time being, silently drop ASCII values below 10
                // except newline and tab.
            }
        }
    }
    return -1;
}

#endif


