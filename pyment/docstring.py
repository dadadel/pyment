# -*- coding: utf-8 -*-

import re
from collections import defaultdict

__author__ = "A. Daouzli"
__copyright__ = "Copyright 2012-2018, A. Daouzli"
__licence__ = "GPL3"
__version__ = "0.3.3"
__maintainer__ = "A. Daouzli"

"""
Formats supported at the time:
 - javadoc, reST (restructured text, Sphinx):
 managed  -> description, param, type, return, rtype, raise
 - google:
 managed  -> description, parameters, return, raises
 - numpydoc:
 managed  -> description, parameters, return (first of list only), raises

"""

RAISES_NAME_REGEX = r'^([\w.]+)'


def isin_alone(elems, line):
    """Check if an element from a list is the only element of a string.

    :type elems: list
    :type line: str

    """
    found = False
    for e in elems:
        if line.strip().lower() == e.lower():
            found = True
            break
    return found


def isin_start(elems, line):
    """Check if an element from a list starts a string.

    :type elems: list
    :type line: str

    """
    found = False
    elems = [elems] if type(elems) is not list else elems
    for e in elems:
        if line.lstrip().lower().startswith(e):
            found = True
            break
    return found


def isin(elems, line):
    """Check if an element from a list is in a string.

    :type elems: list
    :type line: str

    """
    found = False
    for e in elems:
        if e in line.lower():
            found = True
            break
    return found


def get_leading_spaces(data):
    """Get the leading space of a string if it is not empty

    :type data: str

    """
    spaces = ''
    m = re.match(r'^(\s*)', data)
    if m:
        spaces = m.group(1)
    return spaces


class DocToolsBase(object):
    """

    """

    def __init__(self,
                 first_line=None,
                 optional_sections=None,
                 excluded_sections=None,
                 opt=None,
                 section_headers=None,
                 ):
        """

        :param first_line: indicate if description should start
          on first or second line. By default it will follow global config.
        :type first_line: boolean
        :param optional_sections: list of sections that are not mandatory
          if empty. See subclasses for further description.
        :type optional_sections: list
        :param excluded_sections: list of sections that are excluded,
          even if mandatory. The list is the same as for optional sections.
        :type excluded_sections: list
        :param opt:
        :type opt:
        :param section_headers:
        :type section_headers:
        """
        self.first_line = first_line
        self.optional_sections = list(optional_sections)
        self.excluded_sections = list(excluded_sections)
        self.opt = opt
        self.section_headers = section_headers

    def __iter__(self):
        return self.opt.__iter__()

    def __getitem__(self, key):
        return self.opt[key]

    def get_optional_sections(self):
        """Get optional sections"""
        return self.optional_sections

    def get_excluded_sections(self):
        """Get excluded sections"""
        return self.excluded_sections

    def get_mandatory_sections(self):
        """Get mandatory sections"""
        return [s for s in self.opt
                if s not in self.optional_sections and
                   s not in self.excluded_sections]

    def _get_list_key(self, spaces, lines):
        """ Parse lines and extract the list of key elements.

        :param spaces: leading spaces of starting line
        :type spaces: str
        :param lines: list of strings
        :type lines: list(str)
        :return: list of key elements
        """
        raise NotImplementedError

    def get_list_key(self, data, key, header_lines=1):
        """Get the list of a key elements.
        Each element is a tuple (key=None, description, type=None).
        Note that the tuple's element can differ depending on the key.

        :param data: the data to proceed
        :param key: the key

        """
        data = data.splitlines()
        init = self.get_section_key_line(data, key)
        if init == -1:
            return []
        start, end = self.get_next_section_lines(data[init:])
        # get the spacing of line with key
        spaces = get_leading_spaces(data[init + start])
        start += init + header_lines
        if end != -1:
            end += init
        else:
            end = len(data)

        return self._get_list_key(spaces, data[start:end])

    def get_raise_list(self, data):
        """Get the list of exceptions.
        The list contains tuples (name, desc)

        :param data: the data to proceed

        """
        return_list = []
        lst = self.get_list_key(data, 'raise')
        for l in lst:
            # assume raises are only a name and a description
            name, desc, _ = l
            return_list.append((name, desc))

        return return_list

    def get_return_list(self, data):
        """Get the list of returned values.
        The list contains tuples (name=None, desc, type=None)

        :param data: the data to proceed

        """
        return_list = []
        lst = self.get_list_key(data, 'return')
        for l in lst:
            name, desc, rtype = l
            if l[2] is None:
                rtype = l[0]
                name = None
                desc = desc.strip()
            return_list.append((name, desc, rtype))

        return return_list

    def get_param_list(self, data):
        """Get the list of parameters.
        The list contains tuples (name, desc, type=None)

        :param data: the data to proceed

        """
        return self.get_list_key(data, 'param')

    def get_next_section_start_line(self, data):
        """Get the starting line number of next section.
        It will return -1 if no section was found.
        The section is a section key (e.g. 'Parameters:')
        then the content

        :param data: a list of strings containing the docstring's lines
        :returns: the index of next section else -1
        """
        raise NotImplementedError

    def get_next_section_lines(self, data):
        """Get the starting line number and the ending line number of next section.
        It will return (-1, -1) if no section was found.
        The section is a section key (e.g. 'Parameters') then the content
        The ending line number is the line after the end of the section or -1 if
        the section is at the end.

        :param data: the data to proceed

        """
        end = -1
        start = self.get_next_section_start_line(data)
        if start != -1:
            end = self.get_next_section_start_line(data[start + 1:])
        return start, end

    def get_key_section_header(self, key, spaces):
        """Get the key of the section header

        :param key: the key name
        :param spaces: spaces to set at the beginning of the header

        """
        if key in self.section_headers:
            header = self.section_headers[key]
        else:
            return ''

        return header

    def get_section_key_line(self, data, key, opt_extension=''):
        """Get the next section line for a given key.

        :param data: the data to proceed
        :param key: the key
        :param opt_extension: an optional extension to delimit the opt value

        """
        start = 0
        init = 0
        while start != -1:
            start = self.get_next_section_start_line(data[init:])
            init += start
            if start != -1:
                if data[init].strip().lower() == self.opt[key] + opt_extension:
                    break
                init += 1
        if start != -1:
            start = init
        return start


class NumpydocTools(DocToolsBase):
    """ """

    def __init__(self,
                 first_line=None,
                 optional_sections=('raise', 'also', 'ref', 'note', 'other', 'example', 'method', 'attr'),
                 excluded_sections=()):
        '''
        :param first_line: indicate if description should start
          on first or second line. By default it will follow global config.
        :type first_line: boolean
        :param optional_sections: list of sections that are not mandatory
          if empty. The accepted sections are:
          -param
          -return
          -raise
          -also
          -ref
          -note
          -other
          -example
          -method
          -attr
        :type optional_sections: list
        :param excluded_sections: list of sections that are excluded,
          even if mandatory. The list is the same than for optional sections.
        :type excluded_sections: list

        '''
        super(NumpydocTools, self).__init__(first_line=first_line,
                                            optional_sections=optional_sections,
                                            excluded_sections=excluded_sections,
                                            opt={
                                                'also': 'see also',
                                                'attr': 'attributes',
                                                'example': 'examples',
                                                'method': 'methods',
                                                'note': 'notes',
                                                'other': 'other parameters',
                                                'param': 'parameters',
                                                'raise': 'raises',
                                                'ref': 'references',
                                                'return': 'returns',
                                            },
                                            section_headers={
                                                'param': 'Parameters',
                                                'return': 'Returns',
                                                'raise': 'Raises',
                                            },
                                            )

        self.keywords = [
            ':math:',
            '.. math::',
            'see also',
            '.. image::',
        ]

    def get_next_section_start_line(self, data):
        """Get the starting line number of next section.
        It will return -1 if no section was found.
        The section is a section key (e.g. 'Parameters') followed by underline
        (made by -), then the content

        :param data: a list of strings containing the docstring's lines
        :type data: list(str)
        :returns: the index of next section else -1

        """
        start = -1
        for i, line in enumerate(data):
            if start != -1:
                # we found the key so check if this is the underline
                if line.strip() and isin_alone(['-' * len(line.strip())], line):
                    break
                else:
                    start = -1
            if isin_alone(self.opt.values(), line):
                start = i
        return start

    def get_list_key(self, data, key, header_lines=2):
        """Get the list of a key elements.
        Each element is a tuple (key=None, description, type=None).
        Note that the tuple's element can differ depending on the key.

        :param data: the data to proceed
        :param key: the key

        """
        return super(NumpydocTools, self).get_list_key(data, key, header_lines=header_lines)

    def _get_list_key(self, spaces, lines):
        key_list = []
        parse_key = False
        key, desc, ptype = None, '', None

        for line in lines:
            if len(line.strip()) == 0:
                continue
            # on the same column of the key is the key
            curr_spaces = get_leading_spaces(line)
            if len(curr_spaces) == len(spaces):
                if parse_key:
                    key_list.append((key, desc, ptype))
                elems = line.split(':', 1)
                key = elems[0].strip()
                ptype = elems[1].strip() if len(elems) > 1 else None
                desc = ''
                parse_key = True
            else:
                if len(curr_spaces) > len(spaces):
                    line = line.replace(spaces, '', 1)
                if desc:
                    desc += '\n'
                desc += line
        if parse_key:
            key_list.append((key, desc, ptype))

        return key_list

    def get_attr_list(self, data):
        """Get the list of attributes.
        The list contains tuples (name, desc, type=None)

        :param data: the data to proceed

        """
        return self.get_list_key(data, 'attr')

    def get_raw_not_managed(self, data):
        """Get elements not managed. They can be used as is.

        :param data: the data to proceed

        """
        keys = ['also', 'ref', 'note', 'other', 'example', 'method', 'attr']
        elems = [self.opt[k] for k in self.opt if k in keys]
        data = data.splitlines()
        start = 0
        init = 0
        raw = ''
        spaces = None
        while start != -1:
            start, end = self.get_next_section_lines(data[init:])
            if start != -1:
                init += start
                if isin_alone(elems, data[init]) and \
                        not isin_alone([self.opt[e] for e in self.excluded_sections], data[init]):
                    spaces = get_leading_spaces(data[init])
                    if end != -1:
                        section = [d.replace(spaces, '', 1).rstrip() for d in data[init:init + end]]
                    else:
                        section = [d.replace(spaces, '', 1).rstrip() for d in data[init:]]
                    raw += '\n'.join(section) + '\n'
                init += 2
        return raw

    def get_key_section_header(self, key, spaces):
        """Get the key of the header section

        :param key: the key name
        :param spaces: spaces to set at the beginning of the header

        """
        header = super(NumpydocTools, self).get_key_section_header(key, spaces)
        header = spaces + header + '\n' + spaces + '-' * len(header) + '\n'
        return header


