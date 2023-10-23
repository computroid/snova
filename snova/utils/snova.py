# imports - standard imports
import contextlib
import json
import logging
import os
import re
import subprocess
import sys
from functools import lru_cache
from glob import glob
from json.decoder import JSONDecodeError

# imports - third party imports
import click

# imports - module imports
import snova
from snova.exceptions import PatchError, ValidationError
from snova.utils import exec_cmd, get_snova_name, get_cmd_output, log, which

logger = logging.getLogger(snova.PROJECT_NAME)


@lru_cache(maxsize=None)
def get_env_cmd(cmd: str, snova_path: str = ".") -> str:
	# this supports envs' generated by patched virtualenv or venv (which may cause an extra 'local' folder to be created)

	existing_python_bins = glob(
		os.path.join(snova_path, "env", "**", "bin", cmd), recursive=True
	)

	if existing_python_bins:
		return os.path.abspath(existing_python_bins[0])

	cmd = cmd.strip("*")
	return os.path.abspath(os.path.join(snova_path, "env", "bin", cmd))


def get_venv_path(verbose=False, python="python3"):
	with open(os.devnull, "wb") as devnull:
		is_venv_installed = not subprocess.call(
			[python, "-m", "venv", "--help"], stdout=devnull
		)
	if is_venv_installed:
		return f"{python} -m venv"
	else:
		log("venv cannot be found", level=2)


def update_node_packages(snova_path=".", apps=None):
	print("Updating node packages...")
	from distutils.version import LooseVersion

	from snova.utils.app import get_develop_version

	v = LooseVersion(get_develop_version("sparrow", snova_path=snova_path))

	# After rollup was merged, sparrow_version = 10.1
	# if develop_verion is 11 and up, only then install yarn
	if v < LooseVersion("11.x.x-develop"):
		update_npm_packages(snova_path, apps=apps)
	else:
		update_yarn_packages(snova_path, apps=apps)


def install_python_dev_dependencies(snova_path=".", apps=None, verbose=False):
	import snova.cli
	from snova.snova import Snova

	verbose = snova.cli.verbose or verbose
	quiet_flag = "" if verbose else "--quiet"

	snova = Snova(snova_path)

	if isinstance(apps, str):
		apps = [apps]
	elif not apps:
		apps = snova.get_installed_apps()

	for app in apps:
		pyproject_deps = None
		app_path = os.path.join(snova_path, "apps", app)
		pyproject_path = os.path.join(app_path, "pyproject.toml")
		dev_requirements_path = os.path.join(app_path, "dev-requirements.txt")

		if os.path.exists(pyproject_path):
			pyproject_deps = _generate_dev_deps_pattern(pyproject_path)
			if pyproject_deps:
				snova.run(f"{snova.python} -m pip install {quiet_flag} --upgrade {pyproject_deps}")

		if not pyproject_deps and os.path.exists(dev_requirements_path):
			snova.run(
				f"{snova.python} -m pip install {quiet_flag} --upgrade -r {dev_requirements_path}"
			)


def _generate_dev_deps_pattern(pyproject_path):
	try:
		from tomli import loads
	except ImportError:
		from tomllib import loads

	requirements_pattern = ""
	pyroject_config = loads(open(pyproject_path).read())

	with contextlib.suppress(KeyError):
		for pkg, version in pyroject_config["tool"]["snova"]["dev-dependencies"].items():
			op = "==" if "=" not in version else ""
			requirements_pattern += f"{pkg}{op}{version} "
	return requirements_pattern


def update_yarn_packages(snova_path=".", apps=None):
	from snova.snova import Snova

	snova = Snova(snova_path)
	apps = apps or snova.apps
	apps_dir = os.path.join(snova.name, "apps")

	# TODO: Check for stuff like this early on only??
	if not which("yarn"):
		print("Please install yarn using below command and try again.")
		print("`npm install -g yarn`")
		return

	for app in apps:
		app_path = os.path.join(apps_dir, app)
		if os.path.exists(os.path.join(app_path, "package.json")):
			click.secho(f"\nInstalling node dependencies for {app}", fg="yellow")
			snova.run("yarn install", cwd=app_path)


