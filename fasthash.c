#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "c/hash.c"

static PyObject *py_hash32(PyObject *self, PyObject *args) {
    const char *str;
    Py_ssize_t str_len;
    unsigned long seed;

    if (!PyArg_ParseTuple(args, "ks#", &seed, &str, &str_len)) return NULL;

    const uint32_t h = hash32_data(seed, str, str_len);

    return PyLong_FromUnsignedLong(h);
}

static PyObject *py_hash64(PyObject *self, PyObject *args) {
    const char *str;
    Py_ssize_t str_len;
    unsigned PY_LONG_LONG seed;

    if (!PyArg_ParseTuple(args, "Ks#", &seed, &str, &str_len)) return NULL;

    const uint64_t h = hash64_data(seed, str, str_len);

    return PyLong_FromUnsignedLongLong(h);
}

static PyObject *py_hashlongs32(PyObject *self, PyObject *args) {
    PyObject *str;

    if (!PyArg_ParseTuple(args, "O", &str)) return NULL;

    const size_t str_len = PyTuple_Size(str);
    uint32_t buf[str_len];
    size_t i;

    for (i=0; i<str_len; i++)
        buf[i] = PyLong_AsUnsignedLong(PyTuple_GET_ITEM(str, i));

    const uint32_t h = hash32_partial_unicode(buf, str_len);

    return PyLong_FromUnsignedLong(hash32_fmix(h));
}

static PyObject *py_hashlongs64(PyObject *self, PyObject *args) {
    PyObject *str;

    if (!PyArg_ParseTuple(args, "O", &str)) return NULL;

    const size_t str_len = PyTuple_Size(str);
    uint32_t buf[str_len];
    size_t i;

    for (i=0; i<str_len; i++)
        buf[i] = PyLong_AsUnsignedLong(PyTuple_GET_ITEM(str, i));

    const uint64_t h = hash64_partial_unicode(buf, str_len);

    return PyLong_FromUnsignedLongLong(hash64_fmix(h));
}


static PyMethodDef py_methods[] = {
    { "hash32", py_hash32, METH_VARARGS, "32-bit hash" },
    { "hash64", py_hash64, METH_VARARGS, "64-bit hash" },
    { "hashlongs32", py_hashlongs32, METH_VARARGS,
        "32-bit hash (tuple of longs)" },
    { "hashlongs64", py_hashlongs64, METH_VARARGS,
        "64-bit hash (tuple of longs)" },
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef py_module = {
    PyModuleDef_HEAD_INIT,
    "fasthash",
    NULL,
    -1,
    py_methods
};

PyMODINIT_FUNC
PyInit_fasthash(void) {
    return PyModule_Create(&py_module);
}

