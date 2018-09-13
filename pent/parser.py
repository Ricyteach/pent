r"""*Mini-language parser for* ``pent``.

``pent`` Extracts Numerical Text.

**Author**
    Brian Skinn (bskinn@alum.mit.edu)

**File Created**
    8 Sep 2018

**Copyright**
    \(c) Brian Skinn 2018

**Source Repository**
    http://www.github.com/bskinn/pent

**Documentation**
    http://pent.readthedocs.io

**License**
    The MIT License; see |license_txt|_ for full license terms

**Members**

"""

import attr
import pyparsing as pp

from .enums import Number, Sign, TokenField
from .enums import Content, Quantity
from .errors import BadTokenError
from .patterns import std_wordify_open, std_wordify_close


# ## MINI-LANGUAGE PARSER DEFINITION ##

# ## HELPERS ##
group_prefix = "g"
_s_any_flag = "~"
_s_ignore = "!"
_s_no_space = "x"

_pp_no_space = pp.Optional(pp.Literal(_s_no_space)).setResultsName(
    TokenField.NoSpace
)
_pp_ignore = pp.Optional(pp.Literal(_s_ignore)).setResultsName(
    TokenField.Ignore
)
_pp_quantity = pp.Word("".join(Quantity), exact=1).setResultsName(
    TokenField.Quantity
)


# ## ARBITRARY CONTENT ##
# Tilde says anything may be here, including multiple words
# Definitely want to give the option not to capture. Might ideally
# be the default NOT to capture here...
_pp_any_flag = (
    pp.Literal(_s_any_flag).setResultsName(TokenField.Type) + _pp_ignore
)

# ## LITERAL STRING ##
# Marker for the rest of the token to be a literal string
_pp_str_flag = pp.Literal(Content.String.value).setResultsName(TokenField.Type)

# Remainder of the content after the marker, spaces included
_pp_str_value = pp.Word(pp.printables + " ").setResultsName(TokenField.Str)

# Composite pattern for a literal string
_pp_string = (
    _pp_str_flag + _pp_no_space + _pp_ignore + _pp_quantity + _pp_str_value
)

# ## NUMERICAL VALUE ##
# Initial marker for a numerical value
_pp_num_flag = pp.Literal(Content.Number.value).setResultsName(TokenField.Type)

# Marker for the sign of the value; period indicates either sign
_pp_num_sign = pp.Word("".join(Sign), exact=1).setResultsName(TokenField.Sign)

# Marker for the number type to look for
_pp_num_type = pp.Word("".join(Number), exact=1).setResultsName(
    TokenField.Number
)

# Composite pattern for a number
_pp_number = (
    _pp_num_flag
    + _pp_no_space
    + _pp_ignore
    + _pp_quantity
    + pp.Group(_pp_num_sign + _pp_num_type).setResultsName(
        TokenField.SignNumber
    )
)


# ## COMBINED TOKEN PARSER ##
_pp_token = (
    pp.StringStart()
    + (_pp_any_flag ^ _pp_string ^ _pp_number)
    + pp.StringEnd()
)

# Will (presumably) eventually need to implement preceding/following
# literal strings on the number specifications


# ## PARSER CLASS FOR EXTERNAL USE ##


@attr.s
class Parser:
    """Mini-language parser for structured numerical data."""

    @classmethod
    def convert_line(cls, line, *, capture_groups=True):
        """Convert line of tokens to regex.

        The constructed regex is required to match the entirety of a
        line of text, using lookbehind and lookahead at the
        start and end of the pattern, respectively.

        """
        import shlex

        # Parse line into tokens, and then into Tokens
        tokens = shlex.split(line)
        tokens = list(Token(_, do_capture=capture_groups) for _ in tokens)

        # Zero-length start of line (or of entire string) match
        pattern = r"(^|(?<=\n))"

        # Always have optional starting whitespace
        pattern += r"[ \t]*"

        # Must initialize
        group_id = 0

        # Initialize flag for a preceding no-space-after num token
        prior_no_space_token = False

        for i, t in enumerate(tokens):
            tok_pattern = t.pattern
            if t.needs_group_id:
                group_id += 1
                tok_pattern = tok_pattern.format(str(group_id))

            if t.is_any:
                pattern += tok_pattern
                prior_no_space_token = False

            else:
                if not prior_no_space_token:
                    tok_pattern = std_wordify_open(tok_pattern)

                if t.space_after:
                    tok_pattern = std_wordify_close(tok_pattern)
                    prior_no_space_token = False
                else:
                    prior_no_space_token = True

                pattern += tok_pattern

            # Add required space or no space, depending on
            # what the token calls for, as long as it's not
            # the last token
            if i < len(tokens) - 1 and t.space_after:
                pattern += r"[ \t]+"

        # Always put possible whitespace to the end of the line
        pattern += r"[ \t]*($|(?=\n))"

        return pattern


