"""
Setup script for RCA Agent package
"""

from setuptools import setup, find_packages

with open("README_RCA.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements_rca.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="rca-agent",
    version="0.1.0",
    author="RCA Team",
    author_email="team@example.com",
    description="AI Agent for Root Cause Analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rca-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Bug Tracking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
        ],
        "ml": [
            "openai>=1.0.0",
            "langchain>=0.1.0",
        ],
        "integrations": [
            "jira>=3.5.0",
            "GitPython>=3.1.0",
            "slack-sdk>=3.23.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "rca-agent=src.main:main",
        ],
    },
)
