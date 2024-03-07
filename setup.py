from setuptools import find_packages, setup, Extension
from Cython.Build import cythonize

fasthash = Extension(
    name="pefselab.fasthash",
    sources=["pefselab/fasthash.c", "pefselab/c/hash.c"],
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
    include_package_data=True,
    include_dirs=["pefselab/c"],
    package_data={"": ["build*.py, *.pyx, *.c, *.perl"]},
)
