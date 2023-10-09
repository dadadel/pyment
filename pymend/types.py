"""Module for defining commonly used types."""

import ast
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Optional, Union

from typing_extensions import TypeAlias, override

import pymend.docstring_parser as dsp

from .const import DEFAULT_DESCRIPTION, DEFAULT_SUMMARY, DEFAULT_TYPE

__author__ = "J-E. Nitschke"
__copyright__ = "Copyright 2023-2023"
__licence__ = "GPL3"
__version__ = "1.0.0"
__maintainer__ = "J-E. Nitschke"


@dataclass
class DocstringInfo:
    """Wrapper around raw docstring."""

    name: str
    docstring: str
    lines: tuple[int, Optional[int]]
    modifier: str

    def output_docstring(
        self, style: dsp.DocstringStyle = dsp.DocstringStyle.NUMPYDOC
    ) -> str:
        """Parse and fix input docstrings, then compose output docstring.

        Parameters
        ----------
        style : dsp.DocstringStyle
            Output style to use for the docstring.
            (Default value = dsp.DocstringStyle.NUMPYDOC)

        Returns
        -------
        str
            String representing the updated docstring.
        """
        self._escape_triple_quotes()
        parsed = dsp.parse(self.docstring)
        self.fix_docstring(parsed)
        return dsp.compose(parsed, style=style)

    def _escape_triple_quotes(self) -> None:
        r"""Escape \"\"\" in the docstring."""
        if '"""' in self.docstring:
            self.docstring = self.docstring.replace('"""', r"\"\"\"")

    def fix_docstring(self, docstring: dsp.Docstring) -> None:
        """Fix docstrings.

        Default are to add missing dots, blank lines and give defaults for
        descriptions and types.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to fix.
        """
        self._fix_backslashes()
        self._fix_short_description(docstring)
        self._fix_blank_lines(docstring)
        self._fix_descriptions(docstring)
        self._fix_types(docstring)

    def _fix_backslashes(self) -> None:
        """If there is any backslash in the docstring set it as raw."""
        if "\\" in self.docstring and "r" not in self.modifier:
            self.modifier = "r" + self.modifier

    def _fix_short_description(self, docstring: dsp.Docstring) -> None:
        """Set default summary.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to set the default summary for.
        """
        docstring.short_description = docstring.short_description or DEFAULT_SUMMARY
        if not docstring.short_description.rstrip().endswith("."):
            docstring.short_description = f"{docstring.short_description.rstrip()}."

    def _fix_blank_lines(self, docstring: dsp.Docstring) -> None:
        """Set blank lines after short and long description.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to fix the blank lines for.
        """
        # Set blank line after short description if a long one follows
        # If nothing follows we do not want one and other sections bring their own.
        docstring.blank_after_short_description = bool(docstring.long_description)
        # Set blank line after long description of something follows
        # If there is a section after the long description then that already
        # introduces a newline. If not, we do not want one at all.
        docstring.blank_after_long_description = False

    def _fix_descriptions(self, docstring: dsp.Docstring) -> None:
        """Everything should have a description.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring whose descriptions need fixing.
        """
        for ele in docstring.meta:
            # Description works a bit different for examples.
            if isinstance(ele, dsp.DocstringExample):
                continue
            ele.description = ele.description or DEFAULT_DESCRIPTION

    def _fix_types(self, docstring: dsp.Docstring) -> None:
        """Set empty types for parameters and returns.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring whose type information needs fixing
        """
        for param in docstring.params:
            if param.args[0] == "method":
                continue
            param.type_name = param.type_name or DEFAULT_TYPE
        for returned in docstring.many_returns:
            returned.type_name = returned.type_name or DEFAULT_TYPE


@dataclass
class ModuleDocstring(DocstringInfo):
    """Information about a module."""


@dataclass
class Parameter:
    """Info for parameter from signature."""

    arg_name: str
    type_name: Optional[str] = None
    default: Optional[str] = None

    def custom_hash(self) -> int:
        """Implement custom has function for uniquefying.

        Returns
        -------
        int
            Has value of the instance.
        """
        return hash((self.arg_name, self.type_name, self.default))

    @staticmethod
    def uniquefy(lst: Iterable["Parameter"]) -> Iterator["Parameter"]:
        """Remove duplicates while keeping order.

        Parameters
        ----------
        lst : Iterable['Parameter']
            Iterable of parameters that should be uniqueified.

        Yields
        ------
        'Parameter'
            Uniqueified parameters.
        """
        seen: set[int] = set()
        for item in lst:
            if (itemhash := item.custom_hash()) not in seen:
                seen.add(itemhash)
                yield item


