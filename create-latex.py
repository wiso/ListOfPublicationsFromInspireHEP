import subprocess
import argparse

parser = argparse.ArgumentParser(description='Create pdf with bibliography',
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog='example: create-latex bibtex_2016-02-07.bib')
parser.add_argument('bibtex')
args = parser.parse_args()

TEMPLATE_FILENAME = "template_latex.tex"
with open(TEMPLATE_FILENAME) as f:
    template = f.read()

template = template.replace("ADD_BIBTEX_HERE", args.bibtex)
with open('publications.tex', 'w') as f:
    f.write(template)

subprocess.call(['pdflatex', 'publications.tex'])
subprocess.call(['bibtex', 'publications.aux'])
subprocess.call(['pdflatex', 'publications.tex'])
subprocess.call(['pdflatex', 'publications.tex'])

print "output written in publications.pdf"
