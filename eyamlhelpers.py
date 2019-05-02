#!/usr/bin/env python3
################################################################################
# Reusable EYAML helpers.
#
# Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
################################################################################
import re
from subprocess import run, PIPE, CalledProcessError
from os import access, sep, X_OK
from distutils.spawn import find_executable

from yamlhelpers import YAMLHelpers, YAMLValueFormats

class EYAMLHelpers(YAMLHelpers):
    """Collection of generally-useful EYAML helper methods."""

    def __init__(self, logger, **kwargs):
        """Init this class.

        Positional Parameters:
          1. logger (ConsoleWriter) Instance of ConsoleWriter

        Optional Keyword Parameters:
          1. eyaml (str) The eyaml executable to use
          2. publickey (str) An EYAML public key file; when used,
             privatekey must also be set
          3. privatekey (str) An EYAML private key file; when used,
             publickey must also be set

        Returns:  N/A

        Raises:  N/A
        """
        self.log = logger
        self.eyaml = kwargs.pop("eyaml", "eyaml")
        self.publickey = kwargs.pop("publickey", None)
        self.privatekey = kwargs.pop("privatekey", None)

    def find_eyaml_paths(self, data, yaml_path=None):
        """Recursively generates a set of stringified YAML Paths, each entry
        leading to an EYAML value within the evaluated YAML data.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (any) The YAML Path under construction

        Returns:  (str or None) each YAML Path entry as they are discovered

        Raises:  N/A
        """
        path = self.str_path(yaml_path)

        if isinstance(data, list):
            path += "["
            for i, e in enumerate(data):
                if hasattr(e, "anchor"):
                    tmp_path = path + "&" + e.anchor.value + "]"
                else:
                    tmp_path = path + str(i) + "]"

                if self.is_eyaml_value(e):
                    yield tmp_path

                for p in self.find_eyaml_paths(e, tmp_path):
                    yield p

        elif isinstance(data, dict):
            if 0 < len(path):
                path += "."

            for k, v in data.non_merged_items():
                tmp_path = path + str(k)
                if self.is_eyaml_value(v):
                    yield tmp_path

                for p in self.find_eyaml_paths(v, tmp_path):
                    yield p

        else:
            yield None

    def decrypt_eyaml(self, value):
        """Decrypts an EYAML value.

        Positional Parameters:
          1. value (any) The EYAML value to decrypt

        Returns:  (str) The decrypted value or the original value if it was not
        actually encrypted.

        Raises:  Nothing except when the eyaml binary cannot be utilized, an
        error message is printed and the calling program is terminated.
        """
        if not self.is_eyaml_value(value):
            return value

        if not self.can_run_eyaml():
            self.log.error("No accessible eyaml command.", 1)
            return None

        cmdstr = self.eyaml + " decrypt --quiet --stdin"
        if self.publickey:
            cmdstr += " --pkcs7-public-key=" + self.publickey
        if self.privatekey:
            cmdstr += " --pkcs7-private-key=" + self.privatekey

        cmd = cmdstr.split()
        cleanval = str(value).replace("\n", "").replace(" ", "").rstrip()
        bval = (cleanval + "\n").encode("ascii")
        self.log.debug(
            "About to execute {} against:\n{}".format(cmdstr, cleanval)
        )

        try:
            retval = run(
                cmd,
                stdout=PIPE,
                input=bval
            ).stdout.decode('ascii').rstrip()
        except FileNotFoundError:
            self.log.error(
                "The {} command could not be found.".format(self.eyaml), 2
            )
        except CalledProcessError as ex:
            self.log.error(
                "The {} command cannot be run due to exit code:  {}"
                    .format(self.eyaml, ex.returncode)
                , 1
            )

        # Check for bad decryptions
        self.log.debug("Decrypted result:  {}".format(retval))
        if 1 > len(retval) or retval == cleanval:
            self.log.warning(
                "Unable to decrypt value!  Please verify you are using the"
                + " correct old EYAML keys and the value is not corrupt:\n{}"
                    .format(cleanval)
            )
            retval = None

        return retval

    def encrypt_eyaml(self, value, output="string"):
        """Encrypts a value via EYAML.

        Positional Parameters:
          1. value (any) the value to encrypt
          2. output (string) one of "string" or "block"; "string" causes
             the EYAML representation to be one single line while
             "block" results in a folded-string variant

        Returns:  (str) The encrypted result or the original value if it was
        already an EYAML encryption.

        Raises:  Nothing except when the eyaml binary cannot be utilized, an
        error message is printed and the calling program is terminated.
        """
        if self.is_eyaml_value(value):
            return value

        if not self.can_run_eyaml():
            self.log.error(
                "The eyaml binary is not executable at {}.".format(self.eyaml)
                , 1
            )
            return None

        cmdstr = self.eyaml + " encrypt --quiet --stdin --output=" + output
        if self.publickey:
            cmdstr += " --pkcs7-public-key=" + self.publickey
        if self.privatekey:
            cmdstr += " --pkcs7-private-key=" + self.privatekey

        cmd = cmdstr.split()
        self.log.debug("About to execute:  {}".format(" ".join(cmd)))
        bval = (str(value) + "\n").encode("ascii")

        try:
            retval = (
                run(cmd, stdout=PIPE, input=bval, check=True)
                    .stdout
                    .decode('ascii')
                    .rstrip()
            )
        except FileNotFoundError:
            self.log.error(
                "The {} command could not be found.".format(self.eyaml), 2
            )
        except CalledProcessError as ex:
            self.log.error(
                "The {} command cannot be run due to exit code:  {}"
                    .format(self.eyaml, ex.returncode)
                , 1
            )

        if 1 > len(retval):
            self.log.error(
                ("The {} command was unable to encrypt your value.  Please"
                    + " verify this process can run that command and read your"
                    + " EYAML keys.").format(self.eyaml)
                , 1
            )

        if output == "block":
            retval = re.sub(r" +", "", retval) + "\n"

        self.log.debug("Encrypted result:\n{}".format(retval))
        return retval

    def set_eyaml_value(self, data, yaml_path, value,
                        output="string", mustexist=False):
        """Encrypts a value and stores the result to zero or more nodes
        specified via YAML Path.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (any) The YAML Path specifying which node to
             encrypt
          3. value (any) The value to encrypt
          4. output (string) one of "string" or "block"; "string" causes
             the EYAML representation to be one single line while
             "block" results in a folded-string variant
          5. mustexist (Boolean) Indicates whether YAML Path must
             specify a pre-existing node

        Returns:  N/A

        Raises:
            YAMLPathException when YAML Path is invalid
        """
        self.log.verbose(
            "Encrypting value(s) for {}.".format(self.str_path(yaml_path))
        )
        encval = self.encrypt_eyaml(value, output)
        emit_format = YAMLValueFormats.FOLDED
        if output == "string":
            emit_format = YAMLValueFormats.DEFAULT

        self.set_value(
            data,
            yaml_path,
            encval,
            mustexist,
            emit_format
        )

    def get_eyaml_values(self, data, yaml_path,
            mustexist=False, default_value=None
    ):
        """Retrieves and decrypts zero or more EYAML nodes from YAML data at a
        YAML Path.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (any) The YAML Path specifying which node to
             decrypt
          3. mustexist (Boolean) Indicates whether YAML Path must
             specify a pre-existing node
          4. default_value (any) The default value to add to the YAML data when
             mustexist=False and yaml_path points to a non-existent node

        Returns:  (str) The decrypted value or None when YAML Path specifies a
        non-existant node.

        Raises:
            YAMLPathException when YAML Path is invalid
        """
        self.log.verbose(
            "Decrypting value(s) at {}.".format(self.str_path(yaml_path))
        )
        for node in self.get_nodes(data, yaml_path, mustexist, default_value):
            if node is None:
                continue
            plain_text = self.decrypt_eyaml(node)
            yield plain_text

    def is_eyaml_value(self, value):
        """Indicates whether a value is EYAML-encrypted.

        Positional Parameters:
          1. value (any) The value to check

        Returns:  (Boolean) true when the value is encrypted; false, otherwise

        Raises:  N/A
        """
        if value is None:
            return False
        return str(value).replace("\n", "").replace(" ", "").startswith("ENC[")

    def can_run_eyaml(self):
        """Indicates whether this instance is capable of running the eyaml
        binary as specified via its eyaml property.

        Positional Parameters:  N/A

        Returns:  (Boolean) true when the present eyaml property indicates an
        executable; false, otherwise

        Raises:  N/A
        """
        binary = self.eyaml
        if binary is None or 1 > len(binary):
            return False

        if 0 > binary.find(sep):
            self.log.debug("Finding the real path for:  {}".format(binary))
            binary = find_executable(binary)
            if 1 > len(binary):
                return False
            self.eyaml = binary

        self.log.debug(
            "Checking whether eyaml is executable at:  {}".format(binary)
        )
        return access(binary, X_OK)
