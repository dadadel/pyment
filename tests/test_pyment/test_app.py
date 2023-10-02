"""Integration tests of pyment app."""

import os
import re
import subprocess
import sys
import tempfile
import textwrap
from typing import Optional, Pattern, Tuple, Union

import pyment.pyment


class TestApp:
    """Test pyment as an app in a shell.

    It's an integration test.
    """

    def setup_class(self) -> None:
        """Set up class by defining docstrings."""
        # You have to run this as a module when testing so the relative imports work.
        self.CMD_PREFIX = sys.executable + " -m pyment.pymentapp {}"

        self.RE_TYPE = type(re.compile("get the type to test if an argument is an re"))

        # cwd to use when running subprocess.
        # It has to be at the repo directory so python -m can be used
        self.CWD = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        self.INPUT = textwrap.dedent(
            '''

            def func():
                """First line

                :returns: smthg

                :rtype: ret type

                """
                pass
        '''
        )

        # Expected output in overwrite mode.
        self.EXPECTED_OUTPUT = textwrap.dedent(
            '''\
            """_summary_."""

            def func():
                """First line.

                Returns
                -------
                ret type
                    smthg
                """
                pass
        '''
        )

        self.PATCH_PREFIX = f"# Patch generated by Pyment v{pyment.pyment.__version__}"

        # a/- and b/- is replaced by a filename when not testing stdin/stdout
        self.EXPECTED_PATCH = textwrap.dedent(
            f'''\
            {self.PATCH_PREFIX}

            --- a/-
            +++ b/-
            @@ -1,11 +1,12 @@
            +"""_summary_."""

             def func():
            -    """First line
            +    """First line.

            -    :returns: smthg
            -
            -    :rtype: ret type
            -
            +    Returns
            +    -------
            +    ret type
            +        smthg
                 """
                 pass

        '''
        )

    @classmethod
    def normalise_empty_lines(cls, lines: str) -> str:
        r"""Replace any lines that are only whitespace with a single '\n'.

        textwrap.dedent removes all whitespace characters
        on lines only containing whitespaces
        see: https://bugs.python.org/issue30754

        And some people set their editors to strip trailing white space.

        But sometimes there is a space on an empty line in the
        output which will fail the comparison.

        So strip the spaces on empty lines

        Parameters
        ----------
        lines : str
            string of lines to normalise

        Returns
        -------
        str
            normalised lines
        """
        return re.sub(r"^\s+$", "", lines, flags=re.MULTILINE)

    def run_command(
        self, cmd_to_run: str, write_to_stdin: Optional[str] = None
    ) -> Tuple[str, str, int]:
        r"""Run a command in shell mode returning stdout, stderr and the returncode.

        Parameters
        ----------
        cmd_to_run : str
            shell command to run
        write_to_stdin : str | None
            string to put on stdin if not None (Default value = None)

        Returns
        -------
        tuple[str, str, int]
            stdout, stderr, returncode
        """
        process = subprocess.Popen(
            cmd_to_run,
            shell=True,  # noqa: S602
            cwd=self.CWD,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if write_to_stdin:
            # Python3 compatibility - input has to be bytes
            write_to_stdin = write_to_stdin.encode()
        stdout, stderr = process.communicate(write_to_stdin)

        stdout = stdout.decode()
        stderr = stderr.decode()
        return stdout, stderr, process.returncode

    def run_pyment_app_and_assert_is_expected(
        self,
        cmd_args: str,
        write_to_stdin: Optional[str] = None,
        expected_stdout: Union[str, Pattern[str]] = "",
        expected_stderr: Union[str, Pattern[str]] = "",
        expected_returncode: int = 0,
    ) -> None:
        """Run pyment and assert it's output matches the arguments.

        With the cmd_args and output_format specified in a shell.

        If expected_stdout and expected_stderr is the result of a re.compile()
        the output will be checked with re.search().

        Parameters
        ----------
        cmd_args : str
            Extra arguments to pass to pyment - excluding the output_format
        write_to_stdin : Optional[str]
            The input to put on stdin,
            use None if there's nothing (Default value = None)
        expected_stdout : str | Pattern[str]
            Expected string to see on stdout (Default value = "")
        expected_stderr : str | Pattern[str]
            Expected string to see on stderr (Default value = "")
        expected_returncode : int
            Expected returncode after running pyment (Default value = 0)

        Raises
        ------
        AssertionError
            If the expected result is not found
        """

        def assert_output(
            cmd_to_run: str, what: str, got: str, expected: Union[str, Pattern[str]]
        ) -> None:
            """See run_pyment_app_and_assert_is_expected.

            Parameters
            ----------
            cmd_to_run : str
                full command that was run - used to build an error message
            what : str
                The attribute being checked - used for the error message
            got : str
                The result from the test
            expected : Union[str, Pattern[str]]
                The expected result from the test

            Raises
            ------
            AssertionError
                If the expected result is not found
            """
            if isinstance(expected, self.RE_TYPE):
                msg = (
                    f"Test failed for cmd {cmd_to_run}\n{what} was "
                    f"expected to match the regex:\n{expected}\n"
                    f"But this was the output:\n{got!r}\n"
                )
                assert expected.search(got) is not None, msg
            else:
                if isinstance(expected, str):
                    # Turn lines that only have whitespace into
                    # single newline lines to workaround textwrap.dedent
                    # behaviour
                    got = self.normalise_empty_lines(got).replace("\r\n", "\n")
                    expected = self.normalise_empty_lines(expected)
                # repr is used instead of str to make it easier
                # to see newlines and spaces if there's a difference
                msg = (
                    f"Test failed for cmd {cmd_to_run}\n{what} was expected to be:"
                    f"\n{expected!r}\nBut this was the output:\n{got!r}\n"
                )
                assert got == expected, msg

        cmd_to_run = self.CMD_PREFIX.format(cmd_args)

        stdout, stderr, returncode = self.run_command(cmd_to_run, write_to_stdin)

        assert_output(cmd_to_run, "stderr", stderr, expected_stderr)
        assert_output(cmd_to_run, "returncode", returncode, expected_returncode)
        assert_output(cmd_to_run, "stdout", stdout, expected_stdout)

    def test_no_args_ge_py33(self) -> None:
        """Ensure the app outputs an error if there are no arguments."""
        self.run_pyment_app_and_assert_is_expected(
            cmd_args="",
            write_to_stdin=None,
            expected_stderr=re.compile(
                r"usage: pymentapp.py .*"
                r"pymentapp\.py: error: the following arguments are required: path",
                re.DOTALL,
            ),
            expected_returncode=2,
        )

    def test_stdin_patch_mode(self) -> None:
        """Test non overwrite mode when using stdin.

        Means a patch will be written to stdout.
        """
        self.run_pyment_app_and_assert_is_expected(
            cmd_args="--output numpydoc -",
            write_to_stdin=self.INPUT,
            expected_stdout=self.EXPECTED_PATCH,
        )

    def test_run_on_stdin_overwrite(self) -> None:
        """Check 'overwrite' mode with stdin.

        In overwrite mode the output is the new file, not a patch.
        """
        self.run_pyment_app_and_assert_is_expected(
            cmd_args="-w -",
            write_to_stdin=self.INPUT,
            expected_stdout=self.EXPECTED_OUTPUT,
        )

    def run_pyment_app_with_a_file_and_assert_is_expected(
        self,
        file_contents: str,
        cmd_args: str = "",
        *,
        overwrite_mode: bool = False,
        expected_file_contents: Union[str, Pattern[str]] = "",
        expected_stderr: Union[str, Pattern[str]] = "",
        expected_stdout: Union[str, Pattern[str]] = "",
        expected_returncode: int = 0,
    ) -> None:
        """
        Run the pyment app with a file - not stdin.

        A temporary file is created,
        file_contents is written into it then the test is run.
        The .patch and temporary files are removed at the end of the test.

        Parameters
        ----------
        file_contents : str
            write this into the temporary file
        cmd_args : str
            Arguments to pyment - do not put the '-w' argument here -
            it is triggered by overwrite_mode (Default value = "")
        overwrite_mode : bool
            set to True if in overwrite mode (Default value = False)
        expected_file_contents : str | Pattern[str]
            expected result - for a patch file ensure the filename is '-'.
            The '-' (Default value = "")
        expected_stderr : str | Pattern[str]
            expected output on stderr.
            You can match on a regex if you pass it the result of (Default value = "")
        expected_stdout : str | Pattern[str]
            Expected string to see on stdout (Default value = "")
        expected_returncode : int
            Expected return code from pyment. Default is 0.
        output_format : Optional[str]
            If not using auto mode set the output format to this. (Default value = None)
        """
        patch_filename = input_filename = ""
        input_file = None

        try:
            # Create the input file
            input_fd, input_filename = tempfile.mkstemp(suffix=".input", text=True)
            input_file = os.fdopen(input_fd, "w")
            input_file.write(file_contents)
            input_file.close()

            # Get the patch file name so it can be removed if it's created.
            # pyment will create it in the current working directory
            patch_filename = os.path.join(
                self.CWD, f"{os.path.basename(input_filename)}.patch"
            )

            cmd_args = f"{cmd_args} {input_filename}"

            if overwrite_mode:
                cmd_args = f"{cmd_args} -w "

            self.run_pyment_app_and_assert_is_expected(
                cmd_args=cmd_args,
                expected_stderr=expected_stderr,
                expected_returncode=expected_returncode,
                expected_stdout=expected_stdout,
                write_to_stdin=file_contents,
            )

            if overwrite_mode:
                with open(input_filename, encoding="utf-8") as file:
                    output = file.read()
            else:
                with open(patch_filename, encoding="utf-8") as file:
                    output = file.read()
                # The expected output will have filenames of '-'
                # - replace them with the actual filename
                output = re.sub(
                    rf"/{os.path.basename(input_filename)}$",
                    r"/-",
                    output,
                    flags=re.MULTILINE,
                )

            normalised_output = self.normalise_empty_lines(output)
            normalised_expected_output = self.normalise_empty_lines(
                expected_file_contents
            )

            assert normalised_output == normalised_expected_output, (
                f"Output from cmd: {cmd_args} was:\n{normalised_output!r}\nnot "
                f"the expected:\n{normalised_expected_output!r}"
            )

        finally:
            if input_filename:
                if input_file and not input_file.closed:
                    input_file.close()
                os.remove(input_filename)

            if not overwrite_mode and os.path.isfile(patch_filename):
                os.remove(patch_filename)

    def test_overwrite_files_the_same(self) -> None:
        """Test that the file is correct when the output is the same as the input."""
        self.run_pyment_app_with_a_file_and_assert_is_expected(
            file_contents=self.EXPECTED_OUTPUT,
            expected_file_contents=self.EXPECTED_OUTPUT,
            overwrite_mode=True,
        )

    def test_overwrite_files_different(self) -> None:
        """Test the file is overwritten with the correct result."""
        self.run_pyment_app_with_a_file_and_assert_is_expected(
            file_contents=self.INPUT,
            expected_file_contents=self.EXPECTED_OUTPUT,
            expected_stdout=re.compile(
                r"Modified docstrings of elements \(Module, func\) in file.*", re.DOTALL
            ),
            overwrite_mode=True,
        )

    def test_patch_files_the_same(self) -> None:
        """Check the patch file created when the files are the same."""
        self.run_pyment_app_with_a_file_and_assert_is_expected(
            file_contents=self.EXPECTED_OUTPUT,
            expected_file_contents=self.PATCH_PREFIX + "\n",
        )

    def test_patch_files_different(self) -> None:
        """Test the patch file is correct."""
        self.run_pyment_app_with_a_file_and_assert_is_expected(
            file_contents=self.INPUT,
            expected_file_contents=self.EXPECTED_PATCH,
        )
