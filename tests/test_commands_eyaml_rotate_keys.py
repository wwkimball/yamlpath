import pytest

from tests.conftest import (
    create_temp_yaml_file,
    requireseyaml,
    old_eyaml_keys,
    new_eyaml_keys,
)

class Test_eyaml_rotate_keys():
    """Tests for the eyaml-rotate-keys command-line interface."""
    command = "eyaml-rotate-keys"

    def test_no_options(self, script_runner):
        result = script_runner.run(self.command)
        assert not result.success, result.stderr
        assert "usage: {}".format(self.command) in result.stderr

    def test_duplicate_keys(self, script_runner):
        bunk_key = "/does/not/exist/on-most/systems"
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(bunk_key),
            "--newpublickey={}".format(bunk_key),
            "--oldprivatekey={}".format(bunk_key),
            "--oldpublickey={}".format(bunk_key),
            bunk_key
        )
        assert not result.success, result.stderr
        assert "The new and old EYAML keys must be different." in result.stderr

    def test_bad_keys(self, script_runner):
        bunk_file = "/does/not/exist/on-most/systems"
        bunk_old_key = "/does/not/exist/on-most/systems/old"
        bunk_new_key = "/does/not/exist/on-most/systems/new"
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(bunk_new_key),
            "--newpublickey={}".format(bunk_new_key),
            "--oldprivatekey={}".format(bunk_old_key),
            "--oldpublickey={}".format(bunk_old_key),
            bunk_file
        )
        assert not result.success, result.stderr
        assert "EYAML key is not a readable file:" in result.stderr

    @requireseyaml
    def test_no_yaml_files(self, script_runner, old_eyaml_keys, new_eyaml_keys):
        bunk_file = "/does/not/exist/on-most/systems"
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[0]),
            "--newpublickey={}".format(new_eyaml_keys[1]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            bunk_file
        )
        assert not result.success, result.stderr
        assert "Not a file:" in result.stderr

    @requireseyaml
    def test_good_replace(self, script_runner, tmp_path_factory, old_eyaml_keys, new_eyaml_keys):
        content = """---
        encrypted: >
          ENC[PKCS7,MIIBiQYJKoZIhvcNAQcDoIIBejCCAXYCAQAxggEhMIIBHQIBADAFMAACAQEw
          DQYJKoZIhvcNAQEBBQAEggEArvk6OYa1gACTdrWq2SpCrtGRlc61la5AGU7L
          aLTyKfqD9vqx71RDjobfOF96No07kLsEpoAJ+LKKHNjdG6kjvpGPmttj9Dkm
          XVoU6A+YCmm4iYFKD/NkoSOEyAkoDOXSqdjrgt0f37GefEsXt6cqAavDpUJm
          pmc0KI4TCG5zpfCxqttMs+stOY3Y+0WokkulQujZ7K3SdWUSHIysgMrWiect
          Wdg5unxN1A/aeyvhgvYSNPjU9KBco7SDnigSs9InW/QghJFrZRrDhTp1oTUc
          qK5lKvaseHkVGi91vPWeLQxZt1loJB5zL6j5BxMbvRfJK+wc3ax2u4x8WTAB
          EurCwzBMBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBAwcy7jvcOGcMfLEtug
          LEXbgCBkocdckuDe14mVGmUmM++xN34OEVRCeGVWWUnWq1DJ4Q==]
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[0]),
            "--newpublickey={}".format(new_eyaml_keys[1]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert not filedat == content

    def test_yaml_parsing_error(self, script_runner, imparsible_yaml_file, old_eyaml_keys, new_eyaml_keys):
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[0]),
            "--newpublickey={}".format(new_eyaml_keys[1]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            imparsible_yaml_file
        )
        assert not result.success, result.stderr
        assert "YAML parsing error" in result.stderr

    def test_yaml_syntax_error(self, script_runner, badsyntax_yaml_file, old_eyaml_keys, new_eyaml_keys):
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[0]),
            "--newpublickey={}".format(new_eyaml_keys[1]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            badsyntax_yaml_file
        )
        assert not result.success, result.stderr
        assert "YAML syntax error" in result.stderr

    def test_yaml_composition_error(self, script_runner, badcmp_yaml_file, old_eyaml_keys, new_eyaml_keys):
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[0]),
            "--newpublickey={}".format(new_eyaml_keys[1]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            badcmp_yaml_file
        )
        assert not result.success, result.stderr
        assert "YAML composition error" in result.stderr
