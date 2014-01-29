#!/usr/bin/python
# -*- coding: utf8 -*-

__author__ = "A. Daouzli"
__copyright__ = "Copyright 2013/12"
__licence__ = "GPL3"
__version__ = "0.0.1"
__maintainer__ = "A. Daouzli"

#TODO:
# -generate a return if return is used with argument in element
# -generate raises if raises are used
# -choose input style and output style
# -generate diagnosis/statistics
# -parse classes public methods and list them in class docstring
# -create a real command line management (options, ..., perhaps move PyComment outside and make Pyment a manager)
# -allow excluding files from processing
# -add managing a unique patch
# -manage docstrings templates
#
# -manage c/c++ sources
# -accept archives containing source files
# -dev a server that take sources and send back patches

import os
import re
import difflib

from docstring import DocString


class PyComment(object):
    '''This class allow to manage several python scripts docstrings.
    It is used to parse and rewrite in a Pythonic way all the functions', methods' and classes' docstrings.
    The changes are then provided in a patch file.

    '''
    def __init__(self, input_file, input_style=None, output_style='reST', param_type='standard', cotes="'''"):
        '''Sets the configuration including the source to proceed and options.

        @param input_file: path name (file or folder)
        @param input_style: the type of doctrings format of the output. By default, it will
        autodetect the format for each docstring.
        @param output_style: the docstring docstyle to generate.
        @param param_type: the type of parameters format. Can be:
            - standard:
                The style used is the javadoc style.
                e.g.: @ param my_param: the description
        @param cotes: the type of cotes to use for output: ' ' ' or " " "

        '''
        self.file_type = '.py'
        self.filename_list = []
        self.input_file = input_file
        self.input_style = input_style
        self.output_style = output_style
        self.param_type = param_type
        self.doc_index = -1
        self.file_index = 0
        self.docs_list = []
        self.parsed = False
        self.cotes = cotes

    def _parse(self):
        '''Parses the input file's content and generates a list of its elements/docstrings.

        '''
        #TODO manage decorators
        #TODO manage default params with strings escaping chars as (, ), ', ', #, ...
        #TODO manage multilines
        elem_list = []
        reading_element = False
        reading_docs = None
        waiting_docs = False
        raw = ''
        start = 0
        end = 0
        try:
            fd = open(self.input_file)
        except:
            msg = BaseException('Failed to open file "' + self.input_file + '". Please provide a valid file.')
            raise msg
        for i, ln in enumerate(fd.readlines()):
            l = ln.strip()
            if (l.startswith('def ') or l.startswith('class ')) and not reading_docs:
                # if currently reading an element content
                if reading_element:
                    if reading_docs is not None:
                        #FIXME there is a pb
                        raise Exception('reach new element before end of docstring')
                reading_element = True
                waiting_docs = True
                m = re.match(r'^(\s*)[dc]{1}', ln)
                if m is not None and m.group(1) is not None:
                    spaces = m.group(1)
                else:
                    spaces = ''
                # *** Creates the DocString object ***
                e = DocString(l, spaces, cotes=self.cotes,
                              input_style=self.input_style,
                              output_style=self.output_style)
                elem_list.append({'docs': e, 'location': (-i, -i)})
            else:
                if waiting_docs and ('"""' in l or "'''" in l):
                    # start of docstring bloc
                    if not reading_docs:
                        start = i
                        # determine which delimiter
                        idx_c = l.find('"""')
                        idx_dc = l.find("'''")
                        lim = '"""'
                        if idx_c >= 0 and idx_dc >= 0:
                            if idx_c < idx_dc:
                                lim = '"""'
                            else:
                                lim = "'''"
                        elif idx_c < 0:
                            lim = "'''"
                        reading_docs = lim
                        raw = ln
                        # one line docstring
                        if l.count(lim) == 2:
                            end = i
                            elem_list[-1]['docs'].parse_docs(raw)
                            elem_list[-1]['location'] = (start, end)
                            reading_docs = None
                            waiting_docs = False
                            reading_element = False
                            raw = ''
                    # end of docstring bloc
                    elif waiting_docs and lim in l:
                        end = i
                        raw += ln
                        elem_list[-1]['docs'].parse_docs(raw)
                        elem_list[-1]['location'] = (start, end)
                        reading_docs = None
                        waiting_docs = False
                        reading_element = False
                        raw = ''
                    # inside a docstring bloc
                    elif waiting_docs:
                        raw += ln
                # no docstring found for current element
                elif waiting_docs and l != '' and reading_docs is None:
                    waiting_docs = False
                else:
                    if reading_docs is not None:
                        raw += ln
        fd.close()
        self.docs_list = elem_list
        self.parsed = True
        return elem_list

    def get_output_docs(self):
        '''Return the output docstrings once formated

        @return: the formated docstrings
        @rtype: list

        '''
        if not self.parsed:
            self._parse()
        lst = []
        for e in self.docs_list:
            lst.append(e['docs'].get_raw_docs())
        return lst

    def diff(self, source_path='', target_path='', which=-1):
        '''Build the diff between original docstring and proposed docstring.

        @param which: indicates which docstring to proceed:
        -> -1 means all the dosctrings of the file
        -> >=0 means the index of the docstring to proceed
        @type which: int
        @return: the resulted diff
        @rtype: string

        '''
        #TODO: manage which
        if not self.parsed:
            self._parse()
        try:
            fd = open(self.input_file)
        except:
            msg = BaseException('Failed to open file "' + self.input_file + '". Please provide a valid file.')
            raise msg
        list_from = fd.readlines()
        list_to = []
        last = 0
        for e in self.docs_list:
            start, end = e['location']
            if start < 0:
                start, end = -start, -end
                list_to.extend(list_from[last:start + 1])
            else:
                list_to.extend(list_from[last:start])
            docs = e['docs'].get_raw_docs()
            list_docs = [l + os.linesep for l in docs.split(os.linesep)]
            list_to.extend(list_docs)
            last = end + 1
        fd.close()
        if last < len(list_from):
            list_to.extend(list_from[last:])
        if source_path.startswith(os.sep):
            source_path = source_path[1:]
        if source_path and not source_path.endswith(os.sep):
            source_path += os.sep
        if target_path.startswith(os.sep):
            target_path = target_path[1:]
        if target_path and not target_path.endswith(os.sep):
            target_path += os.sep
        fromfile = 'a/' + source_path + os.path.basename(self.input_file)
        tofile = 'b/' + target_path + os.path.basename(self.input_file)
        diff_list = difflib.unified_diff(list_from, list_to, fromfile, tofile)
        return [d for d in diff_list]

    def diff_to_file(self, patch_file, source_path='', target_path=''):
        '''
        '''
        diff = self.diff(source_path, target_path)
        f = open(patch_file, 'w')
        f.writelines(diff)
        f.close()

    def proceed(self):
        '''
        '''
        self._parse()
        for e in self.docs_list:
            e['docs'].generate_docs()
        return self.docs_list

