#!/usr/bin/python
# -*- coding: utf8 -*-

__author__ = "A. Daouzli"
__copyright__ = "Copyright dec. 2013, A. Daouzli"
__licence__ = "GPL3"
__version__ = "0.0.1"
__maintainer__ = "A. Daouzli"

"""
Formats supported at the time:
 - javadoc:
 managed  -> @param, @type, @return, @rtype
 intended -> @raise

Not yet supported but intended:
 - reST:
 same than javadoc but using ':' instead of '@'
"""

import re


class DocStyle(object):
    '''
    '''
    def __init__(self, name=None):
        '''
        '''
        self.keys = {}
        self.name = name

    def get(self, key):
        '''Gets the key.
        e.g.: the key for 'param' is @param (for instance of DocsJavadoc).

        @param key: the category of the key

        '''
        return self.keys[key]

    def get_keys(self):
        '''Gets the whole set of keys

        @return: the set of keys
        @rtype:  list

        '''
        return self.keys.values()


class DocsJavadoc(DocStyle):
    '''
    '''
    def __init__(self, *arg, **kwarg):
        '''
        '''
        super(DocsJavadoc, self).__init__(*arg, **kwarg)
        self.keys = {'param': '@param',
                     'type': '@type',
                     'return': '@return',
                     'rtype': '@rtype',
                     'raise': '@raise'}