class GoogledocTools(DocToolsBase):
    """ """
    def __init__(self,
                 first_line=None,
                 optional_sections=('raise'),
                 excluded_sections=()):
        """
        :param first_line: indicate if description should start
          on first or second line. By default it will follow global config.
        :type first_line: boolean
        :param optional_sections: list of sections that are not mandatory
          if empty. The accepted sections are:
          -param
          -return
          -raise
        :type optional_sections: list
        :param excluded_sections: list of sections that are excluded,
          even if mandatory. The list is the same than for optional sections.
        :type excluded_sections: list

        """
        super(GoogledocTools, self).__init__(first_line=first_line,
                                             optional_sections=optional_sections,
                                             excluded_sections=excluded_sections,
                                             opt={
                                                 'attr': 'attributes',
                                                 'param': 'args',
                                                 'raise': 'raises',
                                                 'return': 'returns',
                                                 'yield': 'yields',
                                             },
                                             section_headers={
                                                 'param': 'Args',
                                                 'return': 'Returns',
                                                 'raise': 'Raises',
                                             },
                                             )

    def get_section_key_line(self, data, key, opt_extension=':'):
        """Get the next section line for a given key.

        :param data: the data to proceed
        :param key: the key
        :param opt_extension: an optional extension to delimit the opt value

        """
        return super(GoogledocTools, self).get_section_key_line(data, key, opt_extension)

    def _get_list_key(self, spaces, lines):
        key_list = []
        parse_key = False
        key, desc, ptype = None, '', None
        param_spaces = 0

        for line in lines:
            if len(line.strip()) == 0:
                continue
            curr_spaces = get_leading_spaces(line)
            if not param_spaces:
                param_spaces = len(curr_spaces)
            if len(curr_spaces) == param_spaces:
                if parse_key:
                    key_list.append((key, desc, ptype))
                if ':' in line:
                    elems = line.split(':', 1)
                    ptype = None
                    key = elems[0].strip()
                    # the param's type is near the key in parenthesis
                    if '(' in key and ')' in key:
                        tstart = key.index('(') + 1
                        tend = key.index(')')
                        # the 'optional' keyword can follow the style after a comma
                        if ',' in key:
                            tend = key.index(',')
                        ptype = key[tstart:tend].strip()
                        key = key[:tstart - 1].strip()
                    desc = elems[1].strip()
                    parse_key = True
                else:
                    if len(curr_spaces) > len(spaces):
                        line = line.replace(spaces, '', 1)
                    if desc:
                        desc += '\n'
                    desc += line
            else:
                if len(curr_spaces) > len(spaces):
                    line = line.replace(spaces, '', 1)
                if desc:
                    desc += '\n'
                desc += line
        if parse_key or desc:
            key_list.append((key, desc, ptype))

        return key_list

    def get_next_section_start_line(self, data):
        """Get the starting line number of next section.
        It will return -1 if no section was found.
        The section is a section key (e.g. 'Parameters:')
        then the content

        :param data: a list of strings containing the docstring's lines
        :returns: the index of next section else -1

        """
        start = -1
        for i, line in enumerate(data):
            if isin_alone([k + ":" for k in self.opt.values()], line):
                start = i
                break
        return start

    def get_key_section_header(self, key, spaces):
        """Get the key of the section header

        :param key: the key name
        :param spaces: spaces to set at the beginning of the header

        """
        header = super(GoogledocTools, self).get_key_section_header(key, spaces)
        header = spaces + header + ':' + '\n'
        return header


class DocsTools(object):
    """This class provides the tools to manage several types of docstring.
    Currently the following are managed:
    - 'javadoc': javadoc style
    - 'reST': restructured text style compatible with Sphinx
    - 'groups': parameters on beginning of lines (like Google Docs)
    - 'google': the numpy format for docstrings (using an external module)
    - 'numpydoc': the numpy format for docstrings (using an external module)

    """
    # TODO: enhance style dependent separation
    # TODO: add set methods to generate style specific outputs
    # TODO: manage C style (\param)
    def __init__(self, style_in='javadoc', style_out='reST', params=None):
        """Choose the kind of docstring type.

        :param style_in: docstring input style ('javadoc', 'reST', 'groups', 'numpydoc', 'google')
        :type style_in: string
        :param style_out: docstring output style ('javadoc', 'reST', 'groups', 'numpydoc', 'google')
        :type style_out: string
        :param params: if known the parameters names that should be found in the docstring.
        :type params: list

        """
        self.style = {'in': style_in,
                      'out': style_out}
        self.opt = {}
        self.tagstyles = []
        self._set_available_styles()
        self.params = params
        self.numpydoc = NumpydocTools()
        self.googledoc = GoogledocTools()

    def _set_available_styles(self):
        """Set the internal styles list and available options in a structure as following:

            param: javadoc: name = '@param'
                            sep  = ':'
                   reST:    name = ':param'
                            sep  = ':'
                   ...
            type:  javadoc: name = '@type'
                            sep  = ':'
                   ...
            ...

        And sets the internal groups style:
            param:  'params', 'args', 'parameters', 'arguments'
            return: 'returns', 'return'
            raise:  'raises', 'raise', 'exceptions', 'exception'

        """
        options_tagstyle = {'keys': ['param', 'type', 'returns', 'return', 'rtype', 'raise'],
                            'styles': {'javadoc': ('@', ':'),  # tuple:  key prefix, separator
                                       'reST': (':', ':'),
                                       'cstyle': ('\\', ' ')}
                           }
        self.tagstyles = list(options_tagstyle['styles'].keys())
        for op in options_tagstyle['keys']:
            self.opt[op] = {}
            for style in options_tagstyle['styles']:
                self.opt[op][style] = {'name': options_tagstyle['styles'][style][0] + op,
                                       'sep': options_tagstyle['styles'][style][1]
                                      }
        self.opt['return']['reST']['name'] = ':returns'
        self.opt['raise']['reST']['name'] = ':raises'
        self.groups = {
                    'param': ['params', 'args', 'parameters', 'arguments'],
                    'return': ['returns', 'return'],
                    'raise': ['raises', 'exceptions', 'raise', 'exception']
                    }

    def autodetect_style(self, data):
        """Determine the style of a docstring,
        and sets it as the default input one for the instance.

        :param data: the docstring's data to recognize.
        :type data: str
        :returns: the style detected else 'unknown'
        :rtype: str

        """
        # evaluate styles with keys

        found_keys = defaultdict(int)
        for style in self.tagstyles:
            for key in self.opt:
                found_keys[style] += data.count(self.opt[key][style]['name'])
        fkey = max(found_keys, key=found_keys.get)
        detected_style = fkey if found_keys[fkey] else 'unknown'

        # evaluate styles with groups

        if detected_style == 'unknown':
            found_groups = 0
            found_googledoc = 0
            found_numpydoc = 0
            found_numpydocsep = 0
            for line in data.strip().splitlines():
                for key in self.groups:
                    found_groups += 1 if isin_start(self.groups[key], line) else 0
                for key in self.googledoc:
                    found_googledoc += 1 if isin_start(self.googledoc[key], line) else 0
                for key in self.numpydoc:
                    found_numpydoc += 1 if isin_start(self.numpydoc[key], line) else 0
                if line.strip() and isin_alone(['-' * len(line.strip())], line):
                    found_numpydocsep += 1
                elif isin(self.numpydoc.keywords, line):
                    found_numpydoc += 1
            # TODO: check if not necessary to have > 1??
            if found_numpydoc and found_numpydocsep:
                detected_style = 'numpydoc'
            elif found_googledoc >= found_groups:
                detected_style = 'google'
            elif found_groups:
                detected_style = 'groups'
        self.style['in'] = detected_style

        return detected_style

    def set_input_style(self, style):
        """Set the input docstring style

        :param style: style to set for input docstring
        :type style: str

        """
        self.style['in'] = style

    def set_output_style(self, style):
        """Set the output docstring style

        :param style: style to set for output docstring
        :type style: str

        """
        self.style['out'] = style

    def _get_options(self, style):
        """Get the list of keywords for a particular style

        :param style: the style that the keywords are wanted

        """
        return [self.opt[o][style]['name'] for o in self.opt]

    def get_key(self, key, target='in'):
        """Get the name of a key in current style.
        e.g.: in javadoc style, the returned key for 'param' is '@param'

        :param key: the key wanted (param, type, return, rtype,..)
        :param target: the target docstring is 'in' for the input or
          'out' for the output to generate. (Default value = 'in')

        """
        target = 'out' if target == 'out' else 'in'
        return self.opt[key][self.style[target]]['name']

    def get_sep(self, key='param', target='in'):
        """Get the separator of current style.
        e.g.: in reST and javadoc style, it is ":"

        :param key: the key which separator is wanted (param, type, return, rtype,..) (Default value = 'param')
        :param target: the target docstring is 'in' for the input or
          'out' for the output to generate. (Default value = 'in')

        """
        target = 'out' if target == 'out' else 'in'
        if self.style[target] in ['numpydoc', 'google']:
            return ''
        return self.opt[key][self.style[target]]['sep']

    def set_known_parameters(self, params):
        """Set known parameters names.

        :param params: the docstring parameters names
        :type params: list

        """
        self.params = params

    def get_doctests_indexes(self, data):
        """Extract Doctests if found and return it

        :param data: string to parse
        :return: index of start and index of end of the doctest, else (-1, -1)
        :rtype: tuple

        """
        start, end = -1, -1
        datalst = data.splitlines()
        for i, line in enumerate(datalst):
            if start > -1:
                if line.strip() == "":
                    break
                end = i
            elif line.strip().startswith(">>>"):
                start = i
                end = i
        return start, end

    def get_group_key_line(self, data, key):
        """Get the next group-style key's line number.

        :param data: string to parse
        :param key: the key category
        :returns: the found line number else -1

        """
        idx = -1
        for i, line in enumerate(data.splitlines()):
            if isin_start(self.groups[key], line):
                idx = i
        return idx