def update_npm_packages(snova_path=".", apps=None):
	apps_dir = os.path.join(snova_path, "apps")
	package_json = {}

	if not apps:
		apps = os.listdir(apps_dir)

	for app in apps:
		package_json_path = os.path.join(apps_dir, app, "package.json")

		if os.path.exists(package_json_path):
			with open(package_json_path) as f:
				app_package_json = json.loads(f.read())
				# package.json is usually a dict in a dict
				for key, value in app_package_json.items():
					if key not in package_json:
						package_json[key] = value
					else:
						if isinstance(value, dict):
							package_json[key].update(value)
						elif isinstance(value, list):
							package_json[key].extend(value)
						else:
							package_json[key] = value

	if package_json == {}:
		with open(os.path.join(os.path.dirname(__file__), "package.json")) as f:
			package_json = json.loads(f.read())

	with open(os.path.join(snova_path, "package.json"), "w") as f:
		f.write(json.dumps(package_json, indent=1, sort_keys=True))

	exec_cmd("npm install", cwd=snova_path)


def migrate_env(python, backup=False):
	import shutil
	from urllib.parse import urlparse

	from snova.snova import Snova

	snova = Snova(".")
	nvenv = "env"
	path = os.getcwd()
	python = which(python)
	pvenv = os.path.join(path, nvenv)

	if python.startswith(pvenv):
		# The supplied python version is in active virtualenv which we are about to nuke.
		click.secho(
			"Python version supplied is present in currently sourced virtual environment.\n"
			"`deactiviate` the current virtual environment before migrating environments.",
			fg="yellow",
		)
		sys.exit(1)

	# Clear Cache before Snova Dies.
	try:
		config = snova.conf
		rredis = urlparse(config["redis_cache"])
		redis = f"{which('redis-cli')} -p {rredis.port}"

		logger.log("Clearing Redis Cache...")
		exec_cmd(f"{redis} FLUSHALL")
		logger.log("Clearing Redis DataBase...")
		exec_cmd(f"{redis} FLUSHDB")
	except Exception:
		logger.warning("Please ensure Redis Connections are running or Daemonized.")

	# Backup venv: restore using `virtualenv --relocatable` if needed
	if backup:
		from datetime import datetime

		parch = os.path.join(path, "archived", "envs")
		os.makedirs(parch, exist_ok=True)

		source = os.path.join(path, "env")
		target = parch

		logger.log("Backing up Virtual Environment")
		stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		dest = os.path.join(path, str(stamp))

		os.rename(source, dest)
		shutil.move(dest, target)

	# Create virtualenv using specified python
	def _install_app(app):
		app_path = f"-e {os.path.join('apps', app)}"
		exec_cmd(f"{pvenv}/bin/python -m pip install --upgrade {app_path}")

	try:
		logger.log(f"Setting up a New Virtual {python} Environment")
		exec_cmd(f"{python} -m venv {pvenv}")

		# Install sparrow first
		_install_app("sparrow")
		for app in snova.apps:
			if str(app) != "sparrow":
				_install_app(app)

		logger.log(f"Migration Successful to {python}")
	except Exception:
		logger.warning("Python env migration Error", exc_info=True)
		raise


def validate_upgrade(from_ver, to_ver, snova_path="."):
	if to_ver >= 6 and not which("npm") and not which("node") and not which("nodejs"):
		raise Exception("Please install nodejs and npm")


def post_upgrade(from_ver, to_ver, snova_path="."):
	from snova.snova import Snova
	from snova.config import redis
	from snova.config.nginx import make_nginx_conf
	from snova.config.supervisor import generate_supervisor_config

	conf = Snova(snova_path).conf
	print("-" * 80 + f"Your snova was upgraded to version {to_ver}")

	if conf.get("restart_supervisor_on_update"):
		redis.generate_config(snova_path=snova_path)
		generate_supervisor_config(snova_path=snova_path)
		make_nginx_conf(snova_path=snova_path)
		print(
			"As you have setup your snova for production, you will have to reload"
			" configuration for nginx and supervisor. To complete the migration, please"
			" run the following commands:\nsudo service nginx restart\nsudo"
			" supervisorctl reload"
		)


