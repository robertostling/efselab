#ifndef __RUN_C__
#define __RUN_C__

static int run(
        const char *data_filename,
        const char *model_filename,
        int evaluate)
{
    FILE *file = (!strcmp(data_filename, "-"))? stdin :
                 fopen(data_filename, "rb");
    if (file == NULL) {
        fprintf(stderr, "Error: can not open input file %s\n", data_filename);
        return -1;
    }
    FILE *model = fopen(model_filename, "rb");
    if (model == NULL) {
        fprintf(stderr, "Error: can not open model file %s\n", model_filename);
        return -1;
    }

    fseek(model, 0, SEEK_END);
    const size_t weights_len = ftell(model) / sizeof(real);

    if (weights_len & (weights_len-1)) {
        fprintf(stderr, "Model file size not power of 2!\n");
        return -1;
    }
    rewind(model);

    real *weights = malloc(sizeof(real)*weights_len);
    if (weights == NULL) {
        fprintf(stderr, "Error: unable to allocate weight vector memory\n");
        return -1;
    }
    if (fread(weights, sizeof(real), weights_len, model) != weights_len) {
        fprintf(stderr, "Error: unable to read weights vector\n");
        return -1;
    }
    fclose(model);

    double error_rate = 1.0;
    if (tag(file, weights, weights_len, stdout,
            (evaluate)? N_TRAIN_FIELDS : N_TAG_FIELDS,
            (evaluate)? &error_rate : NULL)) {
        fprintf(stderr, "Tagging failed!\n");
        fclose(file);
        free(weights);
        return 1;
    }

    if (evaluate)
        fprintf(stderr, "Error rate: %.2f%%\n", 100.0*error_rate);

    fclose(file);
    free(weights);

    return 0;
}

#endif

