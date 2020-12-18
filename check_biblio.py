#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from io import open
import subprocess
import tempfile
import re
from glob import glob
import argparse

parser = argparse.ArgumentParser(description='Check LaTeX bibliography',
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog='example: check_biblio bibtex_2016-02-07.bib')
parser.add_argument('bibtex', default="https://inspirehep.net/")
parser.add_argument('--fix-unicode', action='store_true')
parser.add_argument('--use-bibtex', action='store_true', help='use bibtex instead of biblatex')
args = parser.parse_args()

regex_unicode = re.compile('[^\x00-\x7F]')
regex_latex_error = re.compile('Error', re.IGNORECASE)
def help_unicode(item):
    m = regex_unicode.search(item)
    if m:
        print(item[:m.start()] + "***UNICODE****" + item[m.start():m.end()] + "*****UNICODE******" + item[m.end():])


def replace_unicode(item):
    chars = {'\xa0': ' ',
             '\u2009\u2009': ' ',
             '−': '-',
             '∗': '*'}

    def replace_chars(match):
        char = match.group(0)
        print('unicode found, replacing "%s" with "%s"' % (char, chars[char]))
        return chars[char]
    return re.sub('(' + '|'.join(list(chars.keys())) + ')', replace_chars, item)


def write_error_latex(filename):
    with open(filename, 'r') as f:
        log = f.read()
    splitted = log.split('\n')
    for iline, line in enumerate(splitted):
        if regex_latex_error.search(line):
            break
    else:
        print("no error in the output")
        return
    print("error from the log:")
    print('\n    '.join(splitted[iline - 3: iline + 3]))


def modify_item(item):
    editor_command = os.environ.get("EDITOR")
    if not editor_command:
        print("you haven't defined a default EDITOR, (e.g. export EDITOR=emacs)")
        editor_command = input("enter the command to open an editor (e.g. emacs/atom -w/...): ")
        os.environ['EDITOR'] = editor_command
    editor_command = editor_command.strip().split()

    tmp_filename = next(tempfile._get_candidate_names())

    with open(tmp_filename, 'w') as f:
        f.write(item)
    subprocess.call(editor_command + [tmp_filename])
    with open(tmp_filename) as f:
        new_item = f.read()
    os.remove(tmp_filename)
    return new_item

tmp_files = glob('tmp*')
for f in tmp_files:
    os.remove(f)

f = open(args.bibtex)
biblio = f.read()

regex_key = re.compile(r'@[a-z]+\{([A-Za-z0-9\-:]+),')

latex_template_biblatex = r"""
\documentclass{article}
\usepackage[backend=bibtex, style=numeric-comp, sorting=none, firstinits=true, defernumbers=true]{biblatex}
\addbibresource{tmp.bib}
\usepackage{amsmath}
\usepackage[utf8]{inputenc}
\usepackage{syntonly}
\syntaxonly
\begin{document}
Try to cite: \cite{CITATION}.
\printbibliography
\end{document}
"""

latex_template_bibtex = r"""
\documentclass{article}
\usepackage{amsmath}
\usepackage[utf8]{inputenc}
\usepackage{syntonly}
\syntaxonly
\begin{document}
Try to cite: \cite{CITATION}.
\bibliographystyle{unsrt}
\bibliography{tmp}
\end{document}
"""

latex_template = latex_template_bibtex if args.use_bibtex else latex_template_biblatex

try:
    substitutions = []
    biblio_splitted = biblio.split("\n\n")
    nkey = len(biblio_splitted)
    for ikey, item in enumerate(biblio_splitted, 1):
        if '@' not in item:
            continue
        tmp_biblio = open('tmp.bib', 'w')
        if args.fix_unicode:
            item_unicode_fixed = replace_unicode(item)
            if item_unicode_fixed != item:
                substitutions.append((item, item_unicode_fixed))
                item = item_unicode_fixed
        tmp_biblio.write(item)
        tmp_biblio.close()
        m = regex_key.search(item)
        if not m:
            print("cannot match string %s with regex %s" % (item, regex_key.pattern))
        key = m.group(1)

        latex_file = open('tmp.tex', 'w')
        latex = latex_template.replace('CITATION', key)
        latex_file.write(latex)
        latex_file.close()

        error = False
        stdout = open('stdout.temp', 'w+')
        while True:
            print('checking key %s %d/%d' % (key, ikey, nkey))
            try:
                subprocess.check_call(['pdflatex', '-interaction=nonstopmode', 'tmp.tex'], stdout=stdout)
                subprocess.check_call(['bibtex', 'tmp'], stdout=stdout)
                subprocess.check_call(['pdflatex', '-interaction=nonstopmode', 'tmp.tex'], stdout=stdout)
                subprocess.check_call(['pdflatex', '-interaction=nonstopmode', 'tmp.tex'], stdout=stdout)
            except subprocess.CalledProcessError as error:
                print("problem running %s with item %s" % (error.cmd[0], key))
                stdout.flush()
                write_error_latex('stdout.temp')
                help_unicode(item)
                new_item = modify_item(item)
                os.remove('tmp.aux')
                os.remove('tmp.blg')
                os.remove('tmp.bbl')
                with open('tmp.bib', 'w') as f:
                    f.write(new_item)
                substitutions.append((item, new_item))
            else:
                break
finally:
    with open(args.bibtex) as f:
        biblio = f.read()
    for old, new in substitutions:
        biblio = biblio.replace(old, new)
    with open(args.bibtex, 'w') as f:
        f.write(biblio)
    print("%d fixes done" % len(substitutions))
