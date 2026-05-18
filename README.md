[![Python application](https://github.com/wiso/ListOfPublicationsFromInspireHEP/actions/workflows/python-app.yml/badge.svg)](https://github.com/wiso/ListOfPublicationsFromInspireHEP/actions/workflows/python-app.yml)
# ListOfPublicationsFromInspireHEP

Create a list of publications from InspireHEP and produce a LaTeX document and a PDF. This tool can be useful when the list is very long and there are some LaTeX errors in the BibTeX entries.

## Install

From a local checkout (classic workflow):

    python -m pip install -r requirements.txt

Install the CLI tools with `pipx` (persistent install):

    pipx install listofpublicationsfrominspirehep

or run one-shot without installing with `uvx`:

    uvx --from listofpublicationsfrominspirehep check_biblio -h
    uvx --from listofpublicationsfrominspirehep create_bibtex -h
    uvx --from listofpublicationsfrominspirehep create_latex -h

## Publish to PyPI

The repository now includes a GitHub Actions workflow that publishes a release to PyPI when you push a tag that starts with `v`.

Typical flow:

1. Bump the version in [pyproject.toml](pyproject.toml) and commit it.
2. Create and push a tag such as `v0.1.1`.
3. GitHub Actions runs tests, builds the wheel/sdist, and publishes to PyPI.

Before the first release, enable trusted publishing for this repository in your PyPI project settings, or replace it with an API token-based setup if you prefer that model.

## How to use it

First create the BibTex file downloading all your bib entries, for the options try:

    create_bibtex -h

it downloads the entries from http://inspirehep.net/ and produces a BibTeX file as `bibtex_2016-02-07.bib`. If you get problems you can download the BibTex from inspire.hep, going on your profile and using the "cite all" button. Actually, this is faster, but you can download only 1000 entries. In this case, you can select a few years on the left and then merge the files.

Usually, many LaTeX errors are present, you can fix them with:

    check_biblio --fix-unicode <bibtexfilename.bib>

Finally to create the pdf:

    create_latex <bibtexfilename_new.bib>
