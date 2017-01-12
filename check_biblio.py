#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from io import open
import subprocess
import tempfile
import re
from glob import glob
import argparse
import difflib

if os.name == "nt":
    try:
        from colorama import init
        init()
    except ImportError:
        print "you should install colorama to see colors on Windows"

parser = argparse.ArgumentParser(description='Check LaTeX bibliography',
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog='example: check_biblio bibtex_2016-02-07.bib')
parser.add_argument('bibtex', default="https://inspirehep.net/")
parser.add_argument('--fix-unicode', action='store_true', help='automatically fix common unicode problems')
parser.add_argument('--fix-atlas', action='store_true', help='automatically fix known problems in ATLAS experiment bibliography')
parser.add_argument('--use-bibtex', action='store_true', help='use bibtex instead of biblatex')
args = parser.parse_args()

regex_unicode = re.compile('[^\x00-\x7F]')
regex_latex_error = re.compile('Error', re.IGNORECASE)
def help_unicode(item):
    m = regex_unicode.search(item)
    if m:
        print item[:m.start()] + "***UNICODE****" + item[m.start():m.end()] + "*****UNICODE******" + item[m.end():]


def replace_unicode(item):
    chars = {u'\xa0': ' ',
             u'\u2009\u2009': ' ',
             u'−': '-'}

    def replace_chars(match):
        char = match.group(0)
        return chars[char]
    return re.sub('(' + '|'.join(chars.keys()) + ')', replace_chars, item)

def fix_atlas(item):
    issues = {u'WW$^{∗}$→eνμν': u'$WW^\ast\to e\nu\mu\nu$'}
    for old, new in issues.iteritems():
        item.replace(old, new)
    return item


def write_error_latex(filename):
    with open(filename, 'r') as f:
        log = f.read()
    splitted = log.split('\n')
    for iline, line in enumerate(splitted):
        if regex_latex_error.search(line):
            break
    else:
        print "no error in the output"
        return
    print "error from the log:"
    print '\n    '.join(splitted[iline - 3: iline + 3])


def modify_item(item):
    editor_command = os.environ.get("EDITOR")
    if not editor_command:
        print "you haven't defined a default EDITOR, (e.g. export EDITOR=emacs)"
        editor_command = raw_input("enter the command to open an editor (e.g. emacs/atom -w/...): ")
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

def show_diff(old, new):
    output_old = ''
    output_new = ''
    sm = difflib.SequenceMatcher(None, old, new)

    for status, a1, a2, b1, b2 in sm.get_opcodes():
        if status == 'equal':
            output_old += sm.a[a1:a2]
            output_new += sm.b[b1:b2]
        else:
            color_old = {'replace': '\033[91m', 'insert': '\033[92m', 'delete': '\033[91m'}[status]
            color_new = {'replace': '\033[92m', 'insert': '\033[92m', 'delete': '\033[91m'}[status]
            output_old += color_old + sm.a[a1:a2] + '\033[0m'
            output_new += color_new + sm.b[b1:b2] + '\033[0m'
    print "<" * 30
    print output_old
    print ">" * 30
    print output_new

def ask(question, choices=None):
    while True:
        answer = raw_input(question)
        if choices is None or answer in choices:
            break
        print "\r"
    return answer
    
tmp_files = glob('tmp*')
for f in tmp_files:
    os.remove(f)

f = open(args.bibtex)
biblio = f.read()

regex_key = re.compile(r'@[a-z]+\{([A-Za-z0-9:]+),')

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

        # automatic fix
        if args.fix_unicode:
            item_unicode_fixed = replace_unicode(item)
            if item_unicode_fixed != item:
                print "unicode fixed"
                show_diff(item, item_unicode_fixed)
                if ask("accept changes [y/n]?", ('y', 'n')) == 'y':
                    substitutions.append((item, item_unicode_fixed))
                    item = item_unicode_fixed
                    
        tmp_biblio = open('tmp.bib', 'w')                    
        tmp_biblio.write(item)
        tmp_biblio.close()
        m = regex_key.search(item)
        key = m.group(1)

        latex_file = open('tmp.tex', 'w')
        latex = latex_template.replace('CITATION', key)
        latex_file.write(latex)
        latex_file.close()

        error = False
        stdout = open('stdout.temp', 'w+')
        while True:
            print 'checking key %s %d/%d' % (key, ikey, nkey)
            try:
                subprocess.check_call(['pdflatex', '-interaction=nonstopmode', 'tmp.tex'], stdout=stdout)
                subprocess.check_call(['bibtex', 'tmp'], stdout=stdout)
                subprocess.check_call(['pdflatex', '-interaction=nonstopmode', 'tmp.tex'], stdout=stdout)
                subprocess.check_call(['pdflatex', '-interaction=nonstopmode', 'tmp.tex'], stdout=stdout)
            except subprocess.CalledProcessError as error:
                print "problem running %s with item %s" % (error.cmd[0], key)
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
    print "%d fixes done" % len(substitutions)
