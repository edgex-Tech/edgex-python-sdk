from setuptools import setup, find_packages

# Read the README file for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

setup(
    name="edgex-python-sdk",
    version="0.4.0",
    description="A Python SDK for interacting with the EdgeX Exchange API",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="EdgeX Tech",
    author_email="info@edgex.exchange",
    url="https://github.com/edgex-Tech/edgex-python-sdk",
    project_urls={
        "Bug Reports": "https://github.com/edgex-Tech/edgex-python-sdk/issues",
        "Source": "https://github.com/edgex-Tech/edgex-python-sdk",
        "Documentation": "https://github.com/edgex-Tech/edgex-python-sdk#readme",
    },
    packages=find_packages(exclude=["tests*", "examples*"]),
    install_requires=[
        "aiohttp>=3.8.0",
        "websocket-client>=1.0.0",
        "pydantic>=1.8.0",
        "python-dotenv>=0.15.0",
        "pycryptodome>=3.15.0",
        "ecdsa>=0.17.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.800",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Office/Business :: Financial",
    ],
    python_requires=">=3.7",
    keywords="edgex exchange trading api sdk cryptocurrency",
    include_package_data=True,
)