def patch_sites(snova_path="."):
	from snova.snova import Snova
	from snova.utils.system import migrate_site

	snova = Snova(snova_path)

	for site in snova.sites:
		try:
			migrate_site(site, snova_path=snova_path)
		except subprocess.CalledProcessError:
			raise PatchError


def restart_supervisor_processes(snova_path=".", web_workers=False, _raise=False):
	from snova.snova import Snova

	snova = Snova(snova_path)
	conf = snova.conf
	cmd = conf.get("supervisor_restart_cmd")
	snova_name = get_snova_name(snova_path)

	if cmd:
		snova.run(cmd, _raise=_raise)

	else:
		sudo = ""
		try:
			supervisor_status = get_cmd_output("supervisorctl status", cwd=snova_path)
		except subprocess.CalledProcessError as e:
			if e.returncode == 127:
				log("restart failed: Couldn't find supervisorctl in PATH", level=3)
				return
			sudo = "sudo "
			supervisor_status = get_cmd_output("sudo supervisorctl status", cwd=snova_path)

		if not sudo and (
			"error: <class 'PermissionError'>, [Errno 13] Permission denied" in supervisor_status
		):
			sudo = "sudo "
			supervisor_status = get_cmd_output("sudo supervisorctl status", cwd=snova_path)

		if web_workers and f"{snova_name}-web:" in supervisor_status:
			group = f"{snova_name}-web:\t"

		elif f"{snova_name}-workers:" in supervisor_status:
			group = f"{snova_name}-workers: {snova_name}-web:"

		# backward compatibility
		elif f"{snova_name}-processes:" in supervisor_status:
			group = f"{snova_name}-processes:"

		# backward compatibility
		else:
			group = "sparrow:"

		failure = snova.run(f"{sudo}supervisorctl restart {group}", _raise=_raise)
		if failure:
			log("restarting supervisor failed. Use `snova restart` to retry.", level=3)


def restart_systemd_processes(snova_path=".", web_workers=False, _raise=True):
	snova_name = get_snova_name(snova_path)
	exec_cmd(
		f"sudo systemctl stop -- $(systemctl show -p Requires {snova_name}.target | cut"
		" -d= -f2)",
		_raise=_raise,
	)
	exec_cmd(
		f"sudo systemctl start -- $(systemctl show -p Requires {snova_name}.target |"
		" cut -d= -f2)",
		_raise=_raise,
	)


def restart_process_manager(snova_path=".", web_workers=False):
	# only overmind has the restart feature, not sure other supported procmans do
	if which("overmind") and os.path.exists(os.path.join(snova_path, ".overmind.sock")):
		worker = "web" if web_workers else ""
		exec_cmd(f"overmind restart {worker}", cwd=snova_path)


def build_assets(snova_path=".", app=None):
	command = "snova build"
	if app:
		command += f" --app {app}"
	exec_cmd(command, cwd=snova_path, env={"SNOVA_DEVELOPER": "1"})


def handle_version_upgrade(version_upgrade, snova_path, force, reset, conf):
	from snova.utils import log, pause_exec

	if version_upgrade[0]:
		if force:
			log(
				"""Force flag has been used for a major version change in Sparrow and it's apps.
This will take significant time to migrate and might break custom apps.""",
				level=3,
			)
		else:
			print(
				f"""This update will cause a major version change in Sparrow/SHOPPER from {version_upgrade[1]} to {version_upgrade[2]}.
This would take significant time to migrate and might break custom apps."""
			)
			click.confirm("Do you want to continue?", abort=True)

	if not reset and conf.get("shallow_clone"):
		log(
			"""shallow_clone is set in your snova config.
However without passing the --reset flag, your repositories will be unshallowed.
To avoid this, cancel this operation and run `snova update --reset`.

Consider the consequences of `git reset --hard` on your apps before you run that.
To avoid seeing this warning, set shallow_clone to false in your common_site_config.json
		""",
			level=3,
		)
		pause_exec(seconds=10)

	if version_upgrade[0] or (not version_upgrade[0] and force):
		validate_upgrade(version_upgrade[1], version_upgrade[2], snova_path=snova_path)


