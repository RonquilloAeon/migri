from setuptools import setup, find_packages


setup(
    name='migri',
    version='0.1.2',
    install_requires=[
        'aiofiles==0.4.*',
        'asyncpg==0.18.*',
        'click==7.*',
        'sqlparse==0.3.*',
    ],
    entry_points={
        'console_scripts': [
            'migri = migri.main:main'
        ]
    },
    packages=find_packages(),
    include_package_data=True,
    python_requires='~=3.7',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Topic :: Database',
    ]
)
