#!/usr/bin/python
# -*- coding: utf-8 -*-

import glob
import argparse
import os
import sys

from pyment import PyComment
from pyment import __version__, __copyright__, __author__, __licence__


MAX_DEPTH_RECUR = 50
''' The maximum depth to reach while recursively exploring sub folders'''


def get_files_from_dir(path, recursive=True, depth=0, file_ext='.py'):
    """Retrieve the list of files from a folder.

    @param path: file or directory where to search files
    @param recursive: if True will search also sub-directories
    @param depth: if explore recursively, the depth of sub directories to follow
    @param file_ext: the files extension to get. Default is '.py'
    @return: the file list retrieved. if the input is a file then a one element list.

    """
    file_list = []
    if os.path.isfile(path) or path == '-':
        return [path]
    if path[-1] != os.sep:
        path = path + os.sep
    for f in glob.glob(path + "*"):
        if os.path.isdir(f):
            if depth < MAX_DEPTH_RECUR:  # avoid infinite recursive loop
                file_list.extend(get_files_from_dir(f, recursive, depth + 1))
            else:
                continue
        elif f.endswith(file_ext):
            file_list.append(f)
    return file_list


def get_config(config_file):
    """Get the configuration from a file.

    @param config_file: the configuration file
    @return: the configuration
    @rtype: dict

    """
    config = {}
    tobool = lambda s: True if s.lower() == 'true' else False
    if config_file:
        try:
            f = open(config_file, 'r')
        except:
            print ("Unable to open configuration file '{0}'".format(config_file))
        else:
            for line in f.readlines():
                if len(line.strip()):
                    key, value = line.split("=", 1)
                    key, value = key.strip(), value.strip()
                    if key in ['init2class', 'first_line', 'convert_only']:
                        value = tobool(value)
                    config[key] = value
    return config


def run(source, files=[], input_style='auto', output_style='reST', first_line=True, quotes='"""',
        init2class=False, convert=False, config_file=None, ignore_private=False, overwrite=False):
    if input_style == 'auto':
        input_style = None

    config = get_config(config_file)
    if 'init2class' in config:
        init2class = config.pop('init2class')
    if 'convert_only' in config:
        convert = config.pop('convert_only')
    if 'quotes' in config:
        quotes = config.pop('quotes')
    if 'input_style' in config:
        input_style = config.pop('input_style')
    if 'output_style' in config:
        output_style = config.pop('output_style')
    if 'first_line' in config:
        first_line = config.pop('first_line')
    for f in files:
        if os.path.isdir(source):
            path = source + os.sep + os.path.relpath(os.path.abspath(f), os.path.abspath(source))
            path = path[:-len(os.path.basename(f))]
        else:
            path = ''
        c = PyComment(f, quotes=quotes,
                      input_style=input_style,
                      output_style=output_style,
                      first_line=first_line,
                      ignore_private=ignore_private,
                      convert_only=convert,
                      **config)
        c.proceed()
        if init2class:
            c.docs_init_to_class()

        if overwrite:
            list_from, list_to = c.compute_before_after()
            lines_to_write = list_to
        else:
            lines_to_write = c.get_patch_lines(path, path)

        if f == '-':
            sys.stdout.writelines(lines_to_write)
        else:
            if overwrite:
                if list_from != list_to:
                    c.overwrite_source_file(lines_to_write)
            else:
                c.write_patch_file(os.path.basename(f) + ".patch", lines_to_write)


def main():
    desc = 'Pyment v{0} - {1} - {2} - {3}'.format(__version__, __copyright__, __author__, __licence__)
    parser = argparse.ArgumentParser(description='Generates patches after (re)writing docstrings.')
    parser.add_argument('path', type=str,
                        help='python file or folder containing python files to proceed (explore also sub-folders). Use "-" to read from stdin and write to stdout')
    parser.add_argument('-i', '--input', metavar='style', default='auto',
                        dest='input', help='Input docstring style in ["javadoc", "reST", "numpydoc", "google", "auto"] (default autodetected)')
    parser.add_argument('-o', '--output', metavar='style', default="reST",
                        dest='output', help='Output docstring style in ["javadoc", "reST", "numpydoc", "google"] (default "reST")')
    parser.add_argument('-q', '--quotes', metavar='quotes', default='"""',
                        dest='quotes', help='Type of docstring delimiter quotes: \'\'\' or \"\"\" (default \"\"\"). Note that you may escape the characters using \\ like \\\'\\\'\\\', or surround it with the opposite quotes like \"\'\'\'\"')
    parser.add_argument('-f', '--first-line', metavar='status', default="True",
                        dest='first_line', help='Does the comment starts on the first line after the quotes (default "True")')
    parser.add_argument('-t', '--convert', action="store_true", default=False,
                        help="Existing docstrings will be converted but won't create missing ones")
    parser.add_argument('-c', '--config-file', metavar='config', default="",
                        dest='config_file', help='Get a Pyment configuration from a file. Note that the config values will overload the command line ones.')
    parser.add_argument('-d', '--init2class', help='If no docstring to class, then move the __init__ one',
                        action="store_true")
    parser.add_argument('-p', '--ignore-private', metavar='status', default="True",
                        dest='ignore_private', help='Don\'t proceed the private methods/functions starting with __ (two underscores) (default "True")')
    parser.add_argument('-v', '--version', action='version',
                        version=desc)
    parser.add_argument('-w', '--write', action='store_true', dest='overwrite',
                        default=False, help="Don't write patches. Overwrite files instead.")
    # parser.add_argument('-c', '--config', metavar='config_file',
    #                   dest='config', help='Configuration file')

    args = parser.parse_args()
    source = args.path

    files = get_files_from_dir(source)
    if not files:
        msg = BaseException("No files were found matching {0}".format(args.path))
        raise msg
    if not args.config_file:
        config_file = ''
    else:
        config_file = args.config_file

    tobool = lambda s: True if s.lower() == 'true' else False
    run(source, files, args.input, args.output,
        tobool(args.first_line), args.quotes,
        args.init2class, args.convert, config_file,
        tobool(args.ignore_private), overwrite=args.overwrite)


if __name__ == "__main__":
    main()
