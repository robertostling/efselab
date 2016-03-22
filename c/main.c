int main(int argc, const char **argv) {
    if (argc == 5 && !strcmp(argv[1], "train")) {
        if (train(argv[2], argv[3], argv[4])) return 1;
    } else if (argc == 4 && !strcmp(argv[1], "tag")) {
        if (run(argv[2], argv[3], 0)) return 1;
    } else if (argc == 5 && !strcmp(argv[1], "tag") &&
               !strcmp(argv[4], "evaluate")) {
        if (run(argv[2], argv[3], 1)) return 1;
    } else {
        fprintf(stderr,
                "Usage:\n"
                "    %s train train.txt tune.txt model.bin\n"
                "    %s tag input.txt model.bin [evaluate]\n\n"
                "For tagging, the input file may be \"-\" to use stdin\n\n",
                argv[0], argv[0]);
        return 1;
    }
    return 0;
}

