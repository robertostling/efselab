from setuptools import find_packages, setup, Extension
from Cython.Build import cythonize

fasthash = Extension(
    name="pefselab.fasthash",
    sources=["pefselab/fasthash.c"],
    extra_compile_args=["-Wall"],
)

lemmatize = Extension(
    name="pefselab.lemmatize",
    sources=["pefselab/lemmatize.pyx"],
)

setup(
    name="pefselab",
    description="packaged version of Östling et al. efselab algorithm.",
    packages=find_packages(),
    ext_modules=cythonize([lemmatize, fasthash]),
)
