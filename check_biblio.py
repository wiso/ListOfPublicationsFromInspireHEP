#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import tempfile
import re
import argparse
import sqlite3
import difflib
from typing import Optional

import bibtexparser




def diff_strings(a: str, b: str) -> str:
    output = []
    matcher = difflib.SequenceMatcher(None, a, b)
    green = "\x1b[38;5;16;48;5;2m"
    red = "\x1b[38;5;16;48;5;1m"
    endgreen = "\x1b[0m"
    endred = "\x1b[0m"

    for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
        if opcode == "equal":
            output.append(a[a0:a1])
        elif opcode == "insert":
            output.append(f"{green}{b[b0:b1]}{endgreen}")
        elif opcode == "delete":
            output.append(f"{red}{a[a0:a1]}{endred}")
        elif opcode == "replace":
            output.append(f"{green}{b[b0:b1]}{endgreen}")
            output.append(f"{red}{a[a0:a1]}{endred}")
    return "".join(output)


def help_unicode(item: str) -> Optional[str]:
    m = regex_unicode.search(item)
    if m:
        return (
            item[: m.start()]
            + "***UNICODE****"
            + item[m.start() : m.end()]
            + "*****UNICODE******"
            + item[m.end() :]
        )


def replace_unicode(item: str) -> str:
    """Replace unicode characters with their latex equivalent."""
    chars = {
        "\xa0": " ",
        "\u202f": "",
        "\u2009\u2009": " ",
        "−": "-",
        "∗": "*",
        "Λ": r"\Lambda",
    }

    def replace_chars(match):
        char = match.group(0)
        print('unicode found, replacing "%s" with "%s"' % (char, chars[char]))
        return chars[char]

    return re.sub("(" + "|".join(list(chars.keys())) + ")", replace_chars, item)


def find_error_latex(filename: str) -> str:
    """Find the error in the log file"""
    log = open(filename, "r", encoding="utf-8").read()
    splitted = log.split("\n")
    for iline, line in enumerate(splitted):
        if (
            "error" in line.lower()
            or "! undefined control sequence." in line.lower()
            or "! missing" in line.lower()
        ):
            break
    else:
        return f"cannot find error in log file {filename}"

    return "\n    ".join(splitted[iline - 3 : iline + 3])


def modify_item(item: str, error: str) -> str:
    editor_command = os.environ.get("EDITOR")
    if not editor_command:
        print("you haven't defined a default EDITOR, (e.g. export EDITOR=emacs)")
        editor_command = input(
            "enter the command to open an editor (e.g. emacs/atom -w/...): "
        )
        os.environ["EDITOR"] = editor_command
    editor_command = editor_command.strip()

    tmp_filename = next(tempfile._get_candidate_names())

    with open(tmp_filename, "w", encoding="utf-8") as f:
        preamble = "do not delete these lines\n" "error found:\n"
        preamble += error
        r = help_unicode(item)
        if r is not None:
            preamble += r
        preamble += "\ndo not delete these lines"

        for line in preamble.split("\n"):
            f.write("% " + line + " %\n")

        f.write(item)
    subprocess.call([editor_command] + [tmp_filename])
    new_item = open(tmp_filename, encoding="utf-8").read()
    new_item = "\n".join(
        [line for line in new_item.split("\n") if not line.startswith("%")]
    )
    os.remove(tmp_filename)
    return new_item


