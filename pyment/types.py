"""Module for defining commonly used types."""

import ast
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple, TypeAlias

import docstring_parser as dsp


@dataclass
class DocstringInfo:
    """Wrapper around raw docstring."""

    name: str
    docstring: str
    lines: Tuple[int, Optional[int]]

    def _fix_short_description(self, docstring: dsp.Docstring) -> None:
        """Set default summary."""
        docstring.short_description = docstring.short_description or "_summary_."

    def _fix_long_description(self, docstring: dsp.Docstring) -> None:
        """Add '.' to end of description if missing."""
        if (
            docstring.short_description
            and not docstring.short_description.rstrip().endswith(".")
        ):
            docstring.short_description = f"{docstring.short_description.rstrip()}."

    def _fix_blank_lines(self, docstring: dsp.Docstring) -> None:
        """Set blank lines after short and long description."""
        # Set blank line after short description if a long one follows
        # If nothing follows we do not want one and other sections bring their own.
        docstring.blank_after_short_description = bool(docstring.long_description)
        # Set blank line after long description of something follows
        # If there is a section after the long description then that already
        # introduces a newline. If not, we do not want one at all.
        docstring.blank_after_long_description = False

    def _fix_descriptions(self, docstring: dsp.Docstring) -> None:
        """Everything should have a description."""
        for ele in docstring.meta:
            ele.description = ele.description or "_description_"

    def _fix_types(self, docstring: dsp.Docstring) -> None:
        """Set empty types for parameters and returns."""
        for param in docstring.params:
            param.type_name = param.type_name or "_type_"
        for returned in docstring.many_returns:
            returned.type_name = returned.type_name or "_type_"

    def fix_docstring(self, docstring: dsp.Docstring) -> None:
        """Fix docstrings.

        Default are to add missing dots, blank lines and give defaults for
        descriptions and types.
        """
        self._fix_short_description(docstring)
        self._fix_long_description(docstring)
        self._fix_blank_lines(docstring)
        self._fix_descriptions(docstring)
        self._fix_types(docstring)

    def output_docstring(
        self, style: dsp.DocstringStyle = dsp.DocstringStyle.NUMPYDOC
    ) -> str:
        """Parse and fix input docstrings, then compose output docstring."""
        parsed = dsp.parse(self.docstring)
        self.fix_docstring(parsed)
        return dsp.compose(parsed, style)


@dataclass
class ModuleDocstring(DocstringInfo):
    """Information about a module."""


@dataclass
class ClassDocstring(DocstringInfo):
    """Information about a module."""


@dataclass
class Parameter:
    """Info for parameter from signature."""

    arg_name: str
    type_name: Optional[str]
    default: Optional[str]


@dataclass
class ReturnValue:
    """Info about return value from signature."""

    type_name: Optional[str] = None


@dataclass
class FunctionSignature:
    """Information about a function signature."""

    params: List[Parameter]
    returns: ReturnValue


@dataclass
class FunctionBody:
    """Information about a function from its body."""

    raises: List[str]
    returns: Set[Tuple[str, ...]]
    returns_value: bool
    yields: Set[Tuple[str, ...]]
    yields_value: bool


@dataclass
class FunctionDocstring(DocstringInfo):
    """Information about a function from docstring."""

    signature: FunctionSignature
    body: FunctionBody

    def _adjust_parameters(self, docstring: dsp.Docstring) -> None:
        """Overwrite or create param docstring entries based on signature.

        If an entry already exists update the type description if one exists
        in the signature. Same for the default value.

        If no entry exists then create one with name, type and default from the
        signature and place holder description.
        """
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
                            f" (Default value = {param_sig.default})"
                        )
            else:
                place_holder_description = "_description_"
                if param_sig.default:
                    place_holder_description += (
                        f" (Default value = {param_sig.default})"
                    )
                docstring.meta.append(
                    dsp.DocstringParam(
                        args=["param", name],
                        description=place_holder_description,
                        arg_name=name,
                        type_name=param_sig.type_name or "_type_",
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
        """
        doc_returns = [
            item for item in docstring.many_returns or [] if not item.is_generator
        ]
        sig_return = self.signature.returns
        # If only one return value is specified take the type from the signature
        # as that is more likely to be correct
        if not doc_returns and self.body.returns_value:
            docstring.meta.append(
                dsp.DocstringReturns(
                    args=["returns"],
                    description="_description_",
                    type_name=sig_return.type_name or "_type_",
                    is_generator=False,
                    return_name=None,
                )
            )
        elif len(doc_returns) == 1 and not self.body.yields_value:
            doc_return = doc_returns[0]
            doc_return.type_name = sig_return.type_name or doc_return.type_name
        elif len(doc_returns) > 1 and len(self.body.returns) == 1:
            doc_names = {returned.return_name for returned in doc_returns}
            for body_name in next(iter(self.body.returns)):
                if body_name not in doc_names:
                    docstring.meta.append(
                        dsp.DocstringReturns(
                            args=["returns"],
                            description="_description_",
                            type_name="_type_",
                            is_generator=False,
                            return_name=body_name,
                        )
                    )

    def _adjust_yields(self, docstring: dsp.Docstring) -> None:
        """See _adjust_returns.

        Only difference is that the signature return type is not added
        to the docstring since it is a bit more complicated for generators.
        """
        doc_yields = [
            item for item in docstring.many_returns or [] if item.is_generator
        ]
        # If only one return value is specified take the type from the signature
        # as that is more likely to be correct
        if not doc_yields and self.body.yields_value:
            docstring.meta.append(
                dsp.DocstringReturns(
                    args=["yields"],
                    description="_description_",
                    type_name="_type_",
                    is_generator=True,
                    return_name=None,
                )
            )
        elif len(doc_yields) > 1 and len(self.body.yields) == 1:
            doc_names = {yielded.return_name for yielded in doc_yields}
            for body_name in next(iter(self.body.yields)):
                if body_name not in doc_names:
                    docstring.meta.append(
                        dsp.DocstringReturns(
                            args=["yields"],
                            description="_description_",
                            type_name="_type_",
                            is_generator=True,
                            return_name=body_name,
                        )
                    )

    def _adjust_raises(self, docstring: dsp.Docstring) -> None:
        raised_in_body = self.body.raises.copy()
        for raised in docstring.raises:
            if raised.type_name in raised_in_body:
                raised_in_body.remove(raised.type_name)
        for missing_raise in raised_in_body:
            docstring.meta.append(
                dsp.DocstringRaises(
                    args=["raises", missing_raise],
                    description="_description_",
                    type_name=missing_raise,
                )
            )

    def fix_docstring(self, docstring: dsp.Docstring) -> None:
        """Fix docstrings.

        Default are to add missing dots, blank lines and give defaults for
        descriptions and types.
        """
        super().fix_docstring(docstring)
        self._adjust_parameters(docstring)
        self._adjust_returns(docstring)
        self._adjust_yields(docstring)
        self._adjust_raises(docstring)


ElementDocstring: TypeAlias = ModuleDocstring | ClassDocstring | FunctionDocstring
DefinitionNodes: TypeAlias = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
NodeOfInterest: TypeAlias = DefinitionNodes | ast.Module
