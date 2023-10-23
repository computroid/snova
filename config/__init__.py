"""Module for setting up system and respective snova configurations"""


def env():
	from jinja2 import Environment, PackageLoader

	return Environment(loader=PackageLoader("snova.config"))
