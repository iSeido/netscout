from setuptools import setup, find_packages

setup(
    name="netscout",
    version="1.0.0",
    description="Python network scanner for small-office networks",
    author="Ahmed Maghrabi",
    python_requires=">=3.10",
    packages=find_packages(),
    py_modules=["netscout"],
    install_requires=["rich>=13.0.0"],
    entry_points={
        "console_scripts": [
            "netscout=netscout:main",
        ],
    },
)
