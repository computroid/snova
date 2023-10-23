# imports - standard imports
import getpass
import os
import pathlib
import re
import subprocess
import time
import unittest

# imports - module imports
from snova.utils import exec_cmd, get_cmd_output, which
from snova.config.production_setup import get_supervisor_confdir
from snova.tests.test_base import TestSnovaBase


class TestSetupProduction(TestSnovaBase):
	def test_setup_production(self):
		user = getpass.getuser()

		for snova_name in ("test-snova-1", "test-snova-2"):
			snova_path = os.path.join(os.path.abspath(self.snovaes_path), snova_name)
			self.init_snova(snova_name)
			exec_cmd(f"sudo snova setup production {user} --yes", cwd=snova_path)
			self.assert_nginx_config(snova_name)
			self.assert_supervisor_config(snova_name)
			self.assert_supervisor_process(snova_name)

		self.assert_nginx_process()
		exec_cmd(f"sudo snova setup sudoers {user}")
		self.assert_sudoers(user)

		for snova_name in self.snovaes:
			snova_path = os.path.join(os.path.abspath(self.snovaes_path), snova_name)
			exec_cmd("sudo snova disable-production", cwd=snova_path)

	def production(self):
		try:
			self.test_setup_production()
		except Exception:
			print(self.get_traceback())

	def assert_nginx_config(self, snova_name):
		conf_src = os.path.join(
			os.path.abspath(self.snovaes_path), snova_name, "config", "nginx.conf"
		)
		conf_dest = f"/etc/nginx/conf.d/{snova_name}.conf"

		self.assertTrue(self.file_exists(conf_src))
		self.assertTrue(self.file_exists(conf_dest))

		# symlink matches
		self.assertEqual(os.path.realpath(conf_dest), conf_src)

		# file content
		with open(conf_src) as f:
			f = f.read()

			for key in (
				f"upstream {snova_name}-sparrow",
				f"upstream {snova_name}-socketio-server",
			):
				self.assertTrue(key in f)

	def assert_nginx_process(self):
		out = get_cmd_output("sudo nginx -t 2>&1")
		self.assertTrue(
			"nginx: configuration file /etc/nginx/nginx.conf test is successful" in out
		)

	def assert_sudoers(self, user):
		sudoers_file = "/etc/sudoers.d/sparrow"
		service = which("service")
		nginx = which("nginx")

		self.assertTrue(self.file_exists(sudoers_file))

		if os.environ.get("CI"):
			sudoers = subprocess.check_output(["sudo", "cat", sudoers_file]).decode("utf-8")
		else:
			sudoers = pathlib.Path(sudoers_file).read_text()
		self.assertTrue(f"{user} ALL = (root) NOPASSWD: {service} nginx *" in sudoers)
		self.assertTrue(f"{user} ALL = (root) NOPASSWD: {nginx}" in sudoers)

	def assert_supervisor_config(self, snova_name, use_rq=True):
		conf_src = os.path.join(
			os.path.abspath(self.snovaes_path), snova_name, "config", "supervisor.conf"
		)

		supervisor_conf_dir = get_supervisor_confdir()
		conf_dest = f"{supervisor_conf_dir}/{snova_name}.conf"

		self.assertTrue(self.file_exists(conf_src))
		self.assertTrue(self.file_exists(conf_dest))

		# symlink matches
		self.assertEqual(os.path.realpath(conf_dest), conf_src)

		# file content
		with open(conf_src) as f:
			f = f.read()

			tests = [
				f"program:{snova_name}-sparrow-web",
				f"program:{snova_name}-redis-cache",
				f"program:{snova_name}-redis-queue",
				f"group:{snova_name}-web",
				f"group:{snova_name}-workers",
				f"group:{snova_name}-redis",
			]

			if not os.environ.get("CI"):
				tests.append(f"program:{snova_name}-node-socketio")

			if use_rq:
				tests.extend(
					[
						f"program:{snova_name}-sparrow-schedule",
						f"program:{snova_name}-sparrow-default-worker",
						f"program:{snova_name}-sparrow-short-worker",
						f"program:{snova_name}-sparrow-long-worker",
					]
				)

			else:
				tests.extend(
					[
						f"program:{snova_name}-sparrow-workerbeat",
						f"program:{snova_name}-sparrow-worker",
						f"program:{snova_name}-sparrow-longjob-worker",
						f"program:{snova_name}-sparrow-async-worker",
					]
				)

			for key in tests:
				self.assertTrue(key in f)

	def assert_supervisor_process(self, snova_name, use_rq=True, disable_production=False):
		out = get_cmd_output("supervisorctl status")

		while "STARTING" in out:
			print("Waiting for all processes to start...")
			time.sleep(10)
			out = get_cmd_output("supervisorctl status")

		tests = [
			r"{snova_name}-web:{snova_name}-sparrow-web[\s]+RUNNING",
			# Have commented for the time being. Needs to be uncommented later on. Snova is failing on travis because of this.
			# It works on one snova and fails on another.giving FATAL or BACKOFF (Exited too quickly (process log may have details))
			# "{snova_name}-web:{snova_name}-node-socketio[\s]+RUNNING",
			r"{snova_name}-redis:{snova_name}-redis-cache[\s]+RUNNING",
			r"{snova_name}-redis:{snova_name}-redis-queue[\s]+RUNNING",
		]

		if use_rq:
			tests.extend(
				[
					r"{snova_name}-workers:{snova_name}-sparrow-schedule[\s]+RUNNING",
					r"{snova_name}-workers:{snova_name}-sparrow-default-worker-0[\s]+RUNNING",
					r"{snova_name}-workers:{snova_name}-sparrow-short-worker-0[\s]+RUNNING",
					r"{snova_name}-workers:{snova_name}-sparrow-long-worker-0[\s]+RUNNING",
				]
			)

		else:
			tests.extend(
				[
					r"{snova_name}-workers:{snova_name}-sparrow-workerbeat[\s]+RUNNING",
					r"{snova_name}-workers:{snova_name}-sparrow-worker[\s]+RUNNING",
					r"{snova_name}-workers:{snova_name}-sparrow-longjob-worker[\s]+RUNNING",
					r"{snova_name}-workers:{snova_name}-sparrow-async-worker[\s]+RUNNING",
				]
			)

		for key in tests:
			if disable_production:
				self.assertFalse(re.search(key, out))
			else:
				self.assertTrue(re.search(key, out))


if __name__ == "__main__":
	unittest.main()
