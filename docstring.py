#!/usr/bin/python

import re


class DocsTools(object):
    '''This class provides the tools to manage several type of docstring.
    Currently the following are managed:
    - 'javadoc': javadoc style
    - 'params': parameters on beginning of lines
    - 'unknown': try all possibilities

    '''
    def __init__(self, ds_type='javadoc', params=None):
        '''Choose the kind of docstring type.

        @param ds_type: docstring type ('javadoc', 'params', 'unknown')
        @type ds_type: string
        @param params: if known the parameters names that should be found in the docstring.
        @type params: list

        '''
        self.type = ds_type
        self.options_javadoc = ['@param', '@type', '@return', '@rtype']
        if ds_type in ['javadoc', 'unknown']:
            self.options = self.options_javadoc
        else:
            self.options = []
        self.params = params

    def set_known_parameters(self, params):
        '''Set known parameters names.

        @param params: the docstring parameters names
        @type params: list
        '''
        self.params = params

    def get_elem_index(self, data):
        '''Get from a docstring the next option.
        In javadoc style it could be @param, @return, @type,...

        @param data: string to parse
        @return: index of found element else -1
        @rtype: integer

        '''
        idx = len(data)
        for opt in self.options:
            if opt in data:
                i = data.find(opt)
                if i < idx:
                    idx = i
        if idx == len(data):
            idx = -1
        return idx

    def get_param_indexes(self, data):
        '''Get from a docstring the next parameter name indexes.
        In javadoc style it is after @param.

        @param data: string to parse
        @return: start and end indexes of found element else (-1, -1)
        or else (-2, -2) if try to use params style but no parameters were provided.
        Note: the end index is the index after the last name character
        @rtype: tuple

        '''
        start, end = -1, -1
        if self.type in ['javadoc', 'unknown']:
            idx_p = data.find('@param')
            if idx_p >= 0:
                idx_p += len('@param')
                m = re.match(r'^([\w]+)', data[idx_p:].strip())
                if m is not None:
                    param = m.group(1)
                    start = idx_p + data[idx_p:].find(param)
                    end = start + len(param)

        if self.type in ['params', 'unknown'] and (start, end) == (-1, -1):
            if self.params == None:
                return (-2, -2)
            idx = -1
            param = None
            for p in self.params:
                if type(p) is tuple:
                    p = p[0]
                i = data.find('\n' + p)
                if i >= 0:
                    if idx == -1 or i < idx:
                        idx = i
                        param = p
            if idx != -1:
                start, end = idx, idx + len(param)
        return (start, end)

    def get_param_description_indexes(self, data):
        '''Get from a docstring the next parameter's description.
        In javadoc style it is after @param.

        @param data: string to parse
        @return: start and end indexes of found element else (-1, -1)
        @rtype: tuple

        '''
        start, end = -1, -1
        i1, i2 = self.get_param_indexes(data)
        if i1 < 0:
            return (-1, -1)
        m = re.match(r'\W*(\w+)', data[i2:])
        if m is not None:
            first = m.group(1)
            start = data[i2:].find(first)
            if start >= 0:
                start += i2
                if self.type in ['javadoc', 'unknown']:
                    end = self.get_elem_index(data[start:])
                    if end >= 0:
                        end += start
                if self.type in ['params', 'unknown'] and end == -1:
                    p1, _ = self.get_param_indexes(data[start:])
                    if p1 >= 0:
                        end = p1
                    else:
                        end = len(data)

        return (start, end)


