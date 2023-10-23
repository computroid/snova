# imports - standard imports
import getpass
import os

# imports - third partyimports
import click

# imports - module imports
import snova
from snova.app import use_rq
from snova.snova import Snova
from snova.config.common_site_config import (
	get_gunicorn_workers,
	update_config,
	get_default_max_requests,
	compute_max_requests_jitter,
)
from snova.utils import exec_cmd, which, get_snova_name


def generate_systemd_config(
	snova_path,
	user=None,
	yes=False,
	stop=False,
	create_symlinks=False,
	delete_symlinks=False,
):

	if not user:
		user = getpass.getuser()

	config = Snova(snova_path).conf

	snova_dir = os.path.abspath(snova_path)
	snova_name = get_snova_name(snova_path)

	if stop:
		exec_cmd(
			f"sudo systemctl stop -- $(systemctl show -p Requires {snova_name}.target | cut -d= -f2)"
		)
		return

	if create_symlinks:
		_create_symlinks(snova_path)
		return

	if delete_symlinks:
		_delete_symlinks(snova_path)
		return

	number_of_workers = config.get("background_workers") or 1
	background_workers = []
	for i in range(number_of_workers):
		background_workers.append(
			get_snova_name(snova_path) + "-sparrow-default-worker@" + str(i + 1) + ".service"
		)

	for i in range(number_of_workers):
		background_workers.append(
			get_snova_name(snova_path) + "-sparrow-short-worker@" + str(i + 1) + ".service"
		)

	for i in range(number_of_workers):
		background_workers.append(
			get_snova_name(snova_path) + "-sparrow-long-worker@" + str(i + 1) + ".service"
		)

	web_worker_count = config.get(
		"gunicorn_workers", get_gunicorn_workers()["gunicorn_workers"]
	)
	max_requests = config.get(
		"gunicorn_max_requests", get_default_max_requests(web_worker_count)
	)

	snova_info = {
		"snova_dir": snova_dir,
		"sites_dir": os.path.join(snova_dir, "sites"),
		"user": user,
		"use_rq": use_rq(snova_path),
		"http_timeout": config.get("http_timeout", 120),
		"redis_server": which("redis-server"),
		"node": which("node") or which("nodejs"),
		"redis_cache_config": os.path.join(snova_dir, "config", "redis_cache.conf"),
		"redis_queue_config": os.path.join(snova_dir, "config", "redis_queue.conf"),
		"webserver_port": config.get("webserver_port", 8000),
		"gunicorn_workers": web_worker_count,
		"gunicorn_max_requests": max_requests,
		"gunicorn_max_requests_jitter": compute_max_requests_jitter(max_requests),
		"snova_name": get_snova_name(snova_path),
		"worker_target_wants": " ".join(background_workers),
		"snova_cmd": which("snova"),
	}

	if not yes:
		click.confirm(
			"current systemd configuration will be overwritten. Do you want to continue?",
			abort=True,
		)

	setup_systemd_directory(snova_path)
	setup_main_config(snova_info, snova_path)
	setup_workers_config(snova_info, snova_path)
	setup_web_config(snova_info, snova_path)
	setup_redis_config(snova_info, snova_path)

	update_config({"restart_systemd_on_update": False}, snova_path=snova_path)
	update_config({"restart_supervisor_on_update": False}, snova_path=snova_path)


def setup_systemd_directory(snova_path):
	if not os.path.exists(os.path.join(snova_path, "config", "systemd")):
		os.makedirs(os.path.join(snova_path, "config", "systemd"))


def setup_main_config(snova_info, snova_path):
	# Main config
	snova_template = snova.config.env().get_template("systemd/sparrow-snova.target")
	snova_config = snova_template.render(**snova_info)
	snova_config_path = os.path.join(
		snova_path, "config", "systemd", snova_info.get("snova_name") + ".target"
	)

	with open(snova_config_path, "w") as f:
		f.write(snova_config)


def setup_workers_config(snova_info, snova_path):
	# Worker Group
	snova_workers_target_template = snova.config.env().get_template(
		"systemd/sparrow-snova-workers.target"
	)
	snova_default_worker_template = snova.config.env().get_template(
		"systemd/sparrow-snova-sparrow-default-worker.service"
	)
	snova_short_worker_template = snova.config.env().get_template(
		"systemd/sparrow-snova-sparrow-short-worker.service"
	)
	snova_long_worker_template = snova.config.env().get_template(
		"systemd/sparrow-snova-sparrow-long-worker.service"
	)
	snova_schedule_worker_template = snova.config.env().get_template(
		"systemd/sparrow-snova-sparrow-schedule.service"
	)

	snova_workers_target_config = snova_workers_target_template.render(**snova_info)
	snova_default_worker_config = snova_default_worker_template.render(**snova_info)
	snova_short_worker_config = snova_short_worker_template.render(**snova_info)
	snova_long_worker_config = snova_long_worker_template.render(**snova_info)
	snova_schedule_worker_config = snova_schedule_worker_template.render(**snova_info)

	snova_workers_target_config_path = os.path.join(
		snova_path, "config", "systemd", snova_info.get("snova_name") + "-workers.target"
	)
	snova_default_worker_config_path = os.path.join(
		snova_path,
		"config",
		"systemd",
		snova_info.get("snova_name") + "-sparrow-default-worker@.service",
	)
	snova_short_worker_config_path = os.path.join(
		snova_path,
		"config",
		"systemd",
		snova_info.get("snova_name") + "-sparrow-short-worker@.service",
	)
	snova_long_worker_config_path = os.path.join(
		snova_path,
		"config",
		"systemd",
		snova_info.get("snova_name") + "-sparrow-long-worker@.service",
	)
	snova_schedule_worker_config_path = os.path.join(
		snova_path,
		"config",
		"systemd",
		snova_info.get("snova_name") + "-sparrow-schedule.service",
	)

	with open(snova_workers_target_config_path, "w") as f:
		f.write(snova_workers_target_config)

	with open(snova_default_worker_config_path, "w") as f:
		f.write(snova_default_worker_config)

	with open(snova_short_worker_config_path, "w") as f:
		f.write(snova_short_worker_config)

	with open(snova_long_worker_config_path, "w") as f:
		f.write(snova_long_worker_config)

	with open(snova_schedule_worker_config_path, "w") as f:
		f.write(snova_schedule_worker_config)


