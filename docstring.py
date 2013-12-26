
class DocString(dict):
    '''This class represents the docstring'''

    def __init__(self, element=None, docs_raw=None):
        '''
        @param element: raw data of the element (def or class).
        @param docs_raw: the raw data of the docstring part if any.
        '''
        self.element = {}
        self.element['raw'] = element
        self.element['name'] = None
        self.element['type'] = None
        self.element['params'] = []
        self.raw = docs_raw

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
            l = l.find('(')+1: l.find(')').strip()
            lst = [c.strip() for c in l.split(',')]
            for e in lst:
                if '=' in e:
                    k, v = e.split('=', 1)
                    self.element['params'].append({k.strip(): v.strip()})
                else:
                    self.element['params'].append(e);

    def proceed(self):
        '''Proceed the raw docstring part if any.
        '''


