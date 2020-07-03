from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="migri",
    version="0.2.1",
    long_description=readme,
    long_description_content_type="text/markdown",
    extras_requires={
        # "mysql": ["aiomysql"],  TODO enable when ready
        "postgresql": ["asyncpg"],
        # "sqlite": ["aiosqlite"],  TODO enable when ready
    },
    install_requires=[
        "click==7.*",
        "sqlparse==0.3.*",
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
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Database",
    ]
)