def setup_web_config(snova_info, snova_path):
	# Web Group
	snova_web_target_template = snova.config.env().get_template(
		"systemd/sparrow-snova-web.target"
	)
	snova_web_service_template = snova.config.env().get_template(
		"systemd/sparrow-snova-sparrow-web.service"
	)
	snova_node_socketio_template = snova.config.env().get_template(
		"systemd/sparrow-snova-node-socketio.service"
	)

	snova_web_target_config = snova_web_target_template.render(**snova_info)
	snova_web_service_config = snova_web_service_template.render(**snova_info)
	snova_node_socketio_config = snova_node_socketio_template.render(**snova_info)

	snova_web_target_config_path = os.path.join(
		snova_path, "config", "systemd", snova_info.get("snova_name") + "-web.target"
	)
	snova_web_service_config_path = os.path.join(
		snova_path, "config", "systemd", snova_info.get("snova_name") + "-sparrow-web.service"
	)
	snova_node_socketio_config_path = os.path.join(
		snova_path,
		"config",
		"systemd",
		snova_info.get("snova_name") + "-node-socketio.service",
	)

	with open(snova_web_target_config_path, "w") as f:
		f.write(snova_web_target_config)

	with open(snova_web_service_config_path, "w") as f:
		f.write(snova_web_service_config)

	with open(snova_node_socketio_config_path, "w") as f:
		f.write(snova_node_socketio_config)


def setup_redis_config(snova_info, snova_path):
	# Redis Group
	snova_redis_target_template = snova.config.env().get_template(
		"systemd/sparrow-snova-redis.target"
	)
	snova_redis_cache_template = snova.config.env().get_template(
		"systemd/sparrow-snova-redis-cache.service"
	)
	snova_redis_queue_template = snova.config.env().get_template(
		"systemd/sparrow-snova-redis-queue.service"
	)

	snova_redis_target_config = snova_redis_target_template.render(**snova_info)
	snova_redis_cache_config = snova_redis_cache_template.render(**snova_info)
	snova_redis_queue_config = snova_redis_queue_template.render(**snova_info)

	snova_redis_target_config_path = os.path.join(
		snova_path, "config", "systemd", snova_info.get("snova_name") + "-redis.target"
	)
	snova_redis_cache_config_path = os.path.join(
		snova_path, "config", "systemd", snova_info.get("snova_name") + "-redis-cache.service"
	)
	snova_redis_queue_config_path = os.path.join(
		snova_path, "config", "systemd", snova_info.get("snova_name") + "-redis-queue.service"
	)

	with open(snova_redis_target_config_path, "w") as f:
		f.write(snova_redis_target_config)

	with open(snova_redis_cache_config_path, "w") as f:
		f.write(snova_redis_cache_config)

	with open(snova_redis_queue_config_path, "w") as f:
		f.write(snova_redis_queue_config)


def _create_symlinks(snova_path):
	snova_dir = os.path.abspath(snova_path)
	etc_systemd_system = os.path.join("/", "etc", "systemd", "system")
	config_path = os.path.join(snova_dir, "config", "systemd")
	unit_files = get_unit_files(snova_dir)
	for unit_file in unit_files:
		filename = "".join(unit_file)
		exec_cmd(
			f'sudo ln -s {config_path}/{filename} {etc_systemd_system}/{"".join(unit_file)}'
		)
	exec_cmd("sudo systemctl daemon-reload")


def _delete_symlinks(snova_path):
	snova_dir = os.path.abspath(snova_path)
	etc_systemd_system = os.path.join("/", "etc", "systemd", "system")
	unit_files = get_unit_files(snova_dir)
	for unit_file in unit_files:
		exec_cmd(f'sudo rm {etc_systemd_system}/{"".join(unit_file)}')
	exec_cmd("sudo systemctl daemon-reload")


def get_unit_files(snova_path):
	snova_name = get_snova_name(snova_path)
	unit_files = [
		[snova_name, ".target"],
		[snova_name + "-workers", ".target"],
		[snova_name + "-web", ".target"],
		[snova_name + "-redis", ".target"],
		[snova_name + "-sparrow-default-worker@", ".service"],
		[snova_name + "-sparrow-short-worker@", ".service"],
		[snova_name + "-sparrow-long-worker@", ".service"],
		[snova_name + "-sparrow-schedule", ".service"],
		[snova_name + "-sparrow-web", ".service"],
		[snova_name + "-node-socketio", ".service"],
		[snova_name + "-redis-cache", ".service"],
		[snova_name + "-redis-queue", ".service"],
	]
	return unit_files
