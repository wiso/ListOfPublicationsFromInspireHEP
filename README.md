[![Python application](https://github.com/wiso/ListOfPublicationsFromInspireHEP/actions/workflows/python-app.yml/badge.svg)](https://github.com/wiso/ListOfPublicationsFromInspireHEP/actions/workflows/python-app.yml)
# ListOfPublicationsFromInspireHEP

Create a list of publications from InspireHEP and produce a LaTeX document and a PDF. This tool can be useful when the list is very long and there are some LaTeX errors in the BibTeX entries.

## Install

From a local checkout (classic workflow):

    python -m pip install -r requirements.txt

CLI tools via `pipx`/`uvx` (no manual clone needed):

1. From PyPI (after publishing):

       pipx install listofpublicationsfrominspirehep

   or run without persistent install:

       uvx --from listofpublicationsfrominspirehep check_biblio -h

2. Directly from GitHub:

       pipx install "git+https://github.com/wiso/ListOfPublicationsFromInspireHEP.git"

   or one-shot execution:

       uvx --from "git+https://github.com/wiso/ListOfPublicationsFromInspireHEP.git" create_bibtex -h

Installed/exposed commands are:

    check_biblio
    create_bibtex
    create_latex

## How to use it

First create the BibTex file downloading all your bib entries, for the options try:

    create_bibtex -h

it downloads the entries from http://inspirehep.net/ and produces a BibTeX file as `bibtex_2016-02-07.bib`. If you get problems you can download the BibTex from inspire.hep, going on your profile and using the "cite all" button. Actually, this is faster, but you can download only 1000 entries. In this case, you can select a few years on the left and then merge the files.

Usually, many LaTeX errors are present, you can fix them with:

    check_biblio --fix-unicode <bibtexfilename.bib>

Finally to create the pdf:

    create_latex <bibtexfilename_new.bib>
