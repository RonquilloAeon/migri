from setuptools import setup, find_packages

VERSION = "0.6.3"


with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="migri",
    version=VERSION,
    long_description=readme,
    long_description_content_type="text/markdown",
    extras_requires={
        "mysql": ["aiomysql"],
        "postgresql": ["asyncpg"],
        "sqlite": ["aiosqlite"],
    },
    install_requires=[
        "asyncpg",  # TODO remove in 1.1.0
        "click==7.*",
        "sqlparse==0.4.*",
    ],
    entry_points={
        "console_scripts": [
            "migri = migri.main:main"
        ]
    },
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Database",
    ],
    url="https://github.com/RonquilloAeon/migri",
)
