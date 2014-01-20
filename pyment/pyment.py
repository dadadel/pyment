#!/usr/bin/python
# -*- coding: utf8 -*-

__author__ = "A. Daouzli"
__copyright__ = "Copyright dec. 2013, A. Daouzli"
__licence__ = "GPL3"
__version__ = "0.0.1"
__maintainer__ = "A. Daouzli"

#TODO:
# -generate a return if return is used with argument in element
# -file managing only in proceed (remove init open and release)
# -choose input style and output style
# -generate diagnosis/statistics
# -parse classes public methods and list them in class docstring
# -create a real command line management (options, ..., perhaps move PyComment outside and make Pyment a manager)
# -add auto tests
# -allow excluding files from processing
# -add managing a unique patch
# -manage docstrings templates
#
# -manage c/c++ sources
# -accept archives containing source files
# -dev a server that take sources and send back patches

import os
import sys
import re
import difflib

from docstring import DocString


class PyComment(object):
    '''This class allow to manage several python scripts docstrings.
    It is used to parse and rewrite in a Pythonic way all the functions', methods' and classes' docstrings.
    The changes are then provided in a patch file.

    '''
    def __init__(self, input_file, doc_type='normal', param_type='standard', cotes="'''"):
        '''Sets the configuration including the source to proceed and options.

        @param input_file: path name (file or folder)
        @param doc_type: the type of doctrings format. Can be:
            - normal:
                Comment on the first line, a blank line to separate the params and a blank line at the end
                e.g.: def method(test):
                        >"""The comment for this method.
                        >
                        >@ param test: the param test comment
                        >@ return: the result of the method
                        >
                        >"""
        @param param_type: the type of parameters format. Can be:
            - standard:
                The style used is the javadoc style.
                e.g.: @param my_param: the description
        @param cotes: the type of cotes to use for output: ' ' ' or " " "

        '''
        self.file_type = '.py'
        self.filename_list = []
        self.input_file = input_file
        self.doc_type = doc_type
        self.param_type = param_type
        self.doc_index = -1
        self.file_index = 0
        self.docs_list = []
        self.parsed = False
        self.cotes = cotes

    def _get_next(self):
        '''Get the current file's next docstring

        '''

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
                e = DocString(l, spaces, cotes=self.cotes)
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

    def diff(self, which=-1):
        '''Build the diff between original docstring and proposed docstring.

        @param which: indicates which docstring to proceed:
        -> -1 means all the dosctrings of the file
        -> >=0 means the index of the docstring to proceed
        @type which: int
        @return: the resulted diff
        @rtype: string

        '''
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
            list_docs = [l + '\n' for l in docs.split('\n')]
            list_to.extend(list_docs)
            last = end + 1
        fd.close()
        if last < len(list_from):
            list_to.extend(list_from[last:])
        fromfile = 'a/' + os.path.basename(self.input_file)
        tofile = 'b/' + os.path.basename(self.input_file)
        diff_list = difflib.unified_diff(list_from, list_to, fromfile, tofile)
        return [d for d in diff_list]

    def diff_to_file(self, patch_file):
        '''
        '''
        diff = self.diff()
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


if __name__ == "__main__":

    import glob

    MAX_DEPTH_RECUR = 50
    ''' The maximum depth to reach while recursively exploring sub folders'''

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
                if depth < MAX_DEPTH_RECUR:  # avoid recursive loop
                    file_list.extend(get_files_from_dir(f, recursive, depth + 1))
                else:
                    continue
            elif f.endswith(file_ext):
                file_list.append(f)
        return file_list

    source = sys.argv[0]

    if len(sys.argv) > 1:
        source = sys.argv[1]

    files = get_files_from_dir(source)

    for f in files:
        c = PyComment(f, cotes='"""')
        c.proceed()
        c.diff_to_file(os.path.basename(f) + ".patch")
