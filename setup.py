from setuptools import setup

setup(name="yamltools",
      version="1.0.0",
      description="Generally-useful YAML and EYAML tools that implement YAML Path",
      long_description="This project presents and utilizes YAML Paths, which are a human-friendly means of expressing a path through the structure of YAML data to a specific key or a set of keys matching some search criteria.",
	  classifiers=[
		"Development Status :: 3 - Alpha",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
      ],
	  url="https://github.com/wwkimball/yaml-tools",
      author="William W. Kimball, Jr., MBA, MSIS",
      author_email="github-yaml-tools@kimballstuff.com",
      license="ISC",
      keywords="yaml eyaml",
      packages=["yamltools"],
      install_requires=[
          "ruamel.yaml",
      ],
      include_package_data=True,
      zip_safe=False)