class DocsTools(object):
    '''This class provides the tools to manage several type of docstring.
    Currently the following are managed:
    - 'javadoc': javadoc style
    - 'params': parameters on beginning of lines
    - 'unknown': try all possibilities

    '''
    #TODO: enhance style dependent separation
    #TODO: add set methods to generate style specific outputs
    #TODO: manage reST (:param) style and C style (\param)
    #TODO: add auto recognition of the input style
    def __init__(self, style_in='javadoc', style_out='javadoc', params=None):
        '''Choose the kind of docstring type.

        @param style_in: docstring input style ('javadoc', 'params', 'unknown')
        @type style_in: string
        @param style_out: docstring output style ('javadoc', 'params', 'unknown')
        @type style_out: string
        @param params: if known the parameters names that should be found in the docstring.
        @type params: list

        '''
        cs = DocsJavadoc()
        self.style = {'in': style_in,
                      'out': style_out}
        self.opt = {}
        self.keystyles = []
        self._set_available_options()
        self.params = params

    def _set_available_options(self):
        '''Sets the internal styles list and available options in a structure as following:

            param: javadoc: name = '@param'
                            sep  = ':'
                   reST:    name = ':param'
                            sep  = ':'
                   ...
            type:  javadoc: name = '@type'
                            sep  = ':'
                   ...
            ...

        '''
        options_keystyle = {'keys': ['param', 'type', 'return', 'rtype', 'raise'],
                            'styles': {'javadoc': ('@', ':'),  # tuple:  key prefix, separator
                                       'reST':    (':', ':'),
                                       'cstyle':  ('\\', ' ')}
                           }
        self.keystyles = options_keystyle['styles'].keys()
        for op in options_keystyle['keys']:
            self.opt[op] = {}
            for style in options_keystyle['styles']:
                self.opt[op][style] = {'name': options_keystyle['styles'][style][0] + op,
                                       'sep': options_keystyle['styles'][style][1]
                                      }

    def _get_options(self, style):
        '''Gets the list of keywords for a particular style

        @para: the style that the keywords are wanted

        '''
        return [self.opt[o][style]['name'] for o in self.opt]

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
        for opt in self._get_options(self.style['in']):
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
        #TODO: new method to extract an element's name so will be available for @param and @types and other styles (:param, \param)
        start, end = -1, -1
        stl_param = self.opt['param'][self.style['in']]['name']
        if self.style['in'] in self.keystyles + ['unknown']:
            idx_p = data.find(stl_param)
            if idx_p >= 0:
                idx_p += len(stl_param)
                m = re.match(r'^([\w]+)', data[idx_p:].strip())
                if m is not None:
                    param = m.group(1)
                    start = idx_p + data[idx_p:].find(param)
                    end = start + len(param)

        if self.style['in'] in ['params', 'unknown'] and (start, end) == (-1, -1):
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

    def get_param_description_indexes(self, data, prev=None):
        '''Get from a docstring the next parameter's description.
        In javadoc style it is after @param.

        @param data: string to parse
        @param prev: index after the param element name
        @return: start and end indexes of found element else (-1, -1)
        @rtype: tuple

        '''
        start, end = -1, -1
        if not prev:
            _, prev = self.get_param_indexes(data)
        if prev < 0:
            return (-1, -1)
        m = re.match(r'\W*(\w+)', data[prev:])
        if m is not None:
            first = m.group(1)
            start = data[prev:].find(first)
            if start >= 0:
                start += prev
                if self.style['in'] in self.keystyles + ['unknown']:
                    end = self.get_elem_index(data[start:])
                    if end >= 0:
                        end += start
                if self.style['in'] in ['params', 'unknown'] and end == -1:
                    p1, _ = self.get_param_indexes(data[start:])
                    if p1 >= 0:
                        end = p1
                    else:
                        end = len(data)

        return (start, end)

    def get_param_type_indexes(self, data, name=None, prev=None):
        '''Get from a docstring a parameter type indexes.
        In javadoc style it is after @type.

        @param data: string to parse
        @param name: the name of the parameter
        @param prev: index after the previous element (param or param's description)
        @return: start and end indexes of found element else (-1, -1)
        Note: the end index is the index after the last included character or -1 if
        reached the end
        @rtype: tuple

        '''
        start, end = -1, -1
        stl_type = self.opt['type'][self.style['in']]['name']
        if not prev:
            _, prev = self.get_param_description_indexes(data)
        if prev >= 0:
            if self.style['in'] in self.keystyles + ['unknown']:
                idx = self.get_elem_index(data[prev:])
                if idx >= 0 and data[prev + idx:].startswith('@type'):
                    idx = prev + idx + len(stl_type)
                    m = re.match(r'\W*(\w+)', data[idx:])
                    if m is not None:
                        first = m.group(1)
                        start = data[idx:].find(first) + idx

            if self.style['in'] in ['params', 'unknown'] and (start, end) == (-1, -1):
                #TODO: manage this
                pass

        return (start, end)

    def get_return_description_indexes(self, data):
        '''Get from a docstring the return parameter description indexes.
        In javadoc style it is after @return.

        @param data: string to parse
        @return: start and end indexes of found element else (-1, -1)
        Note: the end index is the index after the last included character or -1 if
        reached the end
        @rtype: tuple

        '''
        start, end = -1, -1
        stl_return= self.opt['return'][self.style['in']]['name']
        if self.style['in'] in self.keystyles + ['unknown']:
            idx = self.get_elem_index(data)
            idx_abs = idx
            # search @return
            while idx >= 0 and not data[idx_abs:].startswith(stl_return):
                idx = self.get_elem_index(data[idx_abs + 1:])
                if idx >= 0:
                    idx_abs += idx + 1
            # search starting description
            if idx >= 0:
                #FIXME: take care if a return description starts with <, >, =,...
                m = re.match(r'\W*(\w+)', data[idx_abs + len(stl_return):])
                if m is not None:
                    first = m.group(1)
                    idx = data[idx_abs:].find(first)
                    idx_abs += idx
                    start = idx_abs
                else:
                    idx = -1
            # search the end
            idx = self.get_elem_index(data[idx_abs:])
            if idx > 0:
                idx_abs += idx
                end = idx_abs

        if self.style['in'] in ['params', 'unknown'] and (start, end) == (-1, -1):
            #TODO: manage this
            pass

        return (start, end)

    def get_return_type_indexes(self, data):
        '''Get from a docstring the return parameter type indexes.
        In javadoc style it is after @rtype.

        @param data: string to parse
        @return: start and end indexes of found element else (-1, -1)
        Note: the end index is the index after the last included character or -1 if
        reached the end
        @rtype: tuple

        '''
        start, end = -1, -1
        stl_rtype = self.opt['rtype'][self.style['in']]['name']
        if self.style['in'] in self.keystyles + ['unknown']:
            dstart, dend = self.get_return_description_indexes(data)
            if dstart >= 0 and dend > 0:
                idx = self.get_elem_index(data[dend:])
                if idx >= 0 and data[dend + idx:].startswith(stl_rtype):
                    idx = dend + idx + len(stl_rtype)
                    m = re.match(r'\W*(\w+)', data[idx:])
                    if m is not None:
                        first = m.group(1)
                        start = data[idx:].find(first) + idx

        if self.style['in'] in ['params', 'unknown'] and (start, end) == (-1, -1):
            #TODO: manage this
            pass

        return (start, end)


