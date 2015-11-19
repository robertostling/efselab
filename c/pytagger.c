#include <Python.h>

static PyObject *py_tag(PyObject *self, PyObject *args) {
    PyObject *seq;
    Py_ssize_t buf_len;
    const char *buf;
    if (!PyArg_ParseTuple(args, "y#O", &buf, &buf_len, &seq)) return NULL;
    const real *weights = (real*)buf;
    size_t weights_len = buf_len / sizeof(*weights);
    Py_ssize_t seq_len = PyTuple_Size(seq), i, j;
    uint8_t *field_buf[seq_len*N_TAG_FIELDS];
    size_t field_len[seq_len*N_TAG_FIELDS];

    for (i=0; i<seq_len; i++) {
        PyObject *row = PyTuple_GetItem(seq, i);
        if (PyTuple_Size(row) != N_TAG_FIELDS) return NULL;
        for (j=0; j<N_TAG_FIELDS; j++) {
            PyObject *str = PyTuple_GetItem(row, j);
            field_buf[i*N_TAG_FIELDS + j] = (uint8_t*) PyBytes_AsString(str);
            field_len[i*N_TAG_FIELDS + j] = PyBytes_Size(str);
        }
    }

    label result[seq_len];
    greedy_search(
            (const uint8_t**)field_buf, field_len, N_TAG_FIELDS,
            seq_len, weights, weights_len, 1, result);

    PyObject *tags = PyTuple_New(seq_len);
    for (i=0; i<seq_len; i++)
        PyTuple_SetItem(tags, i, PyBytes_FromString(tag_str[result[i]]));

    return tags;
}

static PyMethodDef py_methods[] = {
    { "tag", py_tag, METH_VARARGS, "Tag one sentence" },
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef py_module = {
    PyModuleDef_HEAD_INIT,
    TAGGER_NAME,
    NULL,
    -1,
    py_methods
};

PyMODINIT_FUNC
PyInit_TAGGER_NAME(void) {
        return PyModule_Create(&py_module);
}

