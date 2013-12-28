
class DocString(object):
    '''This class represents the docstring'''

    def __init__(self, elem_raw=None, docs_raw=None):
        '''
        @param elem_raw: raw data of the element (def or class).
        @param docs_raw: the raw data of the docstring part if any.
        '''
        self.element = {}
        self.element['raw'] = elem_raw
        self.element['name'] = None
        self.element['type'] = None
        self.element['params'] = []
        self.docs_in['raw'] = docs_raw
        self.docs_in['desc'] = None
        self.docs_in['params'] = []
        self.docs_out['raw'] = docs_raw
        self.docs_out['desc'] = None
        self.docs_out['params'] = []

    def __str__(self):
        txt = "element: " + str(self.element['name']) + ' of type ' + str(self.element['type']) + '\n'
        txt += '  -> ' + str(self.raw) + '\n'
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
            l = l[l.find('(')+1: l.find(')')].strip()
            lst = [c.strip() for c in l.split(',')]
            for e in lst:
                if '=' in e:
                    k, v = e.split('=', 1)
                    self.element['params'].append({k.strip(): v.strip()})
                else:
                    self.element['params'].append(e);

    def parse_docs(self, raw=None):
        if raw is not None:
            self.docs_in['raw'] = raw
        if self.docs_in['raw'] is None:
            return
        raw = self.docs_in['raw']
        nb_params = raw.count('@param')
        nb_return = raw.count('@return')

    def proceed(self):
        '''Proceed the raw docstring part if any.
        '''