#        search = '\s*(%s)' % '|'.join(self.groups[key])
#        m = re.match(search, data.lower())
#        if m:
#            key_param = m.group(1)

    def get_group_key_index(self, data, key):
        """Get the next groups style's starting line index for a key

        :param data: string to parse
        :param key: the key category
        :returns: the index if found else -1

        """
        idx = -1
        li = self.get_group_key_line(data, key)
        if li != -1:
            idx = 0
            for line in data.splitlines()[:li]:
                idx += len(line) + len('\n')
        return idx

    def get_group_line(self, data):
        """Get the next group-style key's line.

        :param data: the data to proceed
        :returns: the line number

        """
        idx = -1
        for key in self.groups:
            i = self.get_group_key_line(data, key)
            if (i < idx and i != -1) or idx == -1:
                idx = i
        return idx

    def get_group_index(self, data):
        """Get the next groups style's starting line index

        :param data: string to parse
        :returns: the index if found else -1

        """
        idx = -1
        li = self.get_group_line(data)
        if li != -1:
            idx = 0
            for line in data.splitlines()[:li]:
                idx += len(line) + len('\n')
        return idx

    def get_key_index(self, data, key, starting=True):
        """Get from a docstring the next option with a given key.

        :param data: string to parse
        :param starting: does the key element must start the line (Default value = True)
        :type starting: boolean
        :param key: the key category. Can be 'param', 'type', 'return', ...
        :returns: index of found element else -1
        :rtype: integer

        """
        key = self.opt[key][self.style['in']]['name']
        if key.startswith(':returns'):
            data = data.replace(':return:', ':returns:')  # see issue 9
        idx = len(data)
        ini = 0
        loop = True
        if key in data:
            while loop:
                i = data.find(key)
                if i != -1:
                    if starting:
                        if not data[:i].rstrip(' \t').endswith('\n') and len(data[:i].strip()) > 0:
                            ini = i + 1
                            data = data[ini:]
                        else:
                            idx = ini + i
                            loop = False
                    else:
                        idx = ini + i
                        loop = False
                else:
                    loop = False
        if idx == len(data):
            idx = -1
        return idx

    def get_elem_index(self, data, starting=True):
        """Get from a docstring the next option.
        In javadoc style it could be @param, @return, @type,...

        :param data: string to parse
        :param starting: does the key element must start the line (Default value = True)
        :type starting: boolean
        :returns: index of found element else -1
        :rtype: integer

        """
        idx = len(data)
        for opt in self.opt.keys():
            i = self.get_key_index(data, opt, starting)
            if i < idx and i != -1:
                idx = i
        if idx == len(data):
            idx = -1
        return idx

    def get_elem_desc(self, data, key):
        """TODO """

    def get_elem_param(self):
        """TODO """

    def get_raise_indexes(self, data):
        """Get from a docstring the next raise name indexes.
        In javadoc style it is after @raise.

        :param data: string to parse
        :returns: start and end indexes of found element else (-1, -1)
          or else (-2, -2) if try to use params style but no parameters were provided.
          Note: the end index is the index after the last name character
        :rtype: tuple

        """
        start, end = -1, -1
        stl_param = self.opt['raise'][self.style['in']]['name']
        if self.style['in'] in self.tagstyles + ['unknown']:
            idx_p = self.get_key_index(data, 'raise')
            if idx_p >= 0:
                idx_p += len(stl_param)
                m = re.match(RAISES_NAME_REGEX, data[idx_p:].strip())
                if m:
                    param = m.group(1)
                    start = idx_p + data[idx_p:].find(param)
                    end = start + len(param)

        if self.style['in'] in ['groups', 'unknown'] and (start, end) == (-1, -1):
            # search = '\s*(%s)' % '|'.join(self.groups['param'])
            # m = re.match(search, data.lower())
            # if m:
            #    key_param = m.group(1)
            pass

        return start, end

    def get_raise_description_indexes(self, data, prev=None):
        """Get from a docstring the next raise's description.
        In javadoc style it is after @param.

        :param data: string to parse
        :param prev: index after the param element name (Default value = None)
        :returns: start and end indexes of found element else (-1, -1)
        :rtype: tuple

        """
        start, end = -1, -1
        if not prev:
            _, prev = self.get_raise_indexes(data)
        if prev < 0:
            return -1, -1
        m = re.match(r'\W*(\w+)', data[prev:])
        if m:
            first = m.group(1)
            start = data[prev:].find(first)
            if start >= 0:
                start += prev
                if self.style['in'] in self.tagstyles + ['unknown']:
                    end = self.get_elem_index(data[start:])
                    if end >= 0:
                        end += start
                if self.style['in'] in ['params', 'unknown'] and end == -1:
                    p1, _ = self.get_raise_indexes(data[start:])
                    if p1 >= 0:
                        end = p1
                    else:
                        end = len(data)

        return start, end

    def _extra_tagstyle_elements(self, data):
        ret = {}
        style_param = self.opt['param'][self.style['in']]['name']
        style_type = self.opt['type'][self.style['in']]['name']
        # fixme for return and raise, ignore last char as there's an optional 's' at the end and they are not managed in this function
        style_return = self.opt['return'][self.style['in']]['name'][:-1]
        style_raise = self.opt['raise'][self.style['in']]['name'][:-1]
        last_element = {'nature': None, 'name': None}
        for line in data.splitlines():
            param_name = None
            param_type = None
            param_description = None
            param_part = None
            # parameter statement
            if line.strip().startswith(style_param):
                last_element['nature'] = 'param'
                last_element['name'] = None
                line = line.strip().replace(style_param, '', 1).strip()
                if ':' in line:
                    param_part, param_description = line.split(':', 1)
                else:
                    print("WARNING: malformed docstring parameter")
                res = re.split(r'\s+', param_part.strip())
                if len(res) == 1:
                    param_name = res[0].strip()
                elif len(res) == 2:
                    param_type, param_name = res[0].strip(), res[1].strip()
                else:
                    print("WARNING: malformed docstring parameter")
                if param_name:
                    # keep track in case of multiline
                    last_element['nature'] = 'param'
                    last_element['name'] = param_name
                    if param_name not in ret:
                        ret[param_name] = {'type': None, 'type_in_param': None, 'description': None}
                    if param_type:
                        ret[param_name]['type_in_param'] = param_type
                    if param_description:
                        ret[param_name]['description'] = param_description.strip()
                else:
                    print("WARNING: malformed docstring parameter: unable to extract name")
            # type statement
            elif line.strip().startswith(style_type):
                last_element['nature'] = 'type'
                last_element['name'] = None
                line = line.strip().replace(style_type, '', 1).strip()
                if ':' in line:
                    param_name, param_type = line.split(':', 1)
                    param_name = param_name.strip()
                    param_type = param_type.strip()
                else:
                    print("WARNING: malformed docstring parameter")
                if param_name:
                    # keep track in case of multiline
                    last_element['nature'] = 'type'
                    last_element['name'] = param_name
                    if param_name not in ret:
                        ret[param_name] = {'type': None, 'type_in_param': None, 'description': None}
                    if param_type:
                        ret[param_name]['type'] = param_type.strip()
            elif line.strip().startswith(style_raise) or line.startswith(style_return):
                # fixme not managed in this function
                last_element['nature'] = 'raise-return'
                last_element['name'] = None
            else:
                # suppose to be line of a multiline element
                if last_element['nature'] == 'param':
                    ret[last_element['name']]['description'] += f"\n{line}"
                elif last_element['nature'] == 'type':
                    ret[last_element['name']]['description'] += f"\n{line}"
        return ret

    def _extract_not_tagstyle_old_way(self, data):
        ret = {}
        listed = 0
        loop = True
        maxi = 10000  # avoid infinite loop but should never happen
        i = 0
        while loop:
            i += 1
            if i > maxi:
                loop = False
            start, end = self.get_param_indexes(data)
            if start >= 0:
                param = data[start: end]
                desc = ''
                param_end = end
                start, end = self.get_param_description_indexes(data, prev=end)
                if start > 0:
                    desc = data[start: end].strip()
                if end == -1:
                    end = param_end
                ptype = ''
                start, pend = self.get_param_type_indexes(data, name=param, prev=end)
                if start > 0:
                    ptype = data[start: pend].strip()
                if param in ret:
                    print(f"WARNING: unexpected parsing duplication of docstring parameter '{param}'")
                ret[param] = {'type': ptype, 'type_in_param': None, 'description': desc}
                data = data[end:]
                listed += 1
            else:
                loop = False
        if i > maxi:
            print("WARNING: an infinite loop was reached while extracting docstring parameters (>10000). This should never happen!!!")
        return ret

    def extract_elements(self, data) -> dict:
        """Extract parameter name, description and type from docstring"""
        ret = []
        tagstyles = self.tagstyles + ['unknown']
        if self.style['in'] in tagstyles:
            ret = self._extra_tagstyle_elements(data)
        else:
            # fixme enhance management of other styles
            ret = self._extract_not_tagstyle_old_way(data)
        return ret

    def get_param_indexes(self, data):
        """Get from a docstring the next parameter name indexes.
        In javadoc style it is after @param.

        :param data: string to parse
        :returns: start and end indexes of found element else (-1, -1)
          or else (-2, -2) if try to use params style but no parameters were provided.
          Note: the end index is the index after the last name character
        :rtype: tuple

        """
        # TODO: new method to extract an element's name so will be available for @param and @types and other styles (:param, \param)
        start, end = -1, -1
        stl_param = self.opt['param'][self.style['in']]['name']
        if self.style['in'] in self.tagstyles + ['unknown']:
            idx_p = self.get_key_index(data, 'param')
            if idx_p >= 0:
                idx_p += len(stl_param)
                m = re.match(r'^([\w]+)', data[idx_p:].strip())
                if m:
                    param = m.group(1)
                    start = idx_p + data[idx_p:].find(param)
                    end = start + len(param)

        if self.style['in'] in ['groups', 'unknown'] and (start, end) == (-1, -1):
            # search = '\s*(%s)' % '|'.join(self.groups['param'])
            # m = re.match(search, data.lower())
            # if m:
            #    key_param = m.group(1)
            pass

        if self.style['in'] in ['params', 'groups', 'unknown'] and (start, end) == (-1, -1):
            if not self.params:
                return -2, -2
            idx = -1
            param = None
            for p in self.params:
                p = p['param']
                i = data.find('\n' + p)
                if i >= 0:
                    if idx == -1 or i < idx:
                        idx = i
                        param = p
            if idx != -1:
                start, end = idx, idx + len(param)
        return start, end

    def get_param_description_indexes(self, data, prev=None):
        """Get from a docstring the next parameter's description.
        In javadoc style it is after @param.

        :param data: string to parse
        :param prev: index after the param element name (Default value = None)
        :returns: start and end indexes of found element else (-1, -1)
        :rtype: tuple

        """
        start, end = -1, -1
        if not prev:
            _, prev = self.get_param_indexes(data)
        if prev < 0:
            return -1, -1
        m = re.match(r'\W*(\w+)', data[prev:])
        if m:
            first = m.group(1)
            start = data[prev:].find(first)
            if start >= 0:
                if '\n' in data[prev:prev+start]:
                    # avoid to get next element as a description
                    return -1, -1
                start += prev
                if self.style['in'] in self.tagstyles + ['unknown']:
                    end = self.get_elem_index(data[start:])
                    if end >= 0:
                        end += start
                if self.style['in'] in ['params', 'unknown'] and end == -1:
                    p1, _ = self.get_param_indexes(data[start:])
                    if p1 >= 0:
                        end = p1
                    else:
                        end = len(data)

        return start, end

    def get_param_type_indexes(self, data, name=None, prev=None):
        """Get from a docstring a parameter type indexes.
        In javadoc style it is after @type.

        :param data: string to parse
        :param name: the name of the parameter (Default value = None)
        :param prev: index after the previous element (param or param's description) (Default value = None)
        :returns: start and end indexes of found element else (-1, -1)
          Note: the end index is the index after the last included character or -1 if
          reached the end
        :rtype: tuple

        """
        start, end = -1, -1
        stl_type = self.opt['type'][self.style['in']]['name']
        if not prev:
            _, prev = self.get_param_description_indexes(data)
        if prev >= 0:
            if self.style['in'] in self.tagstyles + ['unknown']:
                idx = self.get_elem_index(data[prev:])
                if idx >= 0 and data[prev + idx:].startswith(stl_type):
                    idx = prev + idx + len(stl_type)
                    m = re.match(r'\W*(\w+)\W+(\w+)\W*', data[idx:].strip())
                    if m:
                        param = m.group(1).strip()
                        if (name and param == name) or not name:
                            desc = m.group(2)
                            start = data[idx:].find(desc) + idx
                            end = self.get_elem_index(data[start:])
                            if end >= 0:
                                end += start

            if self.style['in'] in ['params', 'unknown'] and (start, end) == (-1, -1):
                # TODO: manage this
                pass

        return start, end

    def get_return_description_indexes(self, data):
        """Get from a docstring the return parameter description indexes.
        In javadoc style it is after @return.

        :param data: string to parse
        :returns: start and end indexes of found element else (-1, -1)
          Note: the end index is the index after the last included character or -1 if
          reached the end
        :rtype: tuple

        """
        start, end = -1, -1
        stl_return = self.opt['return'][self.style['in']]['name']
        if self.style['in'] in self.tagstyles + ['unknown']:
            idx = self.get_key_index(data, 'return')
            idx_abs = idx
            # search starting description
            if idx >= 0:
                # FIXME: take care if a return description starts with <, >, =,...
                m = re.match(r'\W*(\w+)', data[idx_abs + len(stl_return):])
                if m:
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
            # TODO: manage this
            pass

        return start, end

    def get_return_type_indexes(self, data):
        """Get from a docstring the return parameter type indexes.
        In javadoc style it is after @rtype.

        :param data: string to parse
        :returns: start and end indexes of found element else (-1, -1)
          Note: the end index is the index after the last included character or -1 if
          reached the end
        :rtype: tuple

        """
        start, end = -1, -1
        stl_rtype = self.opt['rtype'][self.style['in']]['name']
        if self.style['in'] in self.tagstyles + ['unknown']:
            dstart, dend = self.get_return_description_indexes(data)
            # search the start
            if dstart >= 0 and dend > 0:
                idx = self.get_elem_index(data[dend:])
                if idx >= 0 and data[dend + idx:].startswith(stl_rtype):
                    idx = dend + idx + len(stl_rtype)
                    m = re.match(r'\W*(\w+)', data[idx:])
                    if m:
                        first = m.group(1)
                        start = data[idx:].find(first) + idx
            # search the end
            idx = self.get_elem_index(data[start:])
            if idx > 0:
                end = idx + start

        if self.style['in'] in ['params', 'unknown'] and (start, end) == (-1, -1):
            # TODO: manage this
            pass

        return start, end