#########################################################################

import glob
import argparse

MAX_DEPTH_RECUR = 50
''' The maximum depth to reach wargs.hile recursively exploring sub folders'''


def get_files_from_dir(path, recursive=True, depth=0, file_ext='.py'):
    '''Retrieve the list of files from a folder.

    @param path: file or directory where to search files
    @param recursive: if True will search also sub-directories
    @param depth: if explore recursively, the depth of sub directories to follow
    @param file_ext: the files extension to get. Default is '.py'
    @return: the file list retrieved. if the input is a file then a one element list.

    '''
    file_list = []
    if os.path.isfile(path):
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


def main(files=[], input_style='auto', output_style='reST'):
    input_style = None if 'auto' else input_style
    for f in files:
        if os.path.isdir(source):
            path = source + os.sep + os.path.relpath(os.path.abspath(f), os.path.abspath(source))
            path = path[:-len(os.path.basename(f))]
        else:
            path = ''
        c = PyComment(f, cotes='"""',
                      input_style=input_style,
                      output_style=output_style)
        c.proceed()
        c.diff_to_file(os.path.basename(f) + ".patch", path, path)


if __name__ == "__main__":

    desc = 'Pyment %s - %s - %s - %s' % (__version__, __copyright__, __author__, __licence__)
    parser = argparse.ArgumentParser(description='Generates patches after (re)writing docstrings.')
    parser.add_argument('path', type=str,
                        help='python file or folder containing python files to proceed')
    parser.add_argument('-i', '--input', metavar='style', default='auto',
                        dest='input', help='Input docstring style in ["javadoc", "reST", "auto"] (default autodetected)')
    parser.add_argument('-o', '--output', metavar='style', default="reST",
                        dest='output', help='Output docstring style in ["javadoc", "reST"] (default "reST")')
    parser.add_argument('-v', '--version', action='version',
                        version=desc)
    #parser.add_argument('-c', '--config', metavar='config_file',
    #                   dest='config', help='Configuration file')

    args = parser.parse_args()
    source = args.path

    files = get_files_from_dir(source)

    main(files, args.input, args.output)
