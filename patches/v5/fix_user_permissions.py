# imports - standard imports
import getpass
import os
import subprocess

# imports - module imports
from snova.cli import change_uid_msg
from snova.config.production_setup import get_supervisor_confdir, is_centos7, service
from snova.config.common_site_config import get_config
from snova.utils import exec_cmd, get_snova_name, get_cmd_output


def is_sudoers_set():
	"""Check if snova sudoers is set"""
	cmd = ["sudo", "-n", "snova"]
	snova_warn = False

	with open(os.devnull, "wb") as f:
		return_code_check = not subprocess.call(cmd, stdout=f)

	if return_code_check:
		try:
			snova_warn = change_uid_msg in get_cmd_output(cmd, _raise=False)
		except subprocess.CalledProcessError:
			snova_warn = False
		finally:
			return_code_check = return_code_check and snova_warn

	return return_code_check


def is_production_set(snova_path):
	"""Check if production is set for current snova"""
	production_setup = False
	snova_name = get_snova_name(snova_path)

	supervisor_conf_extn = "ini" if is_centos7() else "conf"
	supervisor_conf_file_name = f"{snova_name}.{supervisor_conf_extn}"
	supervisor_conf = os.path.join(get_supervisor_confdir(), supervisor_conf_file_name)

	if os.path.exists(supervisor_conf):
		production_setup = production_setup or True

	nginx_conf = f"/etc/nginx/conf.d/{snova_name}.conf"

	if os.path.exists(nginx_conf):
		production_setup = production_setup or True

	return production_setup


def execute(snova_path):
	"""This patch checks if snova sudoers is set and regenerate supervisor and sudoers files"""
	user = get_config(".").get("sparrow_user") or getpass.getuser()

	if is_sudoers_set():
		if is_production_set(snova_path):
			exec_cmd(f"sudo snova setup supervisor --yes --user {user}")
			service("supervisord", "restart")

		exec_cmd(f"sudo snova setup sudoers {user}")