class DocString(object):
    """This class represents the docstring"""

    def __init__(self, elem_raw, spaces='', docs_raw=None, quotes="'''", input_style=None, output_style=None,
                 first_line=False, trailing_space=True, type_stub=False, before_lim='', num_of_spaces=4,
                 skip_empty=False, **kwargs):
        """
        :param elem_raw: raw data of the element (def or class).
        :param spaces: the leading whitespaces before the element
        :param docs_raw: the raw data of the docstring part if any.
        :param quotes: the type of quotes to use for output: ' ' ' or " " "
        :param style_in: docstring input style ('javadoc', 'reST', 'groups', 'numpydoc', 'google', None).
          If None will be autodetected
        :type style_in: string
        :param style_out: docstring output style ('javadoc', 'reST', 'groups', 'numpydoc', 'google')
        :type style_out: string
        :param first_line: indicate if description should start
          on first or second line
        :type first_line: boolean
        :param trailing_space: if set, a trailing space will be inserted in places where the user
          should write a description
        :type trailing_space: boolean
        :param type_stub: if set, an empty stub will be created for a parameter type
        :type type_stub: boolean
        :param before_lim: specify raw or unicode or format docstring type (ie. "r" for r'''... or "fu" for fu'''...)
        :param num_of_spaces: the number of spaces to indent
        :type num_of_spaces: integer
        :param skip_empty: if set, will skip writing the params, returns, or raises if they are empty
        :type skip_empty: boolean

        """
        self.dst = DocsTools()
        self.before_lim = before_lim
        self.first_line = first_line
        self.trailing_space = ''
        self.type_stub = type_stub
        if trailing_space:
            self.trailing_space = ' '
        if docs_raw and not input_style:
            self.dst.autodetect_style(docs_raw)
        elif input_style:
            self.set_input_style(input_style)
        if output_style:
            self.set_output_style(output_style)
        self.element = {
            'raw': elem_raw,
            'name': None,
            'type': None,
            'params': [],
            'spaces': spaces,
            'rtype': None,
            }
        if docs_raw:
            docs_raw = docs_raw.strip()
            if docs_raw.startswith('"""') or docs_raw.startswith("'''"):
                docs_raw = docs_raw[3:]
            if docs_raw.endswith('"""') or docs_raw.endswith("'''"):
                docs_raw = docs_raw[:-3]
        self.docs = {
            'in': {
                'raw': docs_raw,
                'doctests': "",
                'desc': None,
                'params': [],
                'types': [],
                'return': None,
                'rtype': None,
                'raises': []
                },
            'out': {
                'raw': '',
                'desc': None,
                'params': [],
                'types': [],
                'return': None,
                'rtype': None,
                'raises': [],
                'spaces': spaces + ' ' * kwargs.get('indent', 2)
                }
            }
        if '\t' in spaces:
            self.docs['out']['spaces'] = spaces + '\t'
        elif (len(spaces) % 4) == 0 or spaces == '':
            # FIXME: should bug if tabs for class or function (as spaces=='')
            self.docs['out']['spaces'] = spaces + ' ' * 4
        self.parsed_elem = False
        self.parsed_docs = False
        self.generated_docs = False
        self._options = {
            'hint_rtype_priority': True,  # priority in type hint else in docstring
            'hint_type_priority': True,  # priority in type hint else in docstring
            'rst_type_in_param_priority': True,  # in reST docstring priority on type present in param else on type
        }

        self.parse_definition()
        self.quotes = quotes
        self.num_of_spaces = num_of_spaces
        self.skip_empty = skip_empty

    def __str__(self):
        # for debugging
        txt = "\n\n** " + str(self.element['name'])
        txt += ' of type ' + str(self.element['deftype']) + ':'
        txt += str(self.docs['in']['desc']) + '\n'
        txt += '->' + str(self.docs['in']['params']) + '\n'
        txt += '***>>' + str(self.docs['out']['raw']) + '\n' + '\n'
        return txt

    def __repr__(self):
        return self.__str__()

    def get_input_docstring(self):
        """Get the input raw docstring.

        :returns: the input docstring if any.
        :rtype: str or None

        """
        return self.docs['in']['raw']

    def get_input_style(self):
        """Get the input docstring style

        :returns: the style for input docstring
        :rtype: style: str

        """
        # TODO: use a getter
        return self.dst.style['in']

    def set_input_style(self, style):
        """Sets the input docstring style

        :param style: style to set for input docstring
        :type style: str

        """
        # TODO: use a setter
        self.dst.style['in'] = style

    def get_output_style(self):
        """Sets the output docstring style

        :returns: the style for output docstring
        :rtype: style: str

        """
        # TODO: use a getter
        return self.dst.style['out']

    def set_output_style(self, style):
        """Sets the output docstring style

        :param style: style to set for output docstring
        :type style: str

        """
        # TODO: use a setter
        self.dst.style['out'] = style

    def get_spaces(self):
        """Get the output docstring initial spaces.

        :returns: the spaces

        """
        return self.docs['out']['spaces']

    def set_spaces(self, spaces):
        """Set for output docstring the initial spaces.

        :param spaces: the spaces to set

        """
        self.docs['out']['spaces'] = spaces

    def parse_definition(self, raw=None):
        """Parses the element's elements (type, name and parameters) :)
        e.g.: def methode(param1, param2='default')
        def                      -> type
        methode                  -> name
        param1, param2='default' -> parameters

        :param raw: raw data of the element (def or class). If None will use `self.element['raw']` (Default value = None)

        """
        # TODO: retrieve return from element external code (in parameter)
        if raw is None:
            l = self.element['raw'].strip()
        else:
            l = raw.strip()
        is_class = False
        if l.startswith('async def ') or l.startswith('def ') or l.startswith('class '):
            # retrieves the type
            if l.startswith('def'):
                self.element['deftype'] = 'def'
                l = l.replace('def ', '')
            elif l.startswith('async'):
                self.element['deftype'] = 'def'
                l = l.replace('async def ', '')
            else:
                self.element['deftype'] = 'class'
                l = l.replace('class ', '')
                is_class = True
            # retrieves the name
            self.element['name'] = l[:l.find('(')].strip()
            if not is_class:
                extracted = self._extract_signature_elements(self._remove_signature_comment(l))
                # remove self and cls parameters if any and also empty params (if no param)
                remove_keys = []
                for key in extracted['parameters']:
                    if extracted['parameters'][key]['param'] in ['self', 'cls']:
                        remove_keys.append(key)
                    elif not extracted['parameters'][key]['param']:
                        remove_keys.append(key)
                for key in remove_keys:
                    del extracted['parameters'][key]
                if extracted['return_type']:
                    self.element['rtype'] = extracted['return_type'] # TODO manage this
                self.element['params'].extend(extracted['parameters'].values())
        self.parsed_elem = True

    def _remove_signature_comment(self, txt):
        """If there is a comment at the end of the signature statement, remove it"""
        ret = ""
        inside = None
        end_inside = {'(': ')', '{': '}', '[': ']', "'": "'", '"': '"'}
        for c in txt:
            if (inside and end_inside[inside] != c) or (not inside and c in end_inside.keys()):
                if not inside:
                    inside = c
                ret += c
                continue
            if inside and c == end_inside[inside]:
                inside = None
                ret += c
                continue
            if not inside and c == '#':
                # found a comment so signature is finished we stop parsing
                break
            ret += c
        return ret

    def _extract_signature_elements(self, txt):
        start = txt.find('(') + 1
        end_start = txt.rfind(')')
        end_end = txt.rfind(':')
        return_type = txt[end_start + 1:end_end].replace(' ', '').replace('\t', '').replace('->', '')
        elems = {}
        elem_idx = 0
        reading = 'param'
        elems[elem_idx] = {'type': '', 'param': '', 'default': ''}
        inside = None
        end_inside = {'(': ')', '{': '}', '[': ']', "'": "'", '"': '"'}
        for c in txt[start:end_start]:
            if (inside and end_inside[inside] != c) or (not inside and c in end_inside.keys()):
                if not inside:
                    inside = c
                if reading == 'type':
                    elems[elem_idx]['type'] += c
                elif reading == 'default':
                    elems[elem_idx]['default'] += c
                else:
                    # FIXME: this should not happen!
                    raise Exception("unexpected nested element after "+str(inside)+" while reading "+reading)
                continue
            if inside and c == end_inside[inside]:
                inside = None
            if reading == 'param':
                if c not in ': ,=':
                    elems[elem_idx]['param'] += c
                else:
                    if c == ' ' and elems[elem_idx]['param'] or c != ' ':
                        reading = 'after_param'
            elif reading == 'type':
                if c not in ',=':
                    elems[elem_idx]['type'] += c
                else:
                    reading = 'after_type'
            elif reading == 'default':
                if c != ',':
                    elems[elem_idx]['default'] += c
                else:
                    reading = 'after_default'
            if reading.startswith('after_'):
                if reading == 'after_param' and c == ':':
                    reading = 'type'
                elif c == ',':
                    elem_idx += 1
                    elems[elem_idx] = {'type': '', 'param': '', 'default': ''}
                    reading = 'param'
                elif c == '=':
                    reading = 'default'
        # strip extracted elements
        for elem in elems:
            for subelem in elems[elem]:
                if type(elems[elem][subelem]) is str:
                    elems[elem][subelem] = elems[elem][subelem].strip()
        return {
            'parameters': elems,
            'return_type': return_type.strip()
        }

    def _extract_docs_doctest(self):
        """Extract the doctests if found.
        If there are doctests, they are removed from the input data and set on
        a specific buffer as they won't be altered.

        :return: True if found and proceeded else False
        """
        result = False
        data = self.docs['in']['raw']
        start, end = self.dst.get_doctests_indexes(data)
        while start != -1:
            print (start, end)
            result = True
            datalst = data.splitlines()
            if self.docs['in']['doctests'] != "":
                self.docs['in']['doctests'] += '\n'
            self.docs['in']['doctests'] += '\n'.join(datalst[start:end + 1]) + '\n'
            self.docs['in']['raw'] = '\n'.join(datalst[:start] + datalst[end + 1:])
            data = self.docs['in']['raw']
            start, end = self.dst.get_doctests_indexes(data)
        if self.docs['in']['doctests'] != "":
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['doctests'].splitlines()])
            self.docs['out']['doctests'] = data
        return result

    def _extract_docs_description(self):
        """Extract main description from docstring"""
        # FIXME: the indentation of descriptions is lost
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        if self.dst.style['in'] == 'groups':
            idx = self.dst.get_group_index(data)
        elif self.dst.style['in'] == 'google':
            lines = data.splitlines()
            line_num = self.dst.googledoc.get_next_section_start_line(lines)
            if line_num == -1:
                idx = -1
            else:
                idx = len('\n'.join(lines[:line_num]))
        elif self.dst.style['in'] == 'numpydoc':
            lines = data.splitlines()
            line_num = self.dst.numpydoc.get_next_section_start_line(lines)
            if line_num == -1:
                idx = -1
            else:
                idx = len('\n'.join(lines[:line_num]))
        elif self.dst.style['in'] == 'unknown':
            idx = -1
        else:
            idx = self.dst.get_elem_index(data)
        if idx == 0:
            self.docs['in']['desc'] = ''
        elif idx == -1:
            self.docs['in']['desc'] = data
        else:
            self.docs['in']['desc'] = data[:idx]

    def _extract_groupstyle_docs_params(self):
        """Extract group style parameters"""
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        idx = self.dst.get_group_key_line(data, 'param')
        if idx >= 0:
            data = data.splitlines()[idx + 1:]
            end = self.dst.get_group_line('\n'.join(data))
            end = end if end != -1 else len(data)
            for i in range(end):
                # FIXME: see how retrieve multiline param description and how get type
                line = data[i]
                param = None
                desc = ''
                ptype = ''
                m = re.match(r'^\W*(\w+)[\W\s]+(\w[\s\w]+)', line.strip())
                if m:
                    param = m.group(1).strip()
                    desc = m.group(2).strip()
                else:
                    m = re.match(r'^\W*(\w+)\W*', line.strip())
                    if m:
                        param = m.group(1).strip()
                if param:
                    self.docs['in']['params'].append((param, desc, ptype))

    def _extract_tagstyle_docs_params(self):
        """ """
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        extracted = self.dst.extract_elements(data)
        for param_name, param in extracted.items():
            param_type = param['type']
            if self._options['rst_type_in_param_priority'] and param['type_in_param']:
                param_type = param['type_in_param']
            desc = param['description'] if param['description'] else ""
            self.docs['in']['params'].append((param_name, desc, param_type))

    def _old_extract_tagstyle_docs_params(self):
        """ """
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
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
                param_end = end
                start, end = self.dst.get_param_description_indexes(data, prev=end)
                if start > 0:
                    desc = data[start: end].strip()
                if end == -1:
                    end = param_end
                ptype = ''
                start, pend = self.dst.get_param_type_indexes(data, name=param, prev=end)
                if start > 0:
                    ptype = data[start: pend].strip()
                # a parameter is stored with: (name, description, type)
                self.docs['in']['params'].append((param, desc, ptype))
                data = data[end:]
                listed += 1
            else:
                loop = False
        if i > maxi:
            print("WARNING: an infinite loop was reached while extracting docstring parameters (>10000). This should never happen!!!")

    def _extract_docs_params(self):
        """Extract parameters description and type from docstring. The internal computed parameters list is
        composed by tuples (parameter, description, type).

        """
        if self.dst.style['in'] == 'numpydoc':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            self.docs['in']['params'] += self.dst.numpydoc.get_param_list(data)
        elif self.dst.style['in'] == 'google':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            self.docs['in']['params'] += self.dst.googledoc.get_param_list(data)
        elif self.dst.style['in'] == 'groups':
            self._extract_groupstyle_docs_params()
        elif self.dst.style['in'] in ['javadoc', 'reST']:
            self._extract_tagstyle_docs_params()

    def _extract_groupstyle_docs_raises(self):
        """ """
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        idx = self.dst.get_group_key_line(data, 'raise')
        if idx >= 0:
            data = data.splitlines()[idx + 1:]
            end = self.dst.get_group_line('\n'.join(data))
            end = end if end != -1 else len(data)
            for i in range(end):
                # FIXME: see how retrieve multiline raise description
                line = data[i]
                param = None
                desc = ''
                m = re.match(r'^\W*([\w.]+)[\W\s]+(\w[\s\w]+)', line.strip())
                if m:
                    param = m.group(1).strip()
                    desc = m.group(2).strip()
                else:
                    m = re.match(r'^\W*(\w+)\W*', line.strip())
                    if m:
                        param = m.group(1).strip()
                if param:
                    self.docs['in']['raises'].append((param, desc))

    def _extract_tagstyle_docs_raises(self):
        """ """
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        listed = 0
        loop = True
        maxi = 10000  # avoid infinite loop but should never happen
        i = 0
        while loop:
            i += 1
            if i > maxi:
                loop = False
            start, end = self.dst.get_raise_indexes(data)
            if start >= 0:
                param = data[start: end]
                desc = ''
                start, end = self.dst.get_raise_description_indexes(data, prev=end)
                if start > 0:
                    desc = data[start: end].strip()
                # a parameter is stored with: (name, description)
                self.docs['in']['raises'].append((param, desc))
                data = data[end:]
                listed += 1
            else:
                loop = False
        if i > maxi:
            print("WARNING: an infinite loop was reached while extracting docstring parameters (>10000). This should never happen!!!")

    def _extract_docs_raises(self):
        """Extract raises description from docstring. The internal computed raises list is
        composed by tuples (raise, description).

        """
        if self.dst.style['in'] == 'numpydoc':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            self.docs['in']['raises'] += self.dst.numpydoc.get_raise_list(data)
        if self.dst.style['in'] == 'google':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            self.docs['in']['raises'] += self.dst.googledoc.get_raise_list(data)
        elif self.dst.style['in'] == 'groups':
            self._extract_groupstyle_docs_raises()
        elif self.dst.style['in'] in ['javadoc', 'reST']:
            self._extract_tagstyle_docs_raises()

    def _extract_groupstyle_docs_return(self):
        """ """
        # TODO: manage rtype
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        idx = self.dst.get_group_key_line(data, 'return')
        if idx >= 0:
            data = data.splitlines()[idx + 1:]
            end = self.dst.get_group_line('\n'.join(data))
            end = end if end != -1 else len(data)
            data = '\n'.join(data[:end]).strip()
            self.docs['in']['return'] = data.rstrip()

    def _extract_tagstyle_docs_return(self):
        """ """
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        start, end = self.dst.get_return_description_indexes(data)
        if start >= 0:
            if end >= 0:
                self.docs['in']['return'] = data[start:end].rstrip()
            else:
                self.docs['in']['return'] = data[start:].rstrip()
        start, end = self.dst.get_return_type_indexes(data)
        if start >= 0:
            if end >= 0:
                self.docs['in']['rtype'] = data[start:end].rstrip()
            else:
                self.docs['in']['rtype'] = data[start:].rstrip()

    def _extract_docs_return(self):
        """Extract return description and type"""
        if self.dst.style['in'] == 'numpydoc':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            self.docs['in']['return'] = self.dst.numpydoc.get_return_list(data)
            self.docs['in']['rtype'] = None
