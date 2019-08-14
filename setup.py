# -*- coding: utf-8 -*-

import pathlib
import re

from setuptools import setup

ROOT = pathlib.Path(__file__).parent

with (ROOT / "discord" / "ext" / "timers" / "__init__.py").open(encoding="utf-8") as f:
    version = re.search(r"^__version__\s*=\s*['\"]([^'\"]*)['\"]", f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError("Version is not set.")

with (ROOT / "README.md").open(encoding="utf-8") as f:
    readme = f.read()

setup(
    name="discord-timers",
    author="Lorenzo",
    url="https://github.com/PendragonLore/discord-timers",
    license="MIT",
    description="Timers for bots made with discord.py",
    long_description=readme,
    long_description_content_type="text/markdown",
    project_urls={
        "Code": "https://github.com/PendragonLore/discord-timers",
        "Issue tracker": "https://github.com/PendragonLore/discord-timers/issues",
    },
    version=version,
    packages=["discord.ext.timers"],
    platforms=["any"],
    python_requires=">=3.5.3",
    include_package_data=True,
    keywords="asyncio, discord, timers",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Framework :: AsyncIO",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Development Status :: 3 - Alpha",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Internet",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries",
    ]
)