class DocString(object):
    '''This class represents the docstring'''

    def __init__(self, elem_raw=None, docs_raw=None):
        '''
        @param elem_raw: raw data of the element (def or class).
        @param docs_raw: the raw data of the docstring part if any.

        '''
        self.dst = DocsTools()
        self.element = {}
        self.element['raw'] = elem_raw
        self.element['name'] = None
        self.element['type'] = None
        self.element['params'] = []
        self.docs = {'in': {}, 'out': {}}
        self.docs['in']['raw'] = docs_raw
        self.docs['in']['desc'] = None
        self.docs['in']['params'] = []
        self.docs['in']['types'] = []
        self.docs['in']['rtype'] = []
        self.docs['out']['raw'] = ''
        self.docs['out']['desc'] = None
        self.docs['out']['params'] = []
        self.docs['out']['types'] = []
        self.docs['out']['rtype'] = []

    def __str__(self):
        txt = "\n\n** " + str(self.element['name']) + ' of type ' + str(self.element['type']) + ':' + str(self.docs['in']['desc']) + '\n'
        txt += '->' + str(self.docs['in']['params']) + '\n\n'
        return txt

    def __repr__(self):
        return self.__str__()

    def parse_element(self, raw=None):
        '''Parses the element's elements (type, name and parameters) :)
        e.g.: def methode(param1, param2='default')
            def                      -> type
            methode                  -> name
            param1, param2='default' -> parameters

        @param raw: raw data of the element (def or class).

        '''
        #TODO manage multilines
        if raw is None:
            l = self.element['raw'].strip()
        else:
            l = raw.strip()
        if l.startswith('def ') or l.startswith('class '):
            # retrieves the type
            if l.startswith('def'):
                self.element['type'] = 'def'
                l = l.replace('def ', '')
            else:
                self.element['type'] = 'class'
                l = l.replace('class ', '')
            # retrieves the name
            self.element['name'] = l[:l.find('(')].strip()
            if l[-1] == ':':
                l = l[:-1].strip()
            # retrieves the parameters
            l = l[l.find('(') + 1:l.find(')')].strip()
            lst = [c.strip() for c in l.split(',')]
            for e in lst:
                if '=' in e:
                    k, v = e.split('=', 1)
                    self.element['params'].append((k.strip(), v.strip()))
                else:
                    self.element['params'].append(e)

    def _extract_docs_description(self):
        '''Extract main description from docstring'''
        data = self.docs['in']['raw'].strip()
        if data.startswith('"""') or data.startswith("'''"):
            data = data[3:]
        if data.endswith('"""') or data.endswith("'''"):
            data = data[:-3]
        idx = self.dst.get_elem_index(data)
        if idx == 0:
            self.docs['in']['desc'] = ''
        elif idx == -1:
            self.docs['in']['desc'] = data
        else:
            self.docs['in']['desc'] = data[:idx]

    def _extract_docs_params(self):
        '''Extract parameters description from docstring'''
        data = '\n'.join([d.strip() for d in self.docs['in']['raw'].split('\n')])
        listed = 0
        loop = True
        maxi = 10000  # avoid infinite loop but should never happen
        i = 0
        while loop:
            i += 1
            if i > maxi:
                loop = False
            start, end = self.dst.get_param_indexes(data)
            if start >= 0:
                param = data[start: end]
                desc = ''
                start, end = self.dst.get_param_description_indexes(data)
                if start > 0:
                    desc = data[start: end].strip()
                self.docs['in']['params'].append((param, desc))
                data = data[end:]
                listed += 1
            else:
                loop = False
        if i > maxi:
            print("WARNING: an infinite loop was reached while extracting docstring parameters (>10000). This should never happen!!!")

    def parse_docs(self, raw=None):
        '''Parses the docstring

        @param raw: the data to parse if not already provided

        '''
        if raw is not None:
            self.docs['in']['raw'] = raw
        if self.docs['in']['raw'] is None:
            return
        self.dst.set_known_parameters(self.element['params'])
        self._extract_docs_params()
        self._extract_docs_description()

    def proceed(self):
        '''Proceed the raw docstring part if any.
        '''


if __name__ == "__main__":
    data1 = '''This is test

    @param par1: the first param1

    '''
    data2 = '''This is test

    @param par1: the first param1
    @param prm2: the second param2

    '''
    data3 = '''This is test

    @param par1: the first param1
    @param prm2: the second param2
    @return: the return value

    '''
    data = data3
    print("data:'''" + data + "'''")
    print("")
    dst = DocsTools('javadoc')
    loop = True
    i, maxi = 0, 10
    while loop:
        i += 1
        if i > maxi:
            loop = False
        start, end = dst.get_param_indexes(data)
        if start >= 0:
            new_start = end
            print("param='" + data[start:end] + "'")
            start, end = dst.get_param_description_indexes(data)
            if start >= 0:
                print("desc='" + data[start:end] + "'")
            else:
                print('NO desc')
            data = data[new_start:]
        else:
            print("NO param")
            loop = False
