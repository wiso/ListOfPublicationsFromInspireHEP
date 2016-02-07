# ListOfPublicationsFromInspireHEP
Create a list of publications from InspireHEP and produce a LaTeX document (by now it only produces a corrected bibtex file).

### How to use it
First create the bibtex file downloading all your bib entry, for the options try:

    ./create-bibtex -h

it downloads the entry from http://inspirehep.net/. Usually many LaTeX errors are present, you can fix them with:

    ./check_biblio.py <bibtexfilename.bib>


