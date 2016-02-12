# ListOfPublicationsFromInspireHEP
Create a list of publications from InspireHEP and produce a LaTeX document and a pdf.

### How to use it
First create the bibtex file downloading all your bib entry, for the options try:

    ./create-bibtex -h

it downloads the entries from http://inspirehep.net/ and produces a bibtex file as `bibtex_2016-02-07.bib`. Usually many LaTeX errors are present, you can fix them with:

    ./check_biblio.py <bibtexfilename.bib>

Finally to create the pdf:

    ./create_latex.py <bibtexfilename.bib>
