"""
Implements an EYAML-capable version of YAML Path.

Copyright 2018, 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
import re
from subprocess import run, PIPE, CalledProcessError
from os import access, sep, X_OK
from shutil import which
from typing import Any, Generator, List, Optional

from ruamel.yaml.comments import CommentedSeq, CommentedMap

from yamlpath import YAMLPath
from yamlpath.common import Anchors
from yamlpath.eyaml.enums import EYAMLOutputFormats
from yamlpath.enums import YAMLValueFormats, PathSeperators
from yamlpath.eyaml.exceptions import EYAMLCommandException
from yamlpath.wrappers import ConsolePrinter
from yamlpath import Processor


class EYAMLProcessor(Processor):
    """Extend Processor to understand EYAML content."""

    def __init__(
        self, logger: ConsolePrinter, data: Any, **kwargs: Optional[str]
    ) -> None:
        """
        Instantiate an EYAMLProcessor.

        Parameters:
        1. logger (ConsolePrinter) Instance of ConsolePrinter or subclass
        2. data (Any) Parsed YAML data

        Keyword Arguments:
        * binary (str) The external eyaml command to use when performing
            data encryption or decryption; if no path is provided, the
            command will be sought on the system PATH.  Defaut="eyaml"
        * publickey (Optional[str]) Fully-qualified path to the public key
            for use with data encryption
        * privatekey (Optional[str]) Fully-qualified path to the public key
            for use with data decryption

        Returns:  N/A

        Raises:  N/A
        """
        self.eyaml: str = str(kwargs.pop("binary", "eyaml"))
        self.publickey: Optional[str] = kwargs.pop("publickey", None)
        self.privatekey: Optional[str] = kwargs.pop("privatekey", None)
        super().__init__(logger, data)

    # pylint: disable=locally-disabled,too-many-branches
    def _find_eyaml_paths(
        self, data: Any, build_path: YAMLPath
    ) -> Generator[YAMLPath, None, None]:
        """
        Find every encrypted value and report each as a YAML Path.

        Recursively generates a set of stringified YAML Paths, each entry
        leading to an EYAML value within the evaluated YAML data.

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. build_path (YAMLPath) A YAML Path under construction

        Returns:  (Generator[Path, None, None]) each YAML Path entry as they
            are discovered

        Raises:  N/A
        """
        if isinstance(data, CommentedSeq):
            for idx, ele in enumerate(data):
                node_anchor = Anchors.get_node_anchor(ele)
                if node_anchor is not None:
                    escaped_section = YAMLPath.escape_path_section(
                        node_anchor, PathSeperators.DOT)
                    tmp_path_segment = f"[&{escaped_section}]"
                else:
                    tmp_path_segment = f"[{idx}]"

                tmp_path = build_path + tmp_path_segment
                if self.is_eyaml_value(ele):
                    yield tmp_path
                else:
                    for subpath in self._find_eyaml_paths(ele, tmp_path):
                        yield subpath

        elif isinstance(data, CommentedMap):
            for key, val in data.non_merged_items():
                tmp_path = build_path + YAMLPath.escape_path_section(
                    key, PathSeperators.DOT)
                if self.is_eyaml_value(val):
                    yield tmp_path
                else:
                    for subpath in self._find_eyaml_paths(val, tmp_path):
                        yield subpath

    def find_eyaml_paths(self) -> Generator[YAMLPath, None, None]:
        """
        Find every encrypted value and reports its YAML Path.

        Parameters:  N/A

        Returns:  (Generator[Path, None, None]) each YAML Path entry as they
            are discovered

        Raises:  N/A
        """
        # Initiate the scan from the data root
        for path in self._find_eyaml_paths(self.data, YAMLPath()):
            yield path

    def decrypt_eyaml(self, value: str) -> str:
        """
        Decrypt an EYAML value.

        Parameters:
        1. value (str) The EYAML value to decrypt

        Returns:  (str) The decrypted value or the original value if it was not
            actually encrypted.

        Raises:
        - `EYAMLCommandException` when the eyaml binary cannot be utilized
        """
        if not self.is_eyaml_value(value):
            return value

        if not self._can_run_eyaml():
            raise EYAMLCommandException("No accessible eyaml command.")

        cmd: List[str] = [
            self.eyaml,
            'decrypt',
            '--quiet',
            '--stdin'
        ]
        if self.publickey:
            cmd.append(f"--pkcs7-public-key={self.publickey}")
        if self.privatekey:
            cmd.append(f"--pkcs7-private-key={self.privatekey}")

        cleanval: str = str(value).replace("\n", "").replace(" ", "").rstrip()
        bval: bytes = cleanval.encode("ascii")
        self.logger.debug(
            f"About to execute {' '.join(cmd)} against:\n{cleanval}",
            prefix="EYAMLPath::decrypt_eyaml:  "
        )

        try:
            # self.eyaml is untrusted, so shell must always be False and
            # all parameters must be supplied via a List.
            retval: str = run(
                cmd,
                stdout=PIPE,
                input=bval,
                check=True,
                shell=False
            ).stdout.decode('ascii').rstrip()
        except CalledProcessError as ex:
            raise EYAMLCommandException(
                f"The {self.eyaml} command cannot be run due to exit code:"
                f"  {ex.returncode}"
            ) from ex

        # Check for bad decryptions
        self.logger.debug(
            f"EYAMLPath::decrypt_eyaml:  Decrypted result:  {retval}"
        )
        if not retval or retval == cleanval:
            raise EYAMLCommandException(
                "Unable to decrypt value!  Please verify you are using the"
                " correct old EYAML keys and the value is not corrupt:"
                "    {cleanval}"
            )

        return retval

    def encrypt_eyaml(
        self, value: str,
        output: EYAMLOutputFormats = EYAMLOutputFormats.STRING
    ) -> str:
        """
        Encrypt a value via EYAML.

        Parameters:
        1. value (str) the value to encrypt
        2. output (EYAMLOutputFormats) the output format of the encryption

        Returns:  (str) The encrypted result or the original value if it was
            already an EYAML encryption.

        Raises:
        - `EYAMLCommandException` when the eyaml binary cannot be utilized.
        """
        if self.is_eyaml_value(value):
            return value

        if not self._can_run_eyaml():
            raise EYAMLCommandException(
                f"The eyaml binary is not executable at:  {self.eyaml}"
            )

        cmd: List[str] = [
            self.eyaml,
            'encrypt',
            '--quiet',
            '--stdin',
            f"--output={output}"
        ]
        if self.publickey:
            cmd.append(f"--pkcs7-public-key={self.publickey}")
        if self.privatekey:
            cmd.append(f"--pkcs7-private-key={self.privatekey}")

        self.logger.debug(
            f"EYAMLPath::encrypt_eyaml:  About to execute:  {' '.join(cmd)}"
        )
        bval: bytes = value.encode("ascii")

        try:
            # self.eyaml is untrusted, so shell must always be False and
            # all parameters must be supplied via a List.
            retval: str = (
                run(cmd, stdout=PIPE, input=bval, check=True, shell=False)
                .stdout
                .decode("ascii")
                .rstrip()
            )
        except CalledProcessError as ex:
            raise EYAMLCommandException(
                f"The {self.eyaml} command cannot be run due to exit code:"
                f"  {ex.returncode}"
            ) from ex

        # While exceedingly rare and difficult to test for, it is possible
        # for custom eyaml commands to produce no output.  This is a critical
        # error in every conceivable case but pycov will never get a test
        # that works multi-platform.  So, ignore covering this case.
        if not retval: # pragma: no cover
            raise EYAMLCommandException(
                f"The {self.eyaml} command was unable to encrypt your value."
                "  Please verify this process can run that command and read"
                " your EYAML keys."
            )

        if output is EYAMLOutputFormats.BLOCK:
            retval = re.sub(r" +", "", retval) + "\n"

        self.logger.debug(
            f"Encrypted result:\n{retval}",
            prefix="EYAMLPath::encrypt_eyaml:  "
        )
        return retval

    def set_eyaml_value(
        self, yaml_path: YAMLPath, value: str,
        output: EYAMLOutputFormats = EYAMLOutputFormats.STRING,
        mustexist: bool = False
    ) -> None:
        """
        Encrypt and store a value where specified via YAML Path.

        Parameters:
        1. yaml_path (Path) The YAML Path specifying which nodes are to
           receive the encrypted value
        2. value (any) The value to encrypt
        3. output (EYAMLOutputFormats) the output format of the encryption
        4. mustexist (bool) Indicates whether YAML Path must
           specify a pre-existing node

        Returns:  N/A

        Raises:
        - `YAMLPathException` when YAML Path is invalid
        """
        self.logger.verbose(
            f"Encrypting value(s) for {yaml_path} using {output} format."
        )
        encval: str = self.encrypt_eyaml(value, output)
        emit_format: YAMLValueFormats = YAMLValueFormats.FOLDED
        if output is EYAMLOutputFormats.STRING:
            emit_format = YAMLValueFormats.DEFAULT

        self.set_value(
            yaml_path,
            encval,
            mustexist=mustexist,
            value_format=emit_format
        )

    def get_eyaml_values(
        self, yaml_path: YAMLPath, mustexist: bool = False,
        default_value: str = ""
    ) -> Generator[str, None, None]:
        """
        Retrieve and decrypt all EYAML nodes identified via a YAML Path.

        Parameters:
        1. yaml_path (Path) The YAML Path specifying which nodes to decrypt
        2. mustexist (bool) Indicates whether YAML Path must specify a
           pre-existing node; when False, the node will be created when
           missing
        3. default_value (str) The default value to add to the YAML data
           when `mustexist=False` and yaml_path points to a non-existent
           node

        Returns:  (str) The decrypted value or `default_value` when YAML Path
            specifies a non-existant node

        Raises:
        - `YAMLPathException` when YAML Path is invalid
        """
        self.logger.verbose(f"Decrypting value(s) at {yaml_path}.")
        for node in self.get_nodes(yaml_path, mustexist=mustexist,
                                   default_value=default_value):
            plain_text: str = self.decrypt_eyaml(node.node)
            yield plain_text

    def _can_run_eyaml(self) -> bool:
        """
        Indicate whether this instance is capable of running the eyaml binary.

        Parameters:  N/A

        Returns:  (bool) True when the present eyaml property indicates an
            executable; False, otherwise

        Raises:  N/A
        """
        binary: Optional[str] = EYAMLProcessor.get_eyaml_executable(self.eyaml)
        if binary is None:
            return False
        self.eyaml = binary
        return True

    @staticmethod
    def get_eyaml_executable(binary: Optional[str] = "eyaml") -> Optional[str]:
        """
        Return the full executable path to an eyaml binary.

        Returns None when it cannot be found or is not executable.

        Parameters:
        1. binary (str) The executable to test; if an absolute or relative
           path is not provided, the system PATH will be searched for a
           match to test

        Returns: (str) None or the executable eyaml binary path

        Raises:  N/A
        """
        if binary is None or not binary:
            return None

        if binary.find(sep) < 0:
            binary = which(binary)
            if binary is None:
                return None
            binary = str(binary)

        if access(binary, X_OK):
            return binary
        return None

    @staticmethod
    def is_eyaml_value(value: str) -> bool:
        """
        Indicate whether a value is EYAML-encrypted.

        Parameters:
        1. value (any) The value to check

        Returns:  (bool) True when the value is encrypted; False, otherwise

        Raises:  N/A
        """
        if not isinstance(value, str):
            return False
        return value.replace("\n", "").replace(" ", "").startswith("ENC[")
