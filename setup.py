from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyclassanalyzer",
    version="1.0.1",
    author="s0okju",
    author_email="your.email@example.com",
    description="A tool for analyzing Python class structure and generating PlantUML diagrams",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/s0okju/pyclassanalyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "pyclassanalyzer=pyclassanalyzer.cli:main",
        ],
    },
) 