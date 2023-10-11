"""Module for defining commonly used types."""

import ast
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Optional, Union

from typing_extensions import TypeAlias, override

import pymend.docstring_parser as dsp

from .const import DEFAULT_DESCRIPTION, DEFAULT_SUMMARY, DEFAULT_TYPE

__author__ = "J-E. Nitschke"
__copyright__ = "Copyright 2023-2023"
__licence__ = "GPL3"
__version__ = "1.0.0"
__maintainer__ = "J-E. Nitschke"


@dataclass(frozen=True)
class FixerSettings:
    """Settings to influence which sections are required and when."""

    force_params: bool = True
    force_return: bool = True
    force_raises: bool = True
    force_methods: bool = False
    force_attributes: bool = False
    force_params_min_n_params: int = 0
    force_meta_min_func_length: int = 0
    ignore_privates: bool = True
    ignore_unused_arguments: bool = True
    ignored_decorators: list[str] = field(default_factory=lambda: ["overload"])
    ignored_functions: list[str] = field(default_factory=lambda: ["main"])
    ignored_classes: list[str] = field(default_factory=list)
    force_defaults: bool = True


@dataclass
class DocstringInfo:
    """Wrapper around raw docstring."""

    name: str
    docstring: str
    lines: tuple[int, Optional[int]]
    modifier: str
    issues: list[str]

    def output_docstring(
        self,
        *,
        settings: FixerSettings,
        output_style: dsp.DocstringStyle = dsp.DocstringStyle.NUMPYDOC,
        input_style: dsp.DocstringStyle = dsp.DocstringStyle.AUTO,
    ) -> str:
        """Parse and fix input docstrings, then compose output docstring.

        Parameters
        ----------
        settings : FixerSettings
            Settings for what to fix and when.
        output_style : dsp.DocstringStyle
            Output style to use for the docstring.
            (Default value = dsp.DocstringStyle.NUMPYDOC)
        input_style : dsp.DocstringStyle
            Input style to assume for the docstring.
            (Default value = dsp.DocstringStyle.AUTO)

        Returns
        -------
        str
            String representing the updated docstring.

        Raises
        ------
        AssertionError
            If the docstring could not be parsed.
        """
        self._escape_triple_quotes()
        try:
            parsed = dsp.parse(self.docstring, style=input_style)
        except Exception as e:  # noqa: BLE001
            msg = "Failed to parse docstring with error: {e}."
            raise AssertionError(msg) from e
        self._fix_docstring(parsed, settings)
        return dsp.compose(parsed, style=output_style)

    def report_issues(self) -> tuple[int, str]:
        """Report all issues that were found in this docstring.

        Returns
        -------
        tuple[int, str]
            The number of issues found and a string representing a summary
            of those.
        """
        if not self.issues:
            return 0, ""
        return len(self.issues), f"\n{self.name}:\n" + "\n".join(self.issues)

    def _escape_triple_quotes(self) -> None:
        r"""Escape \"\"\" in the docstring."""
        if '"""' in self.docstring:
            self.issues.append("Unescaped triple quotes found.")
            self.docstring = self.docstring.replace('"""', r"\"\"\"")

    def _fix_docstring(
        self, docstring: dsp.Docstring, _settings: FixerSettings
    ) -> None:
        """Fix docstrings.

        Default are to add missing dots, blank lines and give defaults for
        descriptions and types.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to fix.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        self._fix_backslashes()
        self._fix_short_description(docstring)
        self._fix_blank_lines(docstring)
        self._fix_descriptions(docstring)
        self._fix_types(docstring)

    def _fix_backslashes(self) -> None:
        """If there is any backslash in the docstring set it as raw."""
        if "\\" in self.docstring and "r" not in self.modifier:
            self.issues.append("Missing 'r' modifier.")
            self.modifier = "r" + self.modifier

    def _fix_short_description(self, docstring: dsp.Docstring) -> None:
        """Set default summary.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to set the default summary for.
        """
        cleaned_short_description = (
            docstring.short_description.strip() if docstring.short_description else ""
        )
        if (
            not cleaned_short_description
            or cleaned_short_description == DEFAULT_SUMMARY
        ):
            self.issues.append("Missing short description.")
        docstring.short_description = cleaned_short_description or DEFAULT_SUMMARY
        if not docstring.short_description.endswith("."):
            self.issues.append("Short description missing '.' at the end.")
            docstring.short_description = f"{docstring.short_description.rstrip()}."

    def _fix_blank_lines(self, docstring: dsp.Docstring) -> None:
        """Set blank lines after short and long description.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to fix the blank lines for.
        """
        # For parsing a blank line is associated with the description.
        if bool(docstring.blank_after_short_description) != bool(
            docstring.long_description or docstring.meta
        ):
            self.issues.append("Incorrect blank line after short description.")
        too_much = bool(
            docstring.long_description and docstring.blank_after_long_description
        ) and not bool(docstring.meta)
        missing = (
            docstring.long_description
            and not docstring.blank_after_long_description
            and docstring.meta
        )
        if too_much or missing:
            self.issues.append("Incorrect blank line after long description.")
        # Set blank line after short description if a long one follows
        # If nothing follows we do not want one and other sections bring their own.
        # For composing.
        docstring.blank_after_short_description = bool(docstring.long_description)
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
            if not ele.description or ele.description == DEFAULT_DESCRIPTION:
                self.issues.append(
                    f"Missing or default description `{ele.description}`."
                )
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
            if not param.type_name or param.type_name == DEFAULT_TYPE:
                self.issues.append(
                    f"Missing or default type name for parameter `{param.arg_name}`."
                )
            param.type_name = param.type_name or DEFAULT_TYPE
        for returned in docstring.many_returns:
            if not returned.type_name or returned.type_name == DEFAULT_TYPE:
                self.issues.append(
                    "Missing or default type name for return value: "
                    f" `{returned.return_name} |"
                    f" {returned.type_name} |"
                    f" {returned.description}`."
                )
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
            Hash value of the instance.
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
    def _fix_docstring(self, docstring: dsp.Docstring, settings: FixerSettings) -> None:
        """Fix docstrings.

        Additionally adjust attributes and methods from body.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to fix.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        super()._fix_docstring(docstring, settings)
        self._adjust_attributes(docstring, settings)
        self._adjust_methods(docstring, settings)

    def _adjust_attributes(
        self, docstring: dsp.Docstring, settings: FixerSettings
    ) -> None:
        """Overwrite or create attribute docstring entries based on body.

        Create the full list if there was no original docstring.

        Do not add additional attributes and do not create the section
        if it did not exist.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust parameters for.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        # If a docstring or the section already exists we are done.
        # We already fixed empty types and descriptions in the super call.
        if self.docstring and not settings.force_attributes:
            return
        # Build dicts for faster lookup
        atts_from_doc = {
            att.arg_name: att for att in docstring.params if att.args[0] == "attribute"
        }
        atts_from_sig = {att.arg_name: att for att in self.attributes}
        for name, att_sig in atts_from_sig.items():
            # We already updated types and descriptions in the super call.
            if name in atts_from_doc:
                continue
            self.issues.append(f"Missing attribute `{att_sig.arg_name}`.")
            docstring.meta.append(
                dsp.DocstringParam(
                    args=["attribute", att_sig.arg_name],
                    description=DEFAULT_DESCRIPTION,
                    arg_name=att_sig.arg_name,
                    type_name=DEFAULT_TYPE,
                    is_optional=False,
                    default=None,
                )
            )

    def _adjust_methods(
        self, docstring: dsp.Docstring, settings: FixerSettings
    ) -> None:
        """If a new docstring is generated add a methods section.

        Create the full list if there was no original docstring.

        Do not add additional methods and do not create the section
        if it did not exist.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust methods for.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        if self.docstring and not settings.force_methods:
            return
        # Build dicts for faster lookup
        meth_from_doc = {
            meth.arg_name: meth for meth in docstring.params if meth.args[0] == "method"
        }
        for method in self.methods:
            # We already descriptions in the super call.
            if method in meth_from_doc:
                continue
            self.issues.append(f"Missing method `{method}`.")
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
    length: int

    @override
    def _fix_docstring(self, docstring: dsp.Docstring, settings: FixerSettings) -> None:
        """Fix docstrings.

        Additionally adjust:
            parameters from function signature.
            return and yield from signature and body.
            raises from body.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to fix.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        super()._fix_docstring(docstring, settings)
        self._adjust_parameters(docstring, settings)
        self._adjust_returns(docstring, settings)
        self._adjust_yields(docstring, settings)
        self._adjust_raises(docstring, settings)

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

    def _adjust_parameters(
        self, docstring: dsp.Docstring, settings: FixerSettings
    ) -> None:
        """Overwrite or create param docstring entries based on signature.

        If an entry already exists update the type description if one exists
        in the signature. Same for the default value.

        If no entry exists then create one with name, type and default from the
        signature and place holder description.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust parameters for.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        # Build dicts for faster lookup
        params_from_doc = {param.arg_name: param for param in docstring.params}
        params_from_sig = {param.arg_name: param for param in self.signature.params}
        for name, param_sig in params_from_sig.items():
            if name in params_from_doc:
                param_doc = params_from_doc[name]
                if param_sig.type_name and param_sig.type_name != param_doc.type_name:
                    self.issues.append(
                        f"Parameter type was `{param_doc.type_name} `but signature"
                        f" has type hint `{param_sig.type_name}`."
                    )
                param_doc.type_name = param_sig.type_name or param_doc.type_name
                param_doc.is_optional = False
                if param_sig.default:
                    param_doc.default = param_sig.default
                    # param_doc.description should never be None at this point
                    # as it should have already been set by '_fix_descriptions'
                    if (
                        param_doc.description is not None
                        and "default" not in param_doc.description.lower()
                        and settings.force_defaults
                    ):
                        self.issues.append("Missing description of default value.")
                        param_doc.description += (
                            f" (Default value = "
                            f"{self._escape_default_value(param_sig.default)})"
                        )
            elif (
                settings.force_params
                and len(params_from_doc) >= settings.force_params_min_n_params
                and self.length >= settings.force_meta_min_func_length
            ):
                self.issues.append(f"Missing parameter `{name}`.")
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

    def _adjust_returns(
        self, docstring: dsp.Docstring, settings: FixerSettings
    ) -> None:
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
        settings : FixerSettings
            Settings for what to fix and when.
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
        if (
            not doc_returns
            and self.body.returns_value
            # If we do not want to force returns then only add new ones if
            # there was no docstring at all.
            and (
                settings.force_return
                and self.length >= settings.force_meta_min_func_length
                or not self.docstring
            )
        ):
            self.issues.append("Missing return value.")
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
        # yield anything then correct it with the actual return value.
        elif len(doc_returns) == 1 and not self.body.yields_value:
            doc_return = doc_returns[0]
            if sig_return and doc_return.type_name != sig_return:
                self.issues.append(
                    f"Return type was `{doc_return.type_name}` but"
                    f" signature has type hint `{sig_return}`."
                )
            doc_return.type_name = sig_return or doc_return.type_name
        # If we have multiple return values specified
        # and we have only extracted one set of return values from the body.
        # then update the multiple return values with the names from
        # the actual return values.
        elif len(doc_returns) > 1 and len(self.body.returns) == 1:
            doc_names = {returned.return_name for returned in doc_returns}
            for body_name in next(iter(self.body.returns)):
                if body_name not in doc_names:
                    self.issues.append(
                        f"Missing return value in multi return statement `{body_name}`."
                    )
                    docstring.meta.append(
                        dsp.DocstringReturns(
                            args=["returns"],
                            description=DEFAULT_DESCRIPTION,
                            type_name=DEFAULT_TYPE,
                            is_generator=False,
                            return_name=body_name,
                        )
                    )

    def _adjust_yields(self, docstring: dsp.Docstring, settings: FixerSettings) -> None:
        """See _adjust_returns.

        Only difference is that the signature return type is not added
        to the docstring since it is a bit more complicated for generators.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust yields for.
        settings : FixerSettings
            Settings for what to fix and when.
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
        if not doc_yields and self.body.yields_value and settings.force_return:
            self.issues.append("Missing yielded value.")
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
            if sig_return and doc_yields.type_name != sig_return:
                self.issues.append(
                    f"Yield type was `{doc_yields.type_name}` but"
                    f" signature has type hint `{sig_return}`."
                )
            doc_yields.type_name = sig_return or doc_yields.type_name
        elif len(doc_yields) > 1 and len(self.body.yields) == 1:
            doc_names = {yielded.yield_name for yielded in doc_yields}
            for body_name in next(iter(self.body.yields)):
                if body_name not in doc_names:
                    self.issues.append(
                        f"Missing return value in multi return statement `{body_name}`."
                    )
                    docstring.meta.append(
                        dsp.DocstringYields(
                            args=["yields"],
                            description=DEFAULT_DESCRIPTION,
                            type_name=DEFAULT_TYPE,
                            is_generator=True,
                            yield_name=body_name,
                        )
                    )

    def _adjust_raises(self, docstring: dsp.Docstring, settings: FixerSettings) -> None:
        """Adjust raises section based on parsed body.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust raises section for.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        if self.docstring and not settings.force_raises:
            return
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
            self.issues.append(f"Missing raised exception `{missing_raise}`.")
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
