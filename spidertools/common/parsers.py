
import html.parser as parser
import logging

from spidertools.common import element as el


log = logging.getLogger("talos.utils.parsers")


def attrs_to_dict(attrs):
    """
        Convert a list of tuples of (name, value) attributes to a single dict of attributes [name] -> value
    :param attrs: List of attribute tuples
    :return: Dict of attributes
    """
    out = {}
    for attr in attrs:
        if out.get(attr[0]) is None:
            out[attr[0]] = attr[1]
        else:
            if not isinstance(out[attr[0]], list):
                out[attr[0]] = [out[attr[0]]]
            out[attr[0]].append(attr[1])
    return out


class TreeGen(parser.HTMLParser):
    """
        HTML Parser subclass to convert an HTML document into a DOM Tree of Nodes
    """

    def __init__(self):
        """
            Initialize the TreeGen parser
        """
        super().__init__()
        self.heads = []
        self.cur = None

    def reset(self):
        """
            Reset the parser, prepares it to receive entirely new input data
        """
        super().reset()
        self.heads = []
        self.cur = None

    def close(self):
        """
            Close the current HTML tree being constructed and returns its heads
        :return: Heads of the parsed input
        """
        super().close()
        return self.heads

    def error(self, message):
        """
            Error handler for the HTML parser
        :param message: Parser error message
        """
        log.error(f"Parser Error: {message}")

    def handle_starttag(self, tag, attrs):
        """
            Handle an element starttag. Opens an element, and prepares to add children if it's not self closing
        :param tag: Element tag
        :param attrs: Element attributes
        """
        element = el.Element(tag, attrs_to_dict(attrs))
        if self.cur is None:
            self.heads.append(element)
        else:
            self.cur.add_child(element)

        if tag not in el.Element.SELF_CLOSING:
            self.cur = element

    def handle_endtag(self, tag):
        """
            Handle an element endtag. Closes the current element if it's not self closing
        :param tag: Element tag
        """
        if tag not in el.Element.SELF_CLOSING:
            self.cur = self.cur.parent

    def handle_data(self, data):
        """
            Handle internal element data. Adds a new Content object to the current Element
        :param data: Element internal data
        """
        data = data.strip()
        if not data:
            return

        content = el.Content(data)
        if self.cur is None:
            self.heads.append(content)
        else:
            self.cur.add_child(content)


class _Sentinel:
    pass


_Sentinel = _Sentinel()


class ArgParser:
    """
        Python command-line argument parser. Provides a consistent interface for flags and options
    """

    def __init__(self, args):
        """
            Initialize a new parser from a set of arguments.
        :param args: List of arguments, commonly `sys.argv`
        """
        self.source = args[0]
        args = args[1:]

        self.args = []
        self.flags = []
        self.options = {}

        for arg in args:
            if arg.startswith("--"):
                if "=" in arg:
                    arg = arg[2:]
                    pair = arg.split("=")
                    self.options[pair[0]] = pair[1]
                else:
                    self.flags.append(arg[2:])
            elif arg.startswith("-"):
                for char in arg[1:]:
                    self.flags.append(char)
            else:
                self.args.append(arg)

    def get_arg(self, pos, default=_Sentinel):
        """
            Get the argument from a given position, with optional default if argument doesn't exist
        :param pos: Position of argument, zero-indexed
        :param default: Optional default, returned if argument doesn't exist
        :return: Argument at given position or default
        """
        try:
            return self.args[pos]
        except IndexError:
            if default is not _Sentinel:
                return default
            raise

    def has_flag(self, *, short=None, long=None):
        """
            Check whether the passed arguments contain a given flag. Can provide both short
            and long forms at the same time for ease of use
        :param short: Short form of the flag, should be a single character
        :param long: Long form of the flag, can be any string
        :return: Whether flag exists
        """
        return (short in self.flags) or (long in self.flags)

    def has_option(self, name):
        """
            Check whether the passed arguments contain a given option
        :param name: Name to check in options for
        :return: Whether option was provided
        """
        return name in self.options

    def get_option(self, name, default=_Sentinel):
        """
            Get the value of a given option, with optional default if option doesn't exist.
        :param name: Name of the option to get
        :param default: Optional default, returned if argument doesn't exist
        :return: Option with given name or default
        """
        if default is _Sentinel:
            return self.options.get(name)
        else:
            return self.options.get(name, default)
