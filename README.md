# ListOfPublicationsFromInspireHEP

[![Python application](https://github.com/wiso/ListOfPublicationsFromInspireHEP/actions/workflows/python-app.yml/badge.svg)](https://github.com/wiso/ListOfPublicationsFromInspireHEP/actions/workflows/python-app.yml)

Create a list of publications from InspireHEP and produce a LaTeX document and a PDF. This tool can be useful when the list is very long and there are some LaTeX errors in the BibTeX entries.

## Run it

The simplest way to run the CLI commands once without installing them is `uvx`:

    uvx --from listofpublicationsfrominspirehep listofpublications -h
    uvx --from listofpublicationsfrominspirehep listofpublications check-biblio -h

## Install

The simplest persistent install for end users is `pipx`:

    pipx install listofpublicationsfrominspirehep

After installation, all commands are available:

    listofpublications --help
    listofpublications check-biblio --help
    listofpublications create-bibtex --help
    listofpublications create-latex --help

Legacy individual commands are also available (backward compatible):

    check_biblio --help
    create_bibtex --help
    create_latex --help

From a local checkout, you can still install it with `pip` in editable mode:

    python -m pip install -e .

## Requirements

To generate the final PDF you need a working LaTeX toolchain with `pdflatex` and `bibtex` available in `PATH`.

`check_biblio` also invokes LaTeX checks and may open your editor for manual fixes, so you should also have the `EDITOR` environment variable configured.

## How to use it

First create the BibTeX file downloading all your bib entries:

    listofpublications create-bibtex --help
    listofpublications create-bibtex --query "author%3AR.Turra.1%20and%20collection%3APublished"

This downloads the entries from [inspirehep.net](https://inspirehep.net/) and produces a BibTeX file as `bibtex_YYYY-MM-DD.bib`. 

*Note: If you get problems downloading from INSPIREHEP, you can manually download the BibTeX from inspire.hep going to your profile and using the "cite all" button. However, this is limited to 1000 entries. If needed, select different years and merge the files.*

Then fix LaTeX/Unicode errors:

    listofpublications check-biblio --fix-unicode <bibtexfilename.bib>

Finally generate the PDF:

    listofpublications create-latex <bibtexfilename_new.bib>
