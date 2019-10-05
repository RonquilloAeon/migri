from setuptools import setup, find_packages


setup(
    name="migri",
    install_requires=[
        'Click',
    ],
    entry_points={
        'console_scripts': [
            'migri = migri.main:main'
        ]
    },
    packages=find_packages(),
)