def check_latex_entry(key: str, tex: str, use_bibtex: bool = False) -> Optional[str]:
    """Check if the entry is valid latex"""

    latex_template_biblatex = r"""
\documentclass{article}
\usepackage[backend=bibtex, style=numeric-comp, sorting=none,
            firstinits=true, defernumbers=true]{biblatex}
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

    latex_template = latex_template_bibtex if use_bibtex else latex_template_biblatex
    with tempfile.TemporaryDirectory() as tmpdirname:
        open(os.path.join(tmpdirname, "tmp.bib"), "w", encoding="utf-8").write(tex)
        open(os.path.join(tmpdirname, "tmp.tex"), "w", encoding="utf-8").write(
            latex_template.replace("CITATION", key)
        )

        error = None
        stdout_fn = os.path.join(tmpdirname, "stdout.temp")
        stdout = open(stdout_fn, "w+")

        try:
            subprocess.check_call(
                ["pdflatex", "-interaction=nonstopmode", "tmp.tex"],
                stdout=stdout,
                cwd=tmpdirname,
            )
            subprocess.check_call(["bibtex", "tmp"], cwd=tmpdirname, stdout=stdout)
            subprocess.check_call(
                ["pdflatex", "-interaction=nonstopmode", "tmp.tex"],
                stdout=stdout,
                cwd=tmpdirname,
            )
            subprocess.check_call(
                ["pdflatex", "-interaction=nonstopmode", "tmp.tex"],
                stdout=stdout,
                cwd=tmpdirname,
            )
        except subprocess.CalledProcessError:
            stdout.flush()
            error = find_error_latex(stdout_fn)

        return error


def run_entry(entry, cur, substitutions):
    raw_original = entry.raw.strip()
    raw_proposed = raw_original

    try:
        query = "SELECT * FROM entries WHERE original=?"
        res = cur.execute(query, (raw_original,))
        r = res.fetchone()
    except sqlite3.OperationalError as ex:
        print(f"problem executing query {query} with {raw_original}")
        print("error: %s" % ex)
        raise ex
    if r:
        raw_proposed = r[2].strip()
        if raw_original != raw_proposed:
            substitutions.append((raw_original, raw_proposed))
        return

    if args.fix_unicode:
        raw_proposed = replace_unicode(raw_original)
        if raw_proposed != raw_original:
            print(f"unicode found in {entry.key}, fixing")

    while True:
        error = check_latex_entry(entry.key, raw_proposed, args.use_bibtex)
        if error is None:
            break

        print(f"problem running item {entry.key}")
        raw_proposed = modify_item(raw_proposed, error).strip()

    if raw_original != raw_proposed:
        print(diff_strings(raw_original, raw_proposed))
        substitutions.append((raw_original, raw_proposed))
    cur.execute(
        "INSERT INTO entries VALUES (?, ?, ?)",
        (entry.key, raw_original, raw_proposed),
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check LaTeX bibliography",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="example: check_biblio bibtex_2016-02-07.bib",
    )
    parser.add_argument("bibtex", default="https://inspirehep.net/")
    parser.add_argument("--fix-unicode", action="store_true")
    parser.add_argument(
        "--use-bibtex", action="store_true", help="use bibtex instead of biblatex"
    )
    args = parser.parse_args()

    regex_unicode = re.compile("[^\x00-\x7F]")
    regex_latex_error = re.compile("Error", re.IGNORECASE)


    try:
        substitutions = []
        biblio_parsed = bibtexparser.parse_file(args.bibtex)
        con = sqlite3.connect("db.sqlite")
        cur = con.cursor()
        # check if the table exists
        res = cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entries'"
        )
        if not res.fetchone():
            cur.execute("CREATE TABLE entries(key, original, final)")

        print("found %d comments" % len(biblio_parsed.comments))
        print("found %d strings" % len(biblio_parsed.strings))
        print("found %d preambles" % len(biblio_parsed.preambles))
        print("found %d entries" % len(biblio_parsed.entries))

        nentries = len(biblio_parsed.entries)
        for ientry, entry in enumerate(biblio_parsed.entries, 1):
            print("checking key %s %d/%d" % (entry.key, ientry, nentries))
            run_entry(entry, cur, substitutions)

    finally:
        print("committing to database")
        con.commit()

        biblio = open(args.bibtex, encoding="utf-8").read()
        print(f"applying {len(substitutions)} substitutions")
        for old, new in substitutions:
            if old == new:
                print("BIG PROBLEM: old == new")
            print(diff_strings(old, new))
            if old not in biblio:
                print("BIG PROBLEM: old not in biblio")
            biblio = biblio.replace(old, new)
        new_biblio_fn = args.bibtex.replace(".bib", "_new.bib")
        with open(new_biblio_fn, "w", encoding="utf-8") as f:
            f.write(biblio)
