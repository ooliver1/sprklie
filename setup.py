from setuptools import setup, find_packages

from tooty import __version__, __author__, __title__, __license__


setup(
    name=__title__,
    version=__version__,
    description="A sphinx theme with accessibility in mind",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author=__author__,
    packages=find_packages(),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Plugins",
        "Framework :: Sphinx",
        "Framework :: Sphinx :: Extension",
        "Framework :: Sphinx :: Theme",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Internet",
        "Topic :: Text Processing :: Markup :: reStructuredText",
    ],
    license=__license__,
    license_files=["LICENSE"],
    install_requires=open("requirements.txt").read().splitlines(),
    project_urls={
        "github": "https://github.com/ooliver1/tooty-theme",
        "issues": "https://github.com/ooliver1/tooty-theme/issues",
    },
    entry_points={
        "sphinx.html_themes": [
            "tooty=tooty",
        ]
    },
)