@attr.s
class Token:
    """Encapsulates transforming mini-language patterns tokens into regex."""

    from .patterns import number_patterns as _numpats

    #: Mini-language token string to be parsed
    token = attr.ib()

    #: Whether group capture should be added or not
    do_capture = attr.ib(default=True)

    #: Flag for whether group ID substitution needs to be done
    needs_group_id = attr.ib(default=False, init=False, repr=False)

    #: Assembled regex pattern from the token, as |str|
    @property
    def pattern(self):
        return self._pattern

    #: Flag for whether the token is an "any content" token
    @property
    def is_any(self):
        return self._pr[TokenField.Type] == Content.Any

    #: Flag for whether the token matches a literal string
    @property
    def is_str(self):
        return self._pr[TokenField.Type] == Content.String

    #: Flag for whether the token matches a number
    @property
    def is_num(self):
        return self._pr[TokenField.Type] == Content.Number

    #: Match quantity; |None| for :attr:`pent.enums.Content.Any`
    @property
    def match_quantity(self):
        if self.is_any:
            return None
        else:
            return Quantity(self._pr[TokenField.Quantity])

    #: Number format matched; |None| if token doesn't match a number
    @property
    def number(self):
        if self.is_num:
            return Number(self._pr[TokenField.SignNumber][TokenField.Number])
        else:
            return None

    #: Number sign matched; |None| if token doesn't match a number
    @property
    def sign(self):
        if self.is_num:
            return Sign(self._pr[TokenField.SignNumber][TokenField.Sign])
        else:
            return None

    #: Flag for whether space should be provided for after the match
    @property
    def space_after(self):
        if self.is_any:
            return False
        else:
            return TokenField.NoSpace not in self._pr

    #: Flag for whether result should be ignored in returned output
    @property
    def ignore(self):
        return TokenField.Ignore in self._pr

    def __attrs_post_init__(self):
        """Handle automatic creation stuff."""
        try:
            self._pr = _pp_token.parseString(self.token)
        except pp.ParseException as e:
            raise BadTokenError(self.token) from e

        if self.is_any:
            self._pattern, self.needs_group_id = self._selective_group_enclose(
                ".*?"
            )
            return

        # Only single, non-optional captures implemented for now, regardless of
        # the Quantity flag in the token
        if self.is_str:
            self._pattern = self._string_pattern(self._pr[TokenField.Str])
        elif self.is_num:
            self._pattern = self._get_number_pattern(self._pr)
        else:
            raise NotImplementedError(
                "Unknown content type somehow specified!"
            )

        self._pattern, self.needs_group_id = self._selective_group_enclose(
            self._pattern
        )

    @staticmethod
    def _string_pattern(s):
        """Create a literal string pattern from `s`."""
        pattern = ""

        for c in s:
            if c in "[\^$.|?*+(){}":
                # Must escape regex special characters
                pattern += "\\" + c
            else:
                pattern += c

        return pattern

    @classmethod
    def _get_number_pattern(cls, parse_result):
        """Return the correct number pattern given the parse result."""
        num = Number(parse_result[TokenField.SignNumber][TokenField.Number])
        sign = Sign(parse_result[TokenField.SignNumber][TokenField.Sign])

        return cls._numpats[num, sign]

    @staticmethod
    def _group_open():
        """Create the opening pattern for a named group.

        This leaves a formatting placeholder for the invoking Parser
        to inject the appropriate group ID.

        """
        return r"(?P<{0}{{0}}>".format(group_prefix)

    @staticmethod
    def _group_close():
        """Create the closing pattern for a named group."""
        return ")"

    def _selective_group_enclose(self, pat):
        """Return token pattern enclosed in group IF it should be grouped.

        FIX THIS DOCSTRING, IT'S OUT OF DATE!!!

        """
        if self.do_capture and not self.ignore:
            return (self._group_open() + pat + self._group_close(), True)
        else:
            return pat, False


if __name__ == "__main__":  # pragma: no cover
    print("Module not executable.")
