# ListOfPublicationsFromInspireHEP

[![Python application](https://github.com/wiso/ListOfPublicationsFromInspireHEP/actions/workflows/python-app.yml/badge.svg)](https://github.com/wiso/ListOfPublicationsFromInspireHEP/actions/workflows/python-app.yml)

Create a list of publications from InspireHEP and produce a LaTeX document and a PDF. This tool can be useful when the list is very long and there are some LaTeX errors in the BibTeX entries.

## Run it

The simplest way to run the CLI commands once without installing them is `uvx`:

    uvx --from listofpublicationsfrominspirehep check_biblio -h
    uvx --from listofpublicationsfrominspirehep create_bibtex -h
    uvx --from listofpublicationsfrominspirehep create_latex -h

## Install

The simplest persistent install for end users is `pipx`:

    pipx install listofpublicationsfrominspirehep

After installation, the commands are available directly:

    check_biblio -h
    create_bibtex -h
    create_latex -h

From a local checkout, you can still install it with `pip` in editable mode:

    python -m pip install -e .

## Requirements

To generate the final PDF you need a working LaTeX toolchain with `pdflatex` and `bibtex` available in `PATH`.

`check_biblio` also invokes LaTeX checks and may open your editor for manual fixes, so you should also have the `EDITOR` environment variable configured.

## How to use it

First create the BibTeX file downloading all your bib entries, for the options try:

    create_bibtex -h

it downloads the entries from [inspirehep.net](https://inspirehep.net/) and produces a BibTeX file as `bibtex_2016-02-07.bib`. If you get problems you can download the BibTex from inspire.hep, going on your profile and using the "cite all" button. Actually, this is faster, but you can download only 1000 entries. In this case, you can select a few years on the left and then merge the files.

Usually, many LaTeX errors are present, you can fix them with:

    check_biblio --fix-unicode <bibtexfilename.bib>

Finally to create the PDF:

    create_latex <bibtexfilename_new.bib>
