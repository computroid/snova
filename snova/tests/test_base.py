# imports - standard imports
import getpass
import json
import os
import shutil
import subprocess
import sys
import traceback
import unittest

# imports - module imports
from snova.utils import paths_in_snova, exec_cmd
from snova.utils.system import init
from snova.snova import Snova

PYTHON_VER = sys.version_info

SPARROW_BRANCH = "version-13-hotfix"
if PYTHON_VER.major == 3:
	if PYTHON_VER.minor >= 10:
		SPARROW_BRANCH = "develop"


class TestSnovaBase(unittest.TestCase):
	def setUp(self):
		self.snovaes_path = "."
		self.snovaes = []

	def tearDown(self):
		for snova_name in self.snovaes:
			snova_path = os.path.join(self.snovaes_path, snova_name)
			snova = Snova(snova_path)
			mariadb_password = (
				"travis"
				if os.environ.get("CI")
				else getpass.getpass(prompt="Enter MariaDB root Password: ")
			)

			if snova.exists:
				for site in snova.sites:
					subprocess.call(
						[
							"snova",
							"drop-site",
							site,
							"--force",
							"--no-backup",
							"--root-password",
							mariadb_password,
						],
						cwd=snova_path,
					)
				shutil.rmtree(snova_path, ignore_errors=True)

	def assert_folders(self, snova_name):
		for folder in paths_in_snova:
			self.assert_exists(snova_name, folder)
		self.assert_exists(snova_name, "apps", "sparrow")

	def assert_virtual_env(self, snova_name):
		snova_path = os.path.abspath(snova_name)
		python_path = os.path.abspath(os.path.join(snova_path, "env", "bin", "python"))
		self.assertTrue(python_path.startswith(snova_path))
		for subdir in ("bin", "lib", "share"):
			self.assert_exists(snova_name, "env", subdir)

	def assert_config(self, snova_name):
		for config, search_key in (
			("redis_queue.conf", "redis_queue.rdb"),
			("redis_cache.conf", "redis_cache.rdb"),
		):

			self.assert_exists(snova_name, "config", config)

			with open(os.path.join(snova_name, "config", config)) as f:
				self.assertTrue(search_key in f.read())

	def assert_common_site_config(self, snova_name, expected_config):
		common_site_config_path = os.path.join(
			self.snovaes_path, snova_name, "sites", "common_site_config.json"
		)
		self.assertTrue(os.path.exists(common_site_config_path))

		with open(common_site_config_path) as f:
			config = json.load(f)

		for key, value in list(expected_config.items()):
			self.assertEqual(config.get(key), value)

	def assert_exists(self, *args):
		self.assertTrue(os.path.exists(os.path.join(*args)))

	def new_site(self, site_name, snova_name):
		new_site_cmd = ["snova", "new-site", site_name, "--admin-password", "admin"]

		if os.environ.get("CI"):
			new_site_cmd.extend(["--mariadb-root-password", "travis"])

		subprocess.call(new_site_cmd, cwd=os.path.join(self.snovaes_path, snova_name))

	def init_snova(self, snova_name, **kwargs):
		self.snovaes.append(snova_name)
		sparrow_tmp_path = "/tmp/sparrow"

		if not os.path.exists(sparrow_tmp_path):
			exec_cmd(
				f"git clone https://github.com/sparrow/sparrow -b {SPARROW_BRANCH} --depth 1 --origin upstream {sparrow_tmp_path}"
			)

		kwargs.update(
			dict(
				python=sys.executable,
				no_procfile=True,
				no_backups=True,
				sparrow_path=sparrow_tmp_path,
			)
		)

		if not os.path.exists(os.path.join(self.snovaes_path, snova_name)):
			init(snova_name, **kwargs)
			exec_cmd(
				"git remote set-url upstream https://github.com/sparrow/sparrow",
				cwd=os.path.join(self.snovaes_path, snova_name, "apps", "sparrow"),
			)

	def file_exists(self, path):
		if os.environ.get("CI"):
			return not subprocess.call(["sudo", "test", "-f", path])
		return os.path.isfile(path)

	def get_traceback(self):
		exc_type, exc_value, exc_tb = sys.exc_info()
		trace_list = traceback.format_exception(exc_type, exc_value, exc_tb)
		return "".join(str(t) for t in trace_list)