@dataclass
class ClassDocstring(DocstringInfo):
    """Information about a module."""

    attributes: list[Parameter]
    methods: list[str]

    @override
    def fix_docstring(self, docstring: dsp.Docstring) -> None:
        """Fix docstrings.

        Additionally adjust attributes and methods from body.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to fix.
        """
        super().fix_docstring(docstring)
        self._adjust_attributes(docstring)
        self._adjust_methods(docstring)

    def _adjust_attributes(self, docstring: dsp.Docstring) -> None:
        """Overwrite or create attribute docstring entries based on body.

        Create the full list if there was no original docstring.

        Do not add additional attributes and do not create the section
        if it did not exist.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust parameters for.
        """
        # If a docstring or the section already exists we are done.
        # We already fixed empty types and descriptions in the super call.
        if self.docstring:
            return
        for attribute in self.attributes:
            docstring.meta.append(
                dsp.DocstringParam(
                    args=["attribute", attribute.arg_name],
                    description=DEFAULT_DESCRIPTION,
                    arg_name=attribute.arg_name,
                    type_name=DEFAULT_TYPE,
                    is_optional=False,
                    default=None,
                )
            )

    def _adjust_methods(self, docstring: dsp.Docstring) -> None:
        """If a new docstring is generated add a methods section.

        Create the full list if there was no original docstring.

        Do not add additional methods and do not create the section
        if it did not exist.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust methods for.
        """
        if self.docstring:
            return
        for method in self.methods:
            docstring.meta.append(
                dsp.DocstringParam(
                    args=["method", method],
                    description=DEFAULT_DESCRIPTION,
                    arg_name=method,
                    type_name=None,
                    is_optional=False,
                    default=None,
                )
            )


@dataclass
class ReturnValue:
    """Info about return value from signature."""

    type_name: Optional[str] = None


@dataclass
class FunctionSignature:
    """Information about a function signature."""

    params: list[Parameter]
    returns: ReturnValue


@dataclass
class FunctionBody:
    """Information about a function from its body."""

    raises: list[str]
    returns: set[tuple[str, ...]]
    returns_value: bool
    yields: set[tuple[str, ...]]
    yields_value: bool


