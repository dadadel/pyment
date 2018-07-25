# -*- coding: utf-8 -*-

import os
import re
import difflib
import platform
import sys

from .docstring import DocString

__author__ = "A. Daouzli"
__copyright__ = "Copyright 2012-2018"
__licence__ = "GPL3"
__version__ = "0.3.3"
__maintainer__ = "A. Daouzli"

#TODO:
# -generate a return if return is used with argument in element
# -generate raises if raises are used
# -generate diagnosis/statistics
# -parse classes public methods and list them in class docstring
# -allow excluding files from processing
# -add managing a unique patch
# -manage docstrings templates
# -manage c/c++ sources
# -accept archives containing source files
# -dev a server that take sources and send back patches


class PyComment(object):
    """This class allow to manage several python scripts docstrings.
    It is used to parse and rewrite in a Pythonic way all the functions', methods' and classes' docstrings.
    The changes are then provided in a patch file.

    """
    def __init__(self, input_file, input_style=None, output_style='reST', quotes='"""', first_line=True,
                 convert_only=False, config_file=None, ignore_private=False, **kwargs):
        """Sets the configuration including the source to proceed and options.

        :param input_file: path name (file or folder)
        :param input_style: the type of doctrings format of the output. By default, it will
          autodetect the format for each docstring.
        :param output_style: the docstring docstyle to generate ('javadoc', 'reST', 'groups', 'numpydoc', 'google').
        :param quotes: the type of quotes to use for output: ' ' ' or " " " (default " " ")
        :param first_line: indicate if description should start on first or second line. By default it is True
        :type first_line: boolean
        :param convert_only: if set only existing docstring will be converted. No missing docstring will be created.
        :param config_file: if given configuration file for Pyment
        :param ignore_private: don't proceed the private methods/functions starting with __ (two underscores)

        """
        self.file_type = '.py'
        self.first_line = first_line
        self.filename_list = []
        self.input_file = input_file
        self.input_lines = []  # Need to remember the file when reading off stdin
        self.input_style = input_style
        self.output_style = output_style
        self.doc_index = -1
        self.file_index = 0
        self.docs_list = []
        self.parsed = False
        self.quotes = quotes
        self.convert_only = convert_only
        self.config_file = config_file
        self.ignore_private = ignore_private
        self.kwargs = kwargs

    def _parse(self):
        """Parses the input file's content and generates a list of its elements/docstrings.

        :returns: the list of elements

        """
        #TODO manage decorators
        #TODO manage default params with strings escaping chars as (, ), ', ', #, ...
        #TODO manage elements ending with comments like: def func(param): # blabla
        elem_list = []
        reading_element = None
        reading_docs = None
        waiting_docs = False
        elem = ''
        raw = ''
        start = 0
        end = 0

        try:
            if self.input_file == '-':
                fd = sys.stdin
            else:
                fd = open(self.input_file)

            self.input_lines = fd.readlines()

            if self.input_file != '-':
                fd.close()

        except IOError:
            msg = BaseException('Failed to open file "' + self.input_file + '". Please provide a valid file.')
            raise msg
        for i, ln in enumerate(self.input_lines):
            l = ln.strip()
            if reading_element:
                elem += l
                if l.endswith(':'):
                    reading_element = 'end'
            elif (l.startswith('def ') or l.startswith('class ')) and not reading_docs:
                if self.ignore_private and l[l.find(' '):].strip().startswith("__"):
                    continue
                reading_element = 'start'
                elem = l
                m = re.match(r'^(\s*)[dc]{1}', ln)
                if m is not None and m.group(1) is not None:
                    spaces = m.group(1)
                else:
                    spaces = ''
                if re.search(r''':(|\s*#[^'"]*)$''', l):
                    reading_element = 'end'
            if reading_element == 'end':
                reading_element = None
                # if currently reading an element content
                waiting_docs = True
                # *** Creates the DocString object ***
                e = DocString(elem.replace('\n', ' '), spaces, quotes=self.quotes,
                              input_style=self.input_style,
                              output_style=self.output_style,
                              first_line=self.first_line,
                              **self.kwargs)
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
        if self.convert_only:
            i = 0
            while i < len(elem_list):
                if elem_list[i]['docs'].get_input_docstring() is None:
                    elem_list.pop(i)
                else:
                    i += 1
        self.docs_list = elem_list

        self.parsed = True
        return elem_list

    def docs_init_to_class(self):
        """If found a __init__ method's docstring and the class
        without any docstring, so set the class docstring with __init__one,
        and let __init__ without docstring.

        :returns: True if done
        :rtype: boolean

        """
        result = False
        if not self.parsed:
            self._parse()
        einit = []
        eclass = []
        for e in self.docs_list:
            if len(eclass) == len(einit) + 1 and e['docs'].element['name'] == '__init__':
                einit.append(e)
            elif not eclass and e['docs'].element['type'] == 'class':
                eclass.append(e)
        for c, i in zip(eclass, einit):
            start, _ = c['location']
            if start < 0:
                start, _ = i['location']
                if start > 0:
                    result = True
                    cspaces = c['docs'].get_spaces()
                    ispaces = i['docs'].get_spaces()
                    c['docs'].set_spaces(ispaces)
                    i['docs'].set_spaces(cspaces)
                    c['docs'].generate_docs()
                    i['docs'].generate_docs()
                    c['docs'], i['docs'] = i['docs'], c['docs']
        return result

    def get_output_docs(self):
        """Return the output docstrings once formatted

        :returns: the formatted docstrings
        :rtype: list

        """
        if not self.parsed:
            self._parse()
        lst = []
        for e in self.docs_list:
            lst.append(e['docs'].get_raw_docs())
        return lst

    def compute_before_after(self):
        """Compute the list of lines before and after the proposed docstring changes.

        :return: tuple of before,after where each is a list of lines of python code.
        """
        if not self.parsed:
            self._parse()
        list_from = self.input_lines
        list_to = []
        last = 0
        for e in self.docs_list:
            start, end = e['location']
            if start <= 0:
                start, end = -start, -end
                list_to.extend(list_from[last:start + 1])
            else:
                list_to.extend(list_from[last:start])
            docs = e['docs'].get_raw_docs()
            list_docs = [l + '\n' for l in docs.splitlines()]
            list_to.extend(list_docs)
            last = end + 1
        if last < len(list_from):
            list_to.extend(list_from[last:])

        return list_from, list_to

    def diff(self, source_path='', target_path='', which=-1):
        """Build the diff between original docstring and proposed docstring.

        :type which: int
          -> -1 means all the dosctrings of the file
          -> >=0 means the index of the docstring to proceed (Default value = -1)
        :param source_path:  (Default value = '')
        :param target_path:  (Default value = '')
        :returns: the resulted diff
        :rtype: List[str]
        """
        list_from, list_to = self.compute_before_after()

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

    def get_patch_lines(self, source_path, target_path):
        """Return the diff between source_path and target_path

        :param source_path: name of the original file (Default value = '')
        :param target_path: name of the final file (Default value = '')

        :return: the diff as a list of \n terminated lines
        :rtype: List[str]
        """
        diff = self.diff(source_path, target_path)

        return ["# Patch generated by Pyment v{0}\n\n".format(__version__)] + diff

    def write_patch_file(self, patch_file, lines_to_write):
        """Write lines_to_write to a the file called patch_file

        :param patch_file: file name of the patch to generate
        :param lines_to_write: lines to write to the file - they should be \n terminated
        :type lines_to_write: list[str]

        :return: None
        """
        with open(patch_file, 'w') as f:
            f.writelines(lines_to_write)

    def overwrite_source_file(self, lines_to_write):
        """overwrite the file with line_to_write

        :param lines_to_write: lines to write to the file - they should be \n terminated
        :type lines_to_write: List[str]

        :return: None
        """
        tmp_filename = '{0}.writing'.format(self.input_file)
        ok = False
        try:
            with open(tmp_filename, 'w') as fh:
                fh.writelines(lines_to_write)
            ok = True
        finally:
            if ok:
                if platform.system() == 'Windows':
                    self._windows_rename(tmp_filename)
                else:
                    os.rename(tmp_filename, self.input_file)
            else:
                os.unlink(tmp_filename)

    def _windows_rename(self, tmp_filename):
        """ Workaround the fact that os.rename raises an OSError on Windows
        
        :param tmp_filename: The file to rename
    
        """

        os.remove(self.input_file) if os.path.isfile(self.input_file) else None
        os.rename(tmp_filename, self.input_file)

    def proceed(self):
        """Parses the input file and generates/converts the docstrings.

        :return: the list of docstrings
        :rtype: list of dictionaries

        """
        self._parse()
        for e in self.docs_list:
            e['docs'].generate_docs()
        return self.docs_list
