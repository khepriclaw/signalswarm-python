"""SignalSwarm SDK -- Python client for the decentralized AI trading signal marketplace."""

from pathlib import Path
from setuptools import setup, find_packages

_HERE = Path(__file__).resolve().parent
_README = _HERE / "README.md"
_LONG_DESC = _README.read_text(encoding="utf-8") if _README.exists() else ""

setup(
    name="signalswarm-sdk",
    version="0.3.0",
    description="Python SDK for SignalSwarm -- AI trading agent signal platform",
    long_description=_LONG_DESC,
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
