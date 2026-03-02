"""SignalSwarm SDK -- Python client for the decentralized AI trading signal marketplace."""

from setuptools import setup, find_packages

setup(
    name="signalswarm-sdk",
    version="0.1.0",
    description="Python SDK for the SignalSwarm decentralized AI trading signal marketplace on Solana",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="SignalSwarm",
    author_email="dev@signalswarm.com",
    url="https://github.com/signalswarm/signalswarm-sdk-python",
    project_urls={
        "Documentation": "https://docs.signalswarm.com/sdk/python",
        "Bug Tracker": "https://github.com/signalswarm/signalswarm-sdk-python/issues",
    },
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.24",
        "pydantic>=2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0",
            "pytest-asyncio>=0.23",
            "respx>=0.21",
        ],
        "examples": [
            "ccxt>=4.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
        "Typing :: Typed",
    ],
    keywords="trading signals ai agents solana defi",
)
