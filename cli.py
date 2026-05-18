#!/usr/bin/env python

import sys
import argparse
from check_biblio import main as check_biblio_main
from create_bibtex import main as create_bibtex_main
from create_latex import main as create_latex_main


def main() -> None:
    """Main CLI entry point with subcommands."""
    # If user calls a subcommand directly, delegate without parsing
    if len(sys.argv) > 1 and sys.argv[1] in ('check-biblio', 'create-bibtex', 'create-latex'):
        command = sys.argv[1]
        # Reconstruct argv for the subcommand module
        sys.argv = [command] + sys.argv[2:]
        
        if command == 'check-biblio':
            check_biblio_main()
        elif command == 'create-bibtex':
            create_bibtex_main()
        elif command == 'create-latex':
            create_latex_main()
        return
    
    # Otherwise, show main help
    parser = argparse.ArgumentParser(
        description='Publication management tools from INSPIREHEP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
examples:
  listofpublications create-bibtex --query "author%3AR.Turra.1"
  listofpublications check-biblio bibliography.bib
  listofpublications create-latex bibliography.bib
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # check-biblio subcommand
    subparsers.add_parser(
        'check-biblio',
        help='Check and fix LaTeX/Unicode errors in BibTeX bibliography',
        add_help=False
    )
    
    # create-bibtex subcommand
    subparsers.add_parser(
        'create-bibtex',
        help='Create BibTeX bibliography from INSPIREHEP API',
        add_help=False
    )
    
    # create-latex subcommand
    subparsers.add_parser(
        'create-latex',
        help='Generate PDF from BibTeX file using LaTeX',
        add_help=False
    )
    
    args = parser.parse_args()
    
    if args.command == 'check-biblio':
        sys.argv = ['check-biblio'] + sys.argv[2:]
        check_biblio_main()
    elif args.command == 'create-bibtex':
        sys.argv = ['create-bibtex'] + sys.argv[2:]
        create_bibtex_main()
    elif args.command == 'create-latex':
        sys.argv = ['create-latex'] + sys.argv[2:]
        create_latex_main()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

