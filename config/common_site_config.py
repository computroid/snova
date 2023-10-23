# imports - standard imports
import getpass
import json
import os

default_config = {
	"restart_supervisor_on_update": False,
	"restart_systemd_on_update": False,
	"serve_default_site": True,
	"rebase_on_pull": False,
	"sparrow_user": getpass.getuser(),
	"shallow_clone": True,
	"background_workers": 1,
	"use_redis_auth": False,
	"live_reload": True,
}

DEFAULT_MAX_REQUESTS = 5000


def setup_config(snova_path):
	make_pid_folder(snova_path)
	snova_config = get_config(snova_path)
	snova_config.update(default_config)
	snova_config.update(get_gunicorn_workers())
	update_config_for_sparrow(snova_config, snova_path)

	put_config(snova_config, snova_path)


def get_config(snova_path):
	return get_common_site_config(snova_path)


def get_common_site_config(snova_path):
	config_path = get_config_path(snova_path)
	if not os.path.exists(config_path):
		return {}
	with open(config_path) as f:
		return json.load(f)


def put_config(config, snova_path="."):
	config_path = get_config_path(snova_path)
	with open(config_path, "w") as f:
		return json.dump(config, f, indent=1, sort_keys=True)


def update_config(new_config, snova_path="."):
	config = get_config(snova_path=snova_path)
	config.update(new_config)
	put_config(config, snova_path=snova_path)


def get_config_path(snova_path):
	return os.path.join(snova_path, "sites", "common_site_config.json")


def get_gunicorn_workers():
	"""This function will return the maximum workers that can be started depending upon
	number of cpu's present on the machine"""
	import multiprocessing

	return {"gunicorn_workers": multiprocessing.cpu_count() * 2 + 1}


def compute_max_requests_jitter(max_requests: int) -> int:
	return int(max_requests * 0.1)


def get_default_max_requests(worker_count: int):
	"""Get max requests and jitter config based on number of available workers."""

	if worker_count <= 1:
		# If there's only one worker then random restart can cause spikes in response times and
		# can be annoying. Hence not enabled by default.
		return 0
	return DEFAULT_MAX_REQUESTS


def update_config_for_sparrow(config, snova_path):
	ports = make_ports(snova_path)

	for key in ("redis_cache", "redis_queue", "redis_socketio"):
		if key not in config:
			config[key] = f"redis://127.0.0.1:{ports[key]}"

	for key in ("webserver_port", "socketio_port", "file_watcher_port"):
		if key not in config:
			config[key] = ports[key]


def make_ports(snova_path):
	from urllib.parse import urlparse

	snovaes_path = os.path.dirname(os.path.abspath(snova_path))

	default_ports = {
		"webserver_port": 8000,
		"socketio_port": 9000,
		"file_watcher_port": 6787,
		"redis_queue": 11000,
		"redis_socketio": 13000,
		"redis_cache": 13000,
	}

	# collect all existing ports
	existing_ports = {}
	for folder in os.listdir(snovaes_path):
		snova_path = os.path.join(snovaes_path, folder)
		if os.path.isdir(snova_path):
			snova_config = get_config(snova_path)
			for key in list(default_ports.keys()):
				value = snova_config.get(key)

				# extract port from redis url
				if value and (key in ("redis_cache", "redis_queue", "redis_socketio")):
					value = urlparse(value).port

				if value:
					existing_ports.setdefault(key, []).append(value)

	# new port value = max of existing port value + 1
	ports = {}
	for key, value in list(default_ports.items()):
		existing_value = existing_ports.get(key, [])
		if existing_value:
			value = max(existing_value) + 1

		ports[key] = value

	# Backward compatbility: always keep redis_cache and redis_socketio port same
	# Note: not required from v15
	ports["redis_socketio"] = ports["redis_cache"]

	return ports


def make_pid_folder(snova_path):
	pids_path = os.path.join(snova_path, "config", "pids")
	if not os.path.exists(pids_path):
		os.makedirs(pids_path)