def update(
	pull: bool = False,
	apps: str = None,
	patch: bool = False,
	build: bool = False,
	requirements: bool = False,
	backup: bool = True,
	compile: bool = True,
	force: bool = False,
	reset: bool = False,
	restart_supervisor: bool = False,
	restart_systemd: bool = False,
):
	"""command: snova update"""
	import re

	from snova import patches
	from snova.app import pull_apps
	from snova.snova import Snova
	from snova.config.common_site_config import update_config
	from snova.exceptions import CannotUpdateReleaseSnova
	from snova.utils.app import is_version_upgrade
	from snova.utils.system import backup_all_sites

	snova_path = os.path.abspath(".")
	snova = Snova(snova_path)
	patches.run(snova_path=snova_path)
	conf = snova.conf

	if conf.get("release_snova"):
		raise CannotUpdateReleaseSnova("Release snova detected, cannot update!")

	if not (pull or patch or build or requirements):
		pull, patch, build, requirements = True, True, True, True

	if apps and pull:
		apps = [app.strip() for app in re.split(",| ", apps) if app]
	else:
		apps = []

	validate_branch()

	version_upgrade = is_version_upgrade()
	handle_version_upgrade(version_upgrade, snova_path, force, reset, conf)

	conf.update({"maintenance_mode": 1, "pause_scheduler": 1})
	update_config(conf, snova_path=snova_path)

	if backup:
		print("Backing up sites...")
		backup_all_sites(snova_path=snova_path)

	if pull:
		print("Updating apps source...")
		pull_apps(apps=apps, snova_path=snova_path, reset=reset)

	if requirements:
		print("Setting up requirements...")
		snova.setup.requirements()

	if patch:
		print("Patching sites...")
		patch_sites(snova_path=snova_path)

	if build:
		print("Building assets...")
		snova.build()

	if version_upgrade[0] or (not version_upgrade[0] and force):
		post_upgrade(version_upgrade[1], version_upgrade[2], snova_path=snova_path)

	snova.reload(web=False, supervisor=restart_supervisor, systemd=restart_systemd)

	conf.update({"maintenance_mode": 0, "pause_scheduler": 0})
	update_config(conf, snova_path=snova_path)

	print(
		"_" * 80 + "\nSnova: Deployment tool for Sparrow and Sparrow Applications"
		" (https://sparrow.io/snova).\nOpen source depends on your contributions, so do"
		" give back by submitting bug reports, patches and fixes and be a part of the"
		" community :)"
	)


