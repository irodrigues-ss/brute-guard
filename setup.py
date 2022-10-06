from setuptools import setup, find_packages


with open("README.md") as f:
    long_description = f.read()


setup(
    name="brute-guard",
    version="0.1.0",
    description="A Lightweight tool for preventing Brute Force Attacks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Igor Rodrigues Sousa Silva",
    keywords="security brute force attack authentications auth cybersecurity",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    packages=find_packages(),
    python_requires=">=3.7",
)