@dataclass
class FunctionDocstring(DocstringInfo):
    """Information about a function from docstring."""

    signature: FunctionSignature
    body: FunctionBody

    @override
    def fix_docstring(self, docstring: dsp.Docstring) -> None:
        """Fix docstrings.

        Additionally adjust:
            parameters from function signature.
            return and yield from signature and body.
            raises from body.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to fix.
        """
        super().fix_docstring(docstring)
        self._adjust_parameters(docstring)
        self._adjust_returns(docstring)
        self._adjust_yields(docstring)
        self._adjust_raises(docstring)

    def _escape_default_value(self, default_value: str) -> str:
        r"""Escape the default value so that the docstring remains fully valid.

        Currently only escapes triple quotes '\"\"\"'.

        Parameters
        ----------
        default_value : str
            Value to escape.

        Returns
        -------
        str
            Optionally escaped value.
        """
        if '"""' in default_value:
            if "r" not in self.modifier:
                self.modifier = "r" + self.modifier
            return default_value.replace('"""', r"\"\"\"")
        return default_value

    def _adjust_parameters(self, docstring: dsp.Docstring) -> None:
        """Overwrite or create param docstring entries based on signature.

        If an entry already exists update the type description if one exists
        in the signature. Same for the default value.

        If no entry exists then create one with name, type and default from the
        signature and place holder description.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust parameters for.
        """
        # Build dicts for faster lookup
        params_from_doc = {param.arg_name: param for param in docstring.params}
        params_from_sig = {param.arg_name: param for param in self.signature.params}
        for name, param_sig in params_from_sig.items():
            if name in params_from_doc:
                param_doc = params_from_doc[name]
                param_doc.type_name = param_sig.type_name or param_doc.type_name
                param_doc.is_optional = False
                if param_sig.default:
                    param_doc.default = param_sig.default
                    # param_doc.description should never be None at this point
                    # as it should have already been set by '_fix_descriptions'
                    if (
                        param_doc.description is not None
                        and "default" not in param_doc.description.lower()
                    ):
                        param_doc.description += (
                            f" (Default value = "
                            f"{self._escape_default_value(param_sig.default)})"
                        )
            else:
                place_holder_description = DEFAULT_DESCRIPTION
                if param_sig.default:
                    place_holder_description += (
                        f" (Default value = "
                        f"{self._escape_default_value(param_sig.default)})"
                    )
                docstring.meta.append(
                    dsp.DocstringParam(
                        args=["param", name],
                        description=place_holder_description,
                        arg_name=name,
                        type_name=param_sig.type_name or DEFAULT_TYPE,
                        is_optional=False,
                        default=param_sig.default,
                    )
                )

    def _adjust_returns(self, docstring: dsp.Docstring) -> None:
        """Overwrite or create return docstring entries based on signature.

        If no return value was parsed from the docstring:
        Add one based on the signature with a dummy description except
        if the return type was not specified or specified to be None AND there
        was an existing docstring.

        If one return value is specified overwrite the type with the signature
        if one was present there.

        If multiple were specified then leave them as is.
        They might very well be expanding on a return type like:
        Tuple[int, str, whatever]

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust return values for.
        """
        doc_returns = docstring.many_returns
        sig_return = self.signature.returns.type_name
        # If the return type is a generator extract the actual return type from that.
        if sig_return and (
            matches := (re.match(r"Generator\[(\w+), (\w+), (\w+)\]", sig_return))
        ):
            sig_return = matches[3]
        # If only one return value is specified take the type from the signature
        # as that is more likely to be correct
        if not doc_returns and self.body.returns_value:
            docstring.meta.append(
                dsp.DocstringReturns(
                    args=["returns"],
                    description=DEFAULT_DESCRIPTION,
                    type_name=sig_return or DEFAULT_TYPE,
                    is_generator=False,
                    return_name=None,
                )
            )
        # If there is only one return value specified and we do not
        # yield anything then correct correct it with the actual return value.
        elif len(doc_returns) == 1 and not self.body.yields_value:
            doc_return = doc_returns[0]
            doc_return.type_name = sig_return or doc_return.type_name
        # If we have multiple return values specified
        # and we have only extracted one set of return values from the body.
        # then update the multiple return values with the names from
        # the actual return values.
        elif len(doc_returns) > 1 and len(self.body.returns) == 1:
            doc_names = {returned.return_name for returned in doc_returns}
            for body_name in next(iter(self.body.returns)):
                if body_name not in doc_names:
                    docstring.meta.append(
                        dsp.DocstringReturns(
                            args=["returns"],
                            description=DEFAULT_DESCRIPTION,
                            type_name=DEFAULT_TYPE,
                            is_generator=False,
                            return_name=body_name,
                        )
                    )

    def _adjust_yields(self, docstring: dsp.Docstring) -> None:
        """See _adjust_returns.

        Only difference is that the signature return type is not added
        to the docstring since it is a bit more complicated for generators.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust yields for.
        """
        doc_yields = docstring.many_yields
        sig_return = self.signature.returns.type_name
        # Extract actual return type from Iterators and Generators.
        if sig_return and (
            matches := (
                re.match(r"(?:Iterable|Iterator)\[([^\]]+)\]", sig_return)
                or re.match(r"Generator\[(\w+), (\w+), (\w+)\]", sig_return)
            )
        ):
            sig_return = matches[1]
        else:
            sig_return = None
        # If only one return value is specified take the type from the signature
        # as that is more likely to be correct
        if not doc_yields and self.body.yields_value:
            docstring.meta.append(
                dsp.DocstringYields(
                    args=["yields"],
                    description=DEFAULT_DESCRIPTION,
                    type_name=sig_return or DEFAULT_TYPE,
                    is_generator=True,
                    yield_name=None,
                )
            )
        elif len(doc_yields) == 1:
            doc_yields = doc_yields[0]
            doc_yields.type_name = sig_return or doc_yields.type_name
        elif len(doc_yields) > 1 and len(self.body.yields) == 1:
            doc_names = {yielded.yield_name for yielded in doc_yields}
            for body_name in next(iter(self.body.yields)):
                if body_name not in doc_names:
                    docstring.meta.append(
                        dsp.DocstringYields(
                            args=["yields"],
                            description=DEFAULT_DESCRIPTION,
                            type_name=DEFAULT_TYPE,
                            is_generator=True,
                            yield_name=body_name,
                        )
                    )

    def _adjust_raises(self, docstring: dsp.Docstring) -> None:
        """Adjust raises section based on parsed body.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust raises section for.
        """
        # Only consider those raises that are not already raised in the body.
        # We are potentially raising the same time of exception multiple times.
        # Only remove the first of each type per one encountered in the docstring.
        raised_in_body = self.body.raises.copy()
        for raised in docstring.raises:
            if raised.type_name in raised_in_body:
                raised_in_body.remove(raised.type_name)
            # If this specific Error is not in the body but the body contains
            # unknown exceptions then remove one of those instead.
            # For example when exception stored in variable and raised later.
            # We want people to be able to specific them by name and not have
            # pyment constantly forced unnamed raises on them.
            elif "" in raised_in_body:
                raised_in_body.remove("")
        for missing_raise in raised_in_body:
            docstring.meta.append(
                dsp.DocstringRaises(
                    args=["raises", missing_raise],
                    description=DEFAULT_DESCRIPTION,
                    type_name=missing_raise,
                )
            )


ElementDocstring: TypeAlias = Union[ModuleDocstring, ClassDocstring, FunctionDocstring]
DefinitionNodes: TypeAlias = Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]
NodeOfInterest: TypeAlias = Union[DefinitionNodes, ast.Module]