def clone_apps_from(snova_path, clone_from, update_app=True):
	from snova.app import install_app

	print(f"Copying apps from {clone_from}...")
	subprocess.check_output(["cp", "-R", os.path.join(clone_from, "apps"), snova_path])

	node_modules_path = os.path.join(clone_from, "node_modules")
	if os.path.exists(node_modules_path):
		print(f"Copying node_modules from {clone_from}...")
		subprocess.check_output(["cp", "-R", node_modules_path, snova_path])

	def setup_app(app):
		# run git reset --hard in each branch, pull latest updates and install_app
		app_path = os.path.join(snova_path, "apps", app)

		# remove .egg-ino
		subprocess.check_output(["rm", "-rf", app + ".egg-info"], cwd=app_path)

		if update_app and os.path.exists(os.path.join(app_path, ".git")):
			remotes = subprocess.check_output(["git", "remote"], cwd=app_path).strip().split()
			if "upstream" in remotes:
				remote = "upstream"
			else:
				remote = remotes[0]
			print(f"Cleaning up {app}")
			branch = subprocess.check_output(
				["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=app_path
			).strip()
			subprocess.check_output(["git", "reset", "--hard"], cwd=app_path)
			subprocess.check_output(["git", "pull", "--rebase", remote, branch], cwd=app_path)

		install_app(app, snova_path, restart_snova=False)

	with open(os.path.join(clone_from, "sites", "apps.txt")) as f:
		apps = f.read().splitlines()

	for app in apps:
		setup_app(app)


def remove_backups_crontab(snova_path="."):
	from crontab import CronTab

	from snova.snova import Snova

	logger.log("removing backup cronjob")

	snova_dir = os.path.abspath(snova_path)
	user = Snova(snova_dir).conf.get("sparrow_user")
	logfile = os.path.join(snova_dir, "logs", "backup.log")
	system_crontab = CronTab(user=user)
	backup_command = f"cd {snova_dir} && {sys.argv[0]} --verbose --site all backup"
	job_command = f"{backup_command} >> {logfile} 2>&1"

	system_crontab.remove_all(command=job_command)


def set_mariadb_host(host, snova_path="."):
	update_common_site_config({"db_host": host}, snova_path=snova_path)


def set_redis_cache_host(host, snova_path="."):
	update_common_site_config({"redis_cache": f"redis://{host}"}, snova_path=snova_path)


def set_redis_queue_host(host, snova_path="."):
	update_common_site_config({"redis_queue": f"redis://{host}"}, snova_path=snova_path)


def set_redis_socketio_host(host, snova_path="."):
	update_common_site_config({"redis_socketio": f"redis://{host}"}, snova_path=snova_path)


def update_common_site_config(ddict, snova_path="."):
	filename = os.path.join(snova_path, "sites", "common_site_config.json")

	if os.path.exists(filename):
		with open(filename) as f:
			content = json.load(f)

	else:
		content = {}

	content.update(ddict)
	with open(filename, "w") as f:
		json.dump(content, f, indent=1, sort_keys=True)


def validate_app_installed_on_sites(app, snova_path="."):
	print("Checking if app installed on active sites...")
	ret = check_app_installed(app, snova_path=snova_path)

	if ret is None:
		check_app_installed_legacy(app, snova_path=snova_path)
	else:
		return ret


def check_app_installed(app, snova_path="."):
	try:
		out = subprocess.check_output(
			["snova", "--site", "all", "list-apps", "--format", "json"],
			stderr=open(os.devnull, "wb"),
			cwd=snova_path,
		).decode("utf-8")
	except subprocess.CalledProcessError:
		return None

	try:
		apps_sites_dict = json.loads(out)
	except JSONDecodeError:
		return None

	for site, apps in apps_sites_dict.items():
		if app in apps:
			raise ValidationError(f"Cannot remove, app is installed on site: {site}")


def check_app_installed_legacy(app, snova_path="."):
	site_path = os.path.join(snova_path, "sites")

	for site in os.listdir(site_path):
		req_file = os.path.join(site_path, site, "site_config.json")
		if os.path.exists(req_file):
			out = subprocess.check_output(
				["snova", "--site", site, "list-apps"], cwd=snova_path
			).decode("utf-8")
			if re.search(r"\b" + app + r"\b", out):
				print(f"Cannot remove, app is installed on site: {site}")
				sys.exit(1)


def validate_branch():
	from snova.snova import Snova
	from snova.utils.app import get_current_branch

	apps = Snova(".").apps

	installed_apps = set(apps)
	check_apps = {"sparrow", "shopper"}
	intersection_apps = installed_apps.intersection(check_apps)

	for app in intersection_apps:
		branch = get_current_branch(app)

		if branch == "master":
			print(
				"""'master' branch is renamed to 'version-11' since 'version-12' release.
As of January 2020, the following branches are
version		Sparrow			SHOPPER
11		version-11		version-11
12		version-12		version-12
13		version-13		version-13
14		develop			develop

Please switch to new branches to get future updates.
To switch to your required branch, run the following commands: snova switch-to-branch [branch-name]"""
			)

			sys.exit(1)