class DocString(object):
    '''This class represents the docstring'''

    def __init__(self, elem_raw, spaces='', docs_raw=None):
        '''
        @param elem_raw: raw data of the element (def or class).
        @param spaces: the leading whitespaces before the element
        @param docs_raw: the raw data of the docstring part if any.

        '''
        self.dst = DocsTools()
        self.element = {}
        self.element['raw'] = elem_raw
        self.element['name'] = None
        self.element['type'] = None
        self.element['params'] = []
        self.element['spaces'] = spaces
        self.docs = {'in': {}, 'out': {}}
        self.docs['in']['raw'] = docs_raw
        self.docs['in']['desc'] = None
        self.docs['in']['params'] = []
        self.docs['in']['types'] = []
        self.docs['in']['return'] = None
        self.docs['in']['rtype'] = None
        self.docs['out']['raw'] = ''
        self.docs['out']['desc'] = None
        self.docs['out']['params'] = []
        self.docs['out']['types'] = []
        self.docs['out']['return'] = None
        self.docs['out']['rtype'] = None
        if '\t' in spaces:
            self.docs['out']['spaces'] = spaces + '\t'
        elif (len(spaces) % 4) == 0 or spaces == '':
            #FIXME: should bug if tabs for class or function (as spaces=='')
            self.docs['out']['spaces'] = spaces + ' ' * 4
        else:
            self.docs['out']['spaces'] = spaces + ' ' * 2
        self.parsed_elem = False
        self.parsed_docs = False
        self.generated_docs = False

        self.parse_element()

    def __str__(self):
        txt = "\n\n** " + str(self.element['name'])
        txt += ' of type ' + str(self.element['type']) + ':'
        txt += str(self.docs['in']['desc']) + '\n'
        txt += '->' + str(self.docs['in']['params']) + '\n'
        txt += '***>>' + str(self.docs['out']['raw']) + '\n\n'
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
        #TODO: retrieve return from element external code (in parameter)
        #TODO: manage multilines
        if raw is None:
            l = self.element['raw'].strip()
        else:
            l = raw.strip()
        is_class = False
        if l.startswith('def ') or l.startswith('class '):
            # retrieves the type
            if l.startswith('def'):
                self.element['type'] = 'def'
                l = l.replace('def ', '')
            else:
                self.element['type'] = 'class'
                l = l.replace('class ', '')
                is_class = True
            # retrieves the name
            self.element['name'] = l[:l.find('(')].strip()
            if not is_class:
                if l[-1] == ':':
                    l = l[:-1].strip()
                # retrieves the parameters
                l = l[l.find('(') + 1:l.find(')')].strip()
                lst = [c.strip() for c in l.split(',')]
                for e in lst:
                    if '=' in e:
                        k, v = e.split('=', 1)
                        self.element['params'].append((k.strip(), v.strip()))
                    elif e != 'self' and e != 'cls':
                        self.element['params'].append(e)
        self.parsed_elem = True

    def _extract_docs_description(self):
        '''Extract main description from docstring'''
        #FIXME: the indentation of descriptions is lost
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
        '''Extract parameters description and type from docstring. The internal computed parameters list is
        composed by tuples (parameter, description).

        '''
        #FIXME: the indentation of descriptions is lost
        #TODO: extract type desc using dst.get_param_type_indexes()
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
                start, end = self.dst.get_param_description_indexes(data, prev=end)
                if start > 0:
                    desc = data[start: end].strip()
                self.docs['in']['params'].append((param, desc))
                data = data[end:]
                listed += 1
            else:
                loop = False
        if i > maxi:
            print("WARNING: an infinite loop was reached while extracting docstring parameters (>10000). This should never happen!!!")

    def _extract_docs_param_types(self):
        '''
        '''
        #TODO: remove when done in _extract_docs_params()
        data = '\n'.join([d.strip() for d in self.docs['in']['raw'].split('\n')])
        params = [p[0] for p in self.docs['in']['params']]
        self.docs['in']['types'] = [''] * len(params)
        loop = True
        maxi = 10000  # avoid infinite loop but should never happen
        i = 0
        while loop:
            i += 1
            if i > maxi:
                loop = False
            idx = self.dst.get_elem_index(data)
            if idx == -1:
                loop = False
            elif data[idx:].startswith('@type '):
                d = data[idx + len('@type '):].strip()
                m = re.match(r'^([\w]+)', d)
                if m is not None:
                    param = m.group(1)
                    try:
                        idx_p = params.index(param)
                    except (ValueError):
                        idx_p = -1
                    self.docs['in']['types'][idx_p] = 'FOUND TYPE'
                    #TODO retrieve the content
                    #start = idx_p + data[idx_p:].find(param)
                    #end = start + len(param)
                else:
                    data = data[idx + len('@type'):]
            else:
                data = data[idx + 2:]
        if i > maxi:
            print("WARNING: an infinite loop was reached while extracting docstring parameters (>10000). This should never happen!!!")

    def _extract_docs_return(self):
        '''Extract return description and type
        '''
        data = '\n'.join([d.strip() for d in self.docs['in']['raw'].split('\n')])
        start, end = self.dst.get_return_description_indexes(data)
        if start >= 0:
            if end >= 0:
                self.docs['in']['return'] = data[start:end].rstrip().replace("'''", "")
            else:
                self.docs['in']['return'] = data[start:].rstrip().replace("'''", "")
        start, end = self.dst.get_return_type_indexes(data)
        if start >= 0:
            if end >= 0:
                self.docs['in']['rtype'] = data[start:end].rstrip().replace("'''", "")
            else:
                self.docs['in']['rtype'] = data[start:].rstrip().replace("'''", "")

    def parse_docs(self, raw=None):
        '''Parses the docstring

        @param raw: the data to parse if not internally provided

        '''
        if raw is not None:
            self.docs['in']['raw'] = raw
        if self.docs['in']['raw'] is None:
            return
        self.dst.set_known_parameters(self.element['params'])
        self._extract_docs_params()
        self._extract_docs_param_types()
        self._extract_docs_return()
        self._extract_docs_description()
        self.parsed_docs = True

    def _set_desc(self):
        '''Sets the global description if any
        '''
        if self.docs['in']['desc']:
            self.docs['out']['desc'] = self.docs['in']['desc']
        else:
            self.docs['out']['desc'] = ''

    def _set_params(self):
        '''Sets the parameters with return types, descriptions and default value if any
        '''
        #TODO add types
        if len(self.docs['in']['params']) > 0:
            self.docs['out']['params'] = list(self.docs['in']['params'])
        for e in self.element['params']:
            param = e
            if type(e) is tuple:
                param = e[0]
            found = False
            for i, p in enumerate(self.docs['out']['params']):
                if param == p[0]:
                    found = True
                    # add default value if any
                    if type(e) is tuple:
                        self.docs['out']['params'][i] = (p[0], p[1], e[1])
            if not found:
                if type(e) is tuple:
                    p = (param, '', e[1])
                else:
                    p = (param, '')
                self.docs['out']['params'].append(p)

    def _set_return(self):
        '''Sets the return parameter with description and rtype if any
        '''
        #TODO: manage return retrieved from element code (external)
        self.docs['out']['return'] = self.docs['in']['return']
        self.docs['out']['rtype'] = self.docs['in']['rtype']

    def _set_raw(self):
        '''Sets the raw docstring
        '''
        #TODO: make it no style dependent
        with_space = lambda s: '\n'.join([self.docs['out']['spaces'] + l for l in s.split('\n')])
        raw = self.docs['out']['spaces'] + "'''"
        raw += with_space(self.docs['out']['desc']).strip() + '\n'
        if len(self.docs['out']['params']):
            raw += '\n'
            for p in self.docs['out']['params']:
                raw += self.docs['out']['spaces'] + '@param ' + p[0] + ': ' + with_space(p[1])
                if len(p) > 2 and 'default' not in p[1].lower():
                    raw += ' (Default value = ' + str(p[2]) + ')'
                raw += '\n'
        if self.docs['out']['return']:
            if len(self.docs['out']['params']) == 0:
                raw += '\n'
            raw += self.docs['out']['spaces'] + '@return: ' + self.docs['out']['return'].rstrip() + '\n'
        if self.docs['out']['rtype']:
            if len(self.docs['out']['params']) == 0:
                raw += '\n'
            raw += self.docs['out']['spaces'] + '@rtype: ' + self.docs['out']['rtype'].rstrip() + '\n'
        raw += "\n"
        if raw.count("'''") == 1:
            raw += self.docs['out']['spaces'] + "'''"
        self.docs['out']['raw'] = raw.rstrip()

    def generate_docs(self):
        '''
        '''
        self._set_desc()
        self._set_params()
        self._set_return()
        self._set_raw()
        self.generated_docs = True

    def get_raw_docs(self):
        '''Generates raw docstring
        '''
        if not self.generated_docs:
            self.generate_docs()
        return self.docs['out']['raw']


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
