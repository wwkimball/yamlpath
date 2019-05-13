"""Express an issue with a YAML Path.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""


class YAMLPathException(Exception):
    """Occurs when a YAML Path is illegal or fails to lead to a YAML node."""

    def __init__(self, user_message, yaml_path, segment=None):
        self.user_message = user_message
        self.yaml_path = str(yaml_path)
        self.segment = str(segment) if segment is not None else None

        super(YAMLPathException, self).__init__(
            "user_message: {}, yaml_path: {}, segment: {}"
            .format(user_message, yaml_path, segment)
        )

    # Should Pickling ever be necessary:
    # def __reduce__(self):
    #     return YAMLPathException, (
    #         self.user_message,
    #         self.yaml_path,
    #         self.segment
    #     )

    def __str__(self):
        message = ""
        if self.segment is None:
            message = "{} in {}".format(
                self.user_message,
                self.yaml_path
            )
        else:
            message = "{} at {} in {}".format(
                self.user_message,
                self.segment,
                self.yaml_path
            )
        return message
