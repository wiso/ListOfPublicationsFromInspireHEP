#!/usr/bin/env python

import subprocess
import argparse

def main() -> None:
    parser = argparse.ArgumentParser(description='Create pdf with bibliography',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog='example: create_latex bibtex_2016-02-07.bib')
    parser.add_argument('bibtex')
    args = parser.parse_args()

    template_filename = "template_latex.tex"
    with open(template_filename, 'r', encoding='utf-8') as f:
        template = f.read()

    template = template.replace("ADD_BIBTEX_HERE", args.bibtex)
    with open('publications.tex', 'w', encoding='utf-8') as f:
        f.write(template)

    subprocess.call(['pdflatex', 'publications.tex'])
    subprocess.call(['bibtex', 'publications.aux'])
    subprocess.call(['pdflatex', 'publications.tex'])
    subprocess.call(['pdflatex', 'publications.tex'])

    print("output written in publications.pdf")


if __name__ == "__main__":
    main()
