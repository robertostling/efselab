#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject *py_tag(PyObject *self, PyObject *args) {
    PyObject *seq;
    Py_ssize_t buf_len;
    const char *buf;
    if (!PyArg_ParseTuple(args, "y#O", &buf, &buf_len, &seq)) return NULL;
    if (buf_len & (buf_len-1)) {
        PyErr_SetString(PyExc_ValueError,
                "Weights vector length must be power of 2");
        return NULL;
    }
    int clear_seq = 0;
    if (PyList_Check(seq)) {
        seq = PyList_AsTuple(seq);
        clear_seq = 1;
    } else if (!PyTuple_Check(seq)) {
        PyErr_SetString(PyExc_TypeError, "Expected a list or tuple");
        return NULL;
    }
    const real *weights = (real*)buf;
    size_t weights_len = buf_len / sizeof(*weights);
    Py_ssize_t seq_len = PyTuple_Size(seq), i, j;
    uint8_t *field_buf[seq_len*N_TAG_FIELDS];
    size_t field_len[seq_len*N_TAG_FIELDS];
    PyObject *field_bytes[seq_len*N_TAG_FIELDS];

    for (i=0; i<seq_len; i++) {
        PyObject *row = PyTuple_GetItem(seq, i);
        if (PyUnicode_Check(row)) {
            if (N_TAG_FIELDS != 1) {
                char msg[0x100];
                snprintf(msg, sizeof(msg),
                        "Expected %d fields for token, found single string",
                        N_TAG_FIELDS);
                PyErr_SetString(PyExc_ValueError, msg);
                return NULL;
            }
            PyObject *buf = PyUnicode_AsEncodedString(row, "utf-8", NULL);
            if (PyBytes_Size(buf) >= MAX_STR) {
                char msg[0x100];
                snprintf(msg, sizeof(msg),
                        "Input string too long: %zd bytes",
                        PyBytes_Size(buf));
                PyErr_SetString(PyExc_ValueError, msg);
                return NULL;
            }
            field_buf[i*N_TAG_FIELDS + 0] = (uint8_t*)PyBytes_AsString(buf);
            field_len[i*N_TAG_FIELDS + 0] = PyBytes_Size(buf);
            field_bytes[i*N_TAG_FIELDS + 0] = buf;
        } else {
            int clear_row = 0;
            if (PyList_Check(row)) {
                row = PyList_AsTuple(row);
                clear_row = 1;
            }
            if (!PyTuple_Check(row)) {
                PyErr_SetString(PyExc_TypeError,
                        "Expected tuple, list or str for token");
                return NULL;
            }
            if (PyTuple_Size(row) != N_TAG_FIELDS) {
                char msg[0x100];
                snprintf(msg, sizeof(msg),
                        "Expected %d fields for token, found %zd",
                        N_TAG_FIELDS, PyTuple_Size(row));
                PyErr_SetString(PyExc_ValueError, msg);
                return NULL;
            }
            for (j=0; j<N_TAG_FIELDS; j++) {
                PyObject *str = PyTuple_GetItem(row, j);
                if (PyBytes_Check(str)) {
                    if (PyBytes_Size(str) >= MAX_STR) {
                        char msg[0x100];
                        snprintf(msg, sizeof(msg),
                                "Input string too long: %zd bytes",
                                PyBytes_Size(str));
                        PyErr_SetString(PyExc_ValueError, msg);
                        return NULL;
                    }
                    field_buf[i*N_TAG_FIELDS + j] =
                        (uint8_t*)PyBytes_AsString(str);
                    field_len[i*N_TAG_FIELDS + j] = PyBytes_Size(str);
                    field_bytes[i*N_TAG_FIELDS + j] = NULL;
                } else if(PyUnicode_Check(str)) {
                    PyObject *buf = PyUnicode_AsEncodedString(
                            str, "utf-8", NULL);
                    if (PyBytes_Size(buf) >= MAX_STR) {
                        char msg[0x100];
                        snprintf(msg, sizeof(msg),
                                "Input string too long: %zd bytes",
                                PyBytes_Size(buf));
                        PyErr_SetString(PyExc_ValueError, msg);
                        return NULL;
                    }
                    field_buf[i*N_TAG_FIELDS + j] =
                        (uint8_t*)PyBytes_AsString(buf);
                    field_len[i*N_TAG_FIELDS + j] = PyBytes_Size(buf);
                    field_bytes[i*N_TAG_FIELDS + j] = buf;
                } else {
                    PyErr_SetString(PyExc_TypeError, "Expected bytes or str");
                    return NULL;
                }
            }
            if (clear_row) Py_CLEAR(row);
        }
    }

    label result[seq_len];
    beam_search(
            (const uint8_t**)field_buf, field_len, N_TAG_FIELDS,
            seq_len, weights, weights_len, 1, 0, 0, result);

    PyObject *tags = PyTuple_New(seq_len);
    for (i=0; i<seq_len; i++)
        PyTuple_SetItem(tags, i, PyUnicode_FromString(tag_str[result[i]]));

    for (i=0; i<seq_len; i++) {
        for (j=0; j<N_TAG_FIELDS; j++) {
            Py_CLEAR(field_bytes[i*N_TAG_FIELDS + j]);
        }
    }
    if (clear_seq) Py_CLEAR(seq);

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

