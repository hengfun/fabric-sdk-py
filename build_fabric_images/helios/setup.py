import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="disthelios",
    version="0.0.1",
    author="Heng xin Fun",
    author_email="hengfun@gmail.com",
    description="based on Ben adida",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    install_requires=['pycrypto'],
#    py_modules=['algs','elgamal','numtheory','utils','electionalgs','number','randpool'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

