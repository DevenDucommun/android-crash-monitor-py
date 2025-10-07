#!/usr/bin/env python3

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="android-crash-monitor",
    version="2.0.0",
    author="Deven Ducommun",
    author_email="deven@example.com",
    description="A modern, user-friendly Android crash monitoring tool with rich terminal interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DevenDucommun/android-crash-monitor-py",
    project_urls={
        "Bug Tracker": "https://github.com/DevenDucommun/android-crash-monitor-py/issues",
        "Documentation": "https://github.com/DevenDucommun/android-crash-monitor-py/wiki",
        "Source Code": "https://github.com/DevenDucommun/android-crash-monitor-py",
        "Original Project": "https://github.com/DevenDucommun/android-crash-monitor",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Debugging",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        "rich>=13.0.0",
        "click>=8.0.0",
        "requests>=2.28.0",
        "pydantic>=2.0.0",
        "psutil>=5.9.0",
        "packaging>=21.0",
        "platformdirs>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ],
        "build": [
            "pyinstaller>=5.0.0",
            "wheel>=0.38.0",
            "twine>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "acm=android_crash_monitor.cli:main",
            "android-crash-monitor=android_crash_monitor.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="android adb crash monitor debugging logs development mobile",
)