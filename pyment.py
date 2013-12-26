#!/usr/bin/python

import os
import sys
import glob

from docstring import DocString

class PyComment(object):
    '''This class allow to manage several python scripts docstrings.
    It is used to parse and rewrite in a Pythonic way all the methods and classes docstrings.

    '''

    MAX_DEPTH_RECUR = 50
    ''' The maximum depth to reach while recursively exploring sub folders'''

    def __init__(self, source, output_prefix='pyment_', doc_type='normal', param_type='standard', recursive=True):
        '''Set the configuration including the source to proceed and options.

        @param source: path name (file or folder)
        @param output_prefix: if given will be added at the beginning of each file so it will not modify the original. 
        If None the original file will be updated. By default will add "pyment_"
        @param doc_type: the type of doctrings format. Can be:
            - normal:
                Comment on the first line, a blank line to separate the params and a blank line at the end
                e.g.: def method(test):
                        """The comment for this method.

                        @param test: the param test comment
                        @return: the result of the method

                        """
        @param param_type: the type of parameters format. Can be:
            - standard:
                The style used is the Doxygen default style.
                e.g.: @param my_param: the description
        @param recursive: In case of a folder, will proceed the subdirectories files also

        '''
        self.file_type = '.py'
        self.filename_list = []
        self.source = source
        self.output_prefix = output_prefix
        self.doc_type = doc_type
        self.param_type = param_type
        self.recursive = recursive
        self.current_file = None
        self.doc_index = -1
        self.file_index = 0

        self._set_file_list(source)
        self.next_file()

    def _get_files_from_dir(self, folder, recursive, depth=0):
        '''Retrieve the list of files from a folder.

        @param folder: directory where to search files
        @param recursive: if True will search also sub-directories.
        @return: the file list retrieved

        '''
        file_list = []
        if folder[-1] != os.sep:
            folder = folder + os.sep
        for f in glob.glob(folder + "*"):
            if os.path.isdir(f):
                if depth < self.MAX_DEPTH_RECUR: # avoid recursive loop
                    file_list.extend(self._get_files_from_dir(f, recursive, depth+1))
                else:
                    continue
            elif f.endswith(self.file_type):
                file_list.append(f)
        return file_list


    def _set_file_list(self, source):
        '''Build the list of files to be proceeded.

        @param source: path name (file or folder)
    
        '''
        if os.path.isfile(source):
            self.filename_list.append(source)
        elif os.path.isdir(source):
            self.filename_list.extend(self._get_files_from_dir(source, self.recursive))
        else:
            self.filename_list = []

    def get_file_list(self):
        '''Get the list of files to proceed.
        
        @return: the list of files
        
        '''
        return self.filename_list

    def next_file(self):
        '''Set the new current file to proceed.

        @return: the new current file name. None if there is no more file to proceed.

        '''
        if self.current_file is None:
            self.file_index = 0
        else:
            try:
                self.current_file.close()
            except:
                pass
            self.file_index += 1
        try:
            self.current_file = open(self.filename_list[self.file_index])
        except:
            pass
    
    def _get_next(self):
        '''Get the current file's next docstring

        '''
    def _parse_current_file(self):
        '''Parses the current file's content and generates a list of its elements/docstrings.

        '''
        if self.current_file is None:
            raise 'There is no current file opened to explore the elements.'
        #TODO manage decorators
        #TODO manage default params with strings escaping chars as (, ), ', ', #, ...
        #TODO manage multilines
        elem_list = []
        reading_element = False
        reading_docs = False
        raw = ''
        for l in self.current_file.readlines():
            l = l.strip()
            if l.startswith('def ') or 'class ':
                # if currently reading an element content
                if reading_element:
                reading_element = True
                e = DocString(l)
                e.parse_element()
                elem_list.append(e)
            else:
                if '"""' in l or "'''" in l:
                    if reading_docs:
                        raw += l
                        e.parse_docs_raw(raw)
                        reading_docs = False
                        reading_element = False
                        raw = ''

    def diff(self, which=0):
        '''Build the diff between original docstring and proposed docstring.

        @param which: indicates which docstring to proceed. 0 means current docstring,
        -1 means all file dosctrings, >0 means index of the docstring (starting at 1)
        @return: the resulted diff
        @rtype: string

        '''

    def release(self):
        '''Close the current file if any.'''
        try:
            self.current_file.close()
        except:
            pass


if __name__ == "__main__":
    source = sys.argv[0]

    if len(sys.argv) > 1:
        source = sys.argv[1]

    c = PyComment(source)


    print(c.get_file_list())
    c.release()
