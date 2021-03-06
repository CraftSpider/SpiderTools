
import abc
import io

from . import errors
from .enums import Instruction


class CLLexer(metaclass=abc.ABCMeta):
    """
        Abstract base for CommandLang lexers. Defines the interface they are expected to provide
    """

    __slots__ = ()

    @abc.abstractmethod
    def lex_lang(self, data):
        """
            Run the CL lexer. Should return a list of tokens to pass to an interpreter
        :param data: Text input to run the lexer on
        :return: List of tokens
        """


class DefaultCLLexer(CLLexer):
    """
        Default/Base lexer for CommandLang. Converts string into List[Tuple[Instruction, ...]]
    """

    __slots__ = ("_buffer",)

    def __init__(self):
        """
            Initializes the default lexer, setting the _buffer to None as a placeholder
        """
        self._buffer = None

    def _recurse(self, text):
        """
            Recursively lex, saving the buffer so it can be overwritten then restoring it
        :param text: Text to lex
        :return: Result of lexing text
        """
        buffer = self._buffer
        result = self.lex_lang(text)
        self._buffer = buffer
        return result

    def _lex_if(self):
        """
            Lex an if if statement in the current string
        :return: Tuple result of lexing, (type, statement, text)
        """
        end = False
        maybe_escape = False
        escape = False
        type_known = False
        maybe_text = False
        in_text = False
        depth = 0
        raw = ""
        stype = ""
        statement = ""
        text = ""

        char = None
        while char != "" and not end:
            char = self._buffer.read(1)

            if escape:
                raw += char
                escape = False

            if char == "\\" and not in_text:
                escape = True
            elif char == "\\":
                maybe_escape = True
            elif char == " " and not type_known:
                stype = raw
                if stype not in ("if", "elif", "else"):
                    raise errors.SyntaxError("Invalid if statement type")
                type_known = True
                raw = ""
            elif char == "]" and not in_text:
                maybe_text = True
            elif char == "(" and maybe_text:
                if not type_known:
                    stype = raw
                    if stype not in ("if", "elif", "else"):
                        raise errors.SyntaxError("Invalid if statement type")
                    type_known = True
                    raw = ""
                statement = raw
                raw = ""
                maybe_text = False
                in_text = True
            elif char == "(" and in_text:
                depth += 1
            elif char == ")" and in_text:
                if not maybe_escape:
                    text = raw
                    end = True
                else:
                    raw += ")"
                    maybe_escape = False
            else:
                if maybe_escape:
                    raw += "\\"
                    maybe_escape = False
                if maybe_text:
                    raw += "]"
                    maybe_text = False
                raw += char

        if stype != "else" and statement == "":
            raise errors.SyntaxError("If statement missing boolean expression")
        elif stype == "else" and statement != "":
            raise errors.SyntaxError("Else statement contains unexpected boolean expression")
        if not in_text:
            raise errors.SyntaxError("If statement missing result")
        if char == "":
            raise errors.SyntaxError("Unexpected end of expression")

        return Instruction[stype.upper()], statement, self._recurse(text)

    def _lex_exec(self):
        """
            Lex an exec statement in the current string
        :return: Result of lexing, raw string inside statement
        """
        end = False
        escape = False
        raw = ""

        char = None
        while char != "" and not end:
            char = self._buffer.read(1)

            if escape:
                raw += char
                escape = False
            elif char == "\\":
                escape = True
            elif char == "}":
                end = True
            else:
                raw += char

        return raw

    def lex_lang(self, data):
        """
            Convert a CommandLang string into a series of tokens in the form of tuple (type, *data)
        :param data: String input to the lexer
        :return: List of execution instructions
        """
        self._buffer = io.StringIO(data)
        escape = False
        raw = ""
        exec_stack = []

        char = None
        while char != "":
            char = self._buffer.read(1)

            if escape:
                raw += char
                escape = False

            if char == "\\":
                escape = True
            elif char == "[":
                if raw:
                    exec_stack.append((Instruction.RAW, raw))
                    raw = ""
                stype, statement, text = self._lex_if()
                exec_stack.append((stype, statement, text))
            elif char == "{":
                if raw:
                    exec_stack.append((Instruction.RAW, raw))
                    raw = ""
                text = self._lex_exec()
                exec_stack.append((Instruction.EXEC, text))
            elif char == "" and raw:
                exec_stack.append((Instruction.RAW, raw))
            else:
                raw += char

        return exec_stack