# TODO: fix this
        elif self.dst.style['in'] == 'google':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            self.docs['in']['return'] = self.dst.googledoc.get_return_list(data)
            self.docs['in']['rtype'] = None
        elif self.dst.style['in'] == 'groups':
            self._extract_groupstyle_docs_return()
        elif self.dst.style['in'] in ['javadoc', 'reST']:
            self._extract_tagstyle_docs_return()

    def _extract_docs_other(self):
        """Extract other specific sections"""
        if self.dst.style['in'] == 'numpydoc':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            lst = self.dst.numpydoc.get_list_key(data, 'also')
            lst = self.dst.numpydoc.get_list_key(data, 'ref')
            lst = self.dst.numpydoc.get_list_key(data, 'note')
            lst = self.dst.numpydoc.get_list_key(data, 'other')
            lst = self.dst.numpydoc.get_list_key(data, 'example')
            lst = self.dst.numpydoc.get_list_key(data, 'attr')
            # TODO do something with this?

    def parse_docs(self, raw=None, before_lim=''):
        """Parses the docstring

        :param raw: the data to parse if not internally provided (Default value = None)
        :param before_lim: specify raw or unicode or format docstring type (ie. "r" for r'''... or "fu" for fu'''...)

        """
        self.before_lim = before_lim
        if raw is not None:
            raw = raw.strip()
            if raw.startswith('"""') or raw.startswith("'''"):
                raw = raw[3:]
            if raw.endswith('"""') or raw.endswith("'''"):
                raw = raw[:-3]
            self.docs['in']['raw'] = raw
            self.dst.autodetect_style(raw)
        if self.docs['in']['raw'] is None:
            return
        self.dst.set_known_parameters(self.element['params'])
        self._extract_docs_doctest()
        self._extract_docs_params()
        self._extract_docs_return()
        self._extract_docs_raises()
        self._extract_docs_description()
        self._extract_docs_other()
        self.parsed_docs = True

    def _set_desc(self):
        """Sets the global description if any"""
        # TODO: manage different in/out styles
        if self.docs['in']['desc']:
            self.docs['out']['desc'] = self.docs['in']['desc']
        else:
            self.docs['out']['desc'] = ''

    def _set_params(self):
        """Sets the parameters with types, descriptions and default value if any
        taken from the input docstring and the signature parameters"""
        # TODO: manage different in/out styles
        # convert the list of signature's extracted params into a dict with the names of param as keys
        sig_params = {e['param']: {'type': e['type'], 'default': e['default']} for e in self.element['params']}
        # convert the list of docsting's extracted params into a dict with the names of param as keys
        docs_params = {
            name: {
                'description': desc,
                'type': param_type,
            } for name, desc, param_type in self.docs['in']['params']
        }
        for name in sig_params:
            # WARNING: Note that if a param in docstring isn't in the signature params, it will be dropped
            sig_type, sig_default = sig_params[name]['type'], sig_params[name]['default']
            out_description = ""
            out_type = sig_type if sig_type else None
            out_default = sig_default if sig_default else None
            if name in docs_params:
                out_description = docs_params[name]['description']
                if not out_type or (not self._options['hint_type_priority'] and docs_params[name]['type']):
                    out_type = docs_params[name]['type']
            self.docs['out']['params'].append((name, out_description, out_type, out_default))

    def _set_raises(self):
        """Sets the raises and descriptions"""
        # TODO: manage different in/out styles
        # manage setting if not mandatory for numpy but optional
        if self.docs['in']['raises']:
            if self.dst.style['out'] != 'numpydoc' or self.dst.style['in'] == 'numpydoc' or \
                    (self.dst.style['out'] == 'numpydoc' and
                     'raise' not in self.dst.numpydoc.get_excluded_sections()):
                # list of parameters is like: (name, description)
                self.docs['out']['raises'] = list(self.docs['in']['raises'])

    def _set_return(self):
        """Sets the return parameter with description and rtype if any"""
        # TODO: manage return retrieved from element code (external)
        # TODO: manage different in/out styles
        if type(self.docs['in']['return']) is list and self.dst.style['out'] not in ['groups', 'numpydoc', 'google']:
            # TODO: manage return names
            # manage not setting return if not mandatory for numpy
            lst = self.docs['in']['return']
            if lst:
                if lst[0][0] is not None:
                    self.docs['out']['return'] = "%s-> %s" % (lst[0][0], lst[0][1])
                else:
                    self.docs['out']['return'] = lst[0][1]
                self.docs['out']['rtype'] = lst[0][2]
        else:
            self.docs['out']['return'] = self.docs['in']['return']
            self.docs['out']['rtype'] = self.docs['in']['rtype']
        if (self._options['hint_rtype_priority'] or not self.docs['out']['rtype']) and self.element['rtype']:
            self.docs['out']['rtype'] = self.element['rtype']

    def _set_other(self):
        """Sets other specific sections"""
        # manage not setting if not mandatory for numpy
        if self.dst.style['in'] == 'numpydoc':
            if self.docs['in']['raw'] is not None:
                self.docs['out']['post'] = self.dst.numpydoc.get_raw_not_managed(self.docs['in']['raw'])
            elif 'post' not in self.docs['out'] or self.docs['out']['post'] is None:
                self.docs['out']['post'] = ''

    def _set_raw_params(self, sep):
        """Set the output raw parameters section

        :param sep: the separator of current style

        """
        raw = '\n'
        if self.skip_empty and not self.docs['out']['params']:
            return raw
        if self.dst.style['out'] == 'numpydoc':
            spaces = ' ' * self.num_of_spaces
            with_space = lambda s: '\n'.join([self.docs['out']['spaces'] + spaces +\
                                                    l.lstrip() if i > 0 else\
                                                    l for i, l in enumerate(s.splitlines())])
            raw += self.dst.numpydoc.get_key_section_header('param', self.docs['out']['spaces'])
            for p in self.docs['out']['params']:
                raw += self.docs['out']['spaces'] + p[0] + ' :'
                if p[2] is not None and len(p[2]) > 0:
                    raw += ' ' + p[2]
                raw += '\n'
                raw += self.docs['out']['spaces'] + spaces + with_space(p[1]).strip()
                if len(p) > 2:
                    if 'default' not in p[1].lower() and len(p) > 3 and p[3] is not None:
                        raw += ' (Default value = ' + str(p[3]) + ')'
                raw += '\n'
        elif self.dst.style['out'] == 'google':
            spaces = ' ' * self.num_of_spaces
            with_space = lambda s: '\n'.join([self.docs['out']['spaces'] +\
                                                    l.lstrip() if i > 0 else\
                                                    l for i, l in enumerate(s.splitlines())])
            raw += self.dst.googledoc.get_key_section_header('param', self.docs['out']['spaces'])
            for p in self.docs['out']['params']:
                raw += self.docs['out']['spaces'] + spaces + p[0]
                if p[2] is not None and len(p[2]) > 0:
                    raw += ' (' + p[2]
                    if len(p) > 3 and p[3] is not None:
                        raw += ', optional'
                    raw += ')'
                raw += ': ' + with_space(p[1]).strip()
                if len(p) > 2:
                    if 'default' not in p[1].lower() and len(p) > 3 and p[3] is not None:
                        raw += ' (Default value = ' + str(p[3]) + ')'
                raw += '\n'
        elif self.dst.style['out'] == 'groups':
            pass
        else:
            with_space = lambda s: '\n'.join(
                [self.docs['out']['spaces'] + l if i > 0 else l for i, l in enumerate(s.splitlines())]
            )
            if len(self.docs['out']['params']):
                for p in self.docs['out']['params']:
                    raw += self.docs['out']['spaces'] + self.dst.get_key('param', 'out') + ' ' + p[0] + sep + with_space(p[1]).strip()
                    if len(p) > 2:
                        if 'default' not in p[1].lower() and len(p) > 3 and p[3] is not None:
                            raw += ' (Default value = ' + str(p[3]) + ')'
                        if p[2] is not None and len(p[2]) > 0:
                            raw += '\n'
                            raw += self.docs['out']['spaces'] + self.dst.get_key('type', 'out') + ' ' + p[0] + sep + p[2]
                    if self.type_stub and (len(p) <= 2 or p[2] is None or len(p[2]) == 0):
                        raw += '\n'
                        raw += self.docs['out']['spaces'] + self.dst.get_key('type', 'out') + ' ' + p[0] + sep
                    raw += '\n'
        return raw

    def _set_raw_raise(self, sep):
        """Set the output raw exception section

        :param sep: the separator of current style

        """
        raw = ''
        if self.skip_empty and not self.docs['out']['raises']:
            return raw
        if self.dst.style['out'] == 'numpydoc':
            if 'raise' not in self.dst.numpydoc.get_excluded_sections():
                raw += '\n'
                if 'raise' in self.dst.numpydoc.get_mandatory_sections() or \
                        (self.docs['out']['raises'] and 'raise' in self.dst.numpydoc.get_optional_sections()):
                    spaces = ' ' * self.num_of_spaces
                    with_space = lambda s: '\n'.join([self.docs['out']['spaces'] + spaces + l.lstrip() if i > 0 else l for i, l in enumerate(s.splitlines())])
                    raw += self.dst.numpydoc.get_key_section_header('raise', self.docs['out']['spaces'])
                    if len(self.docs['out']['raises']):
                        for p in self.docs['out']['raises']:
                            raw += self.docs['out']['spaces'] + p[0] + '\n'
                            raw += self.docs['out']['spaces'] + spaces + with_space(p[1]).strip() + '\n'
                    raw += '\n'
        elif self.dst.style['out'] == 'google':
            if 'raise' not in self.dst.googledoc.get_excluded_sections():
                raw += '\n'
                if 'raise' in self.dst.googledoc.get_mandatory_sections() or \
                        (self.docs['out']['raises'] and 'raise' in self.dst.googledoc.get_optional_sections()):
                    spaces = ' ' * self.num_of_spaces
                    with_space = lambda s: '\n'.join([self.docs['out']['spaces'] + spaces + \
                                                            l.lstrip() if i > 0 else \
                                                            l for i, l in enumerate(s.splitlines())])
                    raw += self.dst.googledoc.get_key_section_header('raise', self.docs['out']['spaces'])
                    if len(self.docs['out']['raises']):
                        for p in self.docs['out']['raises']:
                            raw += self.docs['out']['spaces'] + spaces
                            if p[0] is not None:
                                raw += p[0] + ':' + sep
                            if p[1]:
                                raw += p[1].strip()
                            raw += '\n'
                    raw += '\n'
        elif self.dst.style['out'] == 'groups':
            pass
        else:
            with_space = lambda s: '\n'.join([self.docs['out']['spaces'] + l if i > 0 else l for i, l in enumerate(s.splitlines())])
            if len(self.docs['out']['raises']):
                if not self.docs['out']['params'] and not self.docs['out']['return']:
                    raw += '\n'
                for p in self.docs['out']['raises']:
                    raw += self.docs['out']['spaces'] + self.dst.get_key('raise', 'out') + ' '
                    if p[0] is not None:
                        raw += p[0] + sep
                    if p[1]:
                        raw += with_space(p[1]).strip()
                    raw += '\n'
            raw += '\n'
        return raw

    def _set_raw_return(self, sep):
        """Set the output raw return section

        :param sep: the separator of current style

        """
        raw = ''
        if self.skip_empty and not self.docs['out']['return']:
            return raw
        if self.dst.style['out'] == 'numpydoc':
            raw += '\n'
            spaces = ' ' * self.num_of_spaces
            with_space = lambda s: '\n'.join([self.docs['out']['spaces'] + spaces + l.lstrip() if i > 0 else l for i, l in enumerate(s.splitlines())])
            raw += self.dst.numpydoc.get_key_section_header('return', self.docs['out']['spaces'])
            if self.docs['out']['rtype']:
                rtype = self.docs['out']['rtype']
            else:
                rtype = 'type'
            # case of several returns
            if type(self.docs['out']['return']) is list:
                for ret_elem in self.docs['out']['return']:
                    # if tuple (name, desc, rtype) else string desc
                    if type(ret_elem) is tuple and len(ret_elem) == 3:
                        rtype = ret_elem[2]
                        if rtype is None:
                            rtype = ''
                        raw += self.docs['out']['spaces']
                        if ret_elem[0]:
                            raw += ret_elem[0] + ' : '
                        raw += rtype + '\n' + self.docs['out']['spaces'] + spaces + with_space(ret_elem[1]).strip() + '\n'
                    else:
                        # There can be a problem
                        raw += self.docs['out']['spaces'] + rtype + '\n'
                        raw += self.docs['out']['spaces'] + spaces + with_space(str(ret_elem)).strip() + '\n'
            # case of a unique return
            elif self.docs['out']['return'] is not None:
                raw += self.docs['out']['spaces'] + rtype
                raw += '\n' + self.docs['out']['spaces'] + spaces + with_space(self.docs['out']['return']).strip() + '\n'
        elif self.dst.style['out'] == 'google':
            raw += '\n'
            spaces = ' ' * self.num_of_spaces
            with_space = lambda s: '\n'.join([self.docs['out']['spaces'] + spaces +\
                                                    l.lstrip() if i > 0 else\
                                                    l for i, l in enumerate(s.splitlines())])
            raw += self.dst.googledoc.get_key_section_header('return', self.docs['out']['spaces'])
            if self.docs['out']['rtype']:
                rtype = self.docs['out']['rtype']
            else:
                rtype = None
            # case of several returns
            if type(self.docs['out']['return']) is list:
                for ret_elem in self.docs['out']['return']:
                    # if tuple (name=None, desc, rtype) else string desc
                    if type(ret_elem) is tuple and len(ret_elem) == 3:
                        rtype = ret_elem[2]
                        if rtype is None:
                            rtype = ''
                        raw += self.docs['out']['spaces'] + spaces
                        raw += rtype + ': ' + with_space(ret_elem[1]).strip() + '\n'
                    else:
                        # There can be a problem
                        if rtype:
                            raw += self.docs['out']['spaces'] + spaces + rtype + ': '
                            raw += with_space(str(ret_elem)).strip() + '\n'
                        else:
                            raw += self.docs['out']['spaces'] + spaces + with_space(str(ret_elem)).strip() + '\n'
            # case of a unique return
            elif self.docs['out']['return'] is not None:
                if rtype:
                    raw += self.docs['out']['spaces'] + spaces + rtype + ': '
                    raw += with_space(self.docs['out']['return']).strip() + '\n'
                else:
                    raw += self.docs['out']['spaces'] + spaces + with_space(self.docs['out']['return']).strip() + '\n'
        elif self.dst.style['out'] == 'groups':
            pass
        else:
            with_space = lambda s: '\n'.join([self.docs['out']['spaces'] + l if i > 0 else l for i, l in enumerate(s.splitlines())])
            if self.docs['out']['return']:
                if not self.docs['out']['params']:
                    raw += '\n'
                raw += self.docs['out']['spaces'] + self.dst.get_key('return', 'out') + sep + with_space(self.docs['out']['return'].rstrip()).strip() + '\n'
            if self.docs['out']['rtype']:
                if not self.docs['out']['params']:
                    raw += '\n'
                raw += self.docs['out']['spaces'] + self.dst.get_key('rtype', 'out') + sep + self.docs['out']['rtype'].rstrip() + '\n'
        return raw

    def _set_raw(self):
        """Sets the output raw docstring"""
        sep = self.dst.get_sep(target='out')
        sep = sep + ' ' if sep != ' ' else sep
        with_space = lambda s: '\n'.join([self.docs['out']['spaces'] + l if i > 0 else l for i, l in enumerate(s.splitlines())])

        # sets the description section
        raw = self.docs['out']['spaces'] + self.before_lim + self.quotes
        desc = self.docs['out']['desc'].strip()
        if not desc or not desc.count('\n'):
            if not self.docs['out']['params'] and not self.docs['out']['return'] and not self.docs['out']['rtype'] and not self.docs['out']['raises']:
                raw += desc if desc else self.trailing_space
                raw += self.quotes
                self.docs['out']['raw'] = raw.rstrip()
                return
        if not self.first_line:
            raw += '\n' + self.docs['out']['spaces']
        raw += with_space(self.docs['out']['desc']).strip() + '\n'

        # sets the parameters section
        raw += self._set_raw_params(sep)

        # sets the return section
        raw += self._set_raw_return(sep)

        # sets the raises section
        raw += self._set_raw_raise(sep)

        # sets post specific if any
        if 'post' in self.docs['out']:
            raw += self.docs['out']['spaces'] + with_space(self.docs['out']['post']).strip() + '\n'

        # sets the doctests if any
        if 'doctests' in self.docs['out']:
            raw += self.docs['out']['spaces'] + with_space(self.docs['out']['doctests']).strip() + '\n'

        if raw.count(self.quotes) == 1:
            raw += self.docs['out']['spaces'] + self.quotes
        self.docs['out']['raw'] = raw.rstrip()

    def generate_docs(self):
        """Generates the output docstring"""
        if self.dst.style['out'] == 'numpydoc' and self.dst.numpydoc.first_line is not None:
            self.first_line = self.dst.numpydoc.first_line
        self._set_desc()
        self._set_params()
        self._set_return()
        self._set_raises()
        self._set_other()
        self._set_raw()
        self.generated_docs = True

    def get_raw_docs(self):
        """Generates raw docstring

        :returns: the raw docstring

        """
        if not self.generated_docs:
            self.generate_docs()
        return self.docs['out']['raw']


if __name__ == "__main__":
    help(DocString)
