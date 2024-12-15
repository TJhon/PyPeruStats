from setuptools import setup, find_packages

# Read the README.md file to use it as the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="PY=yPeruStats",  # Package name
    version="0.1.0",  # Initial version
    author="Jhon K. Flores Rojas",  # Author name
    author_email="fr.jhonk@gmail.com",  # Author email
    description="Allows downloading data from various data sources in Peru.",  # Short description
    long_description=long_description if long_description else "No long description provided.",  # Fallback for long description
    long_description_content_type="text/markdown",
    url="https://github.com/TJhon/PyPeruStats",  # Repository URL
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",  # License
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas",
        "requests"
    ],
    project_urls={
        "Bug Tracker": "https://github.com/TJhon/PyPeruStats/issues",
    },
)
