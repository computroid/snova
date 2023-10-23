# imports - third party imports
import click

# imports - module imports
from snova.utils.cli import (
	MultiCommandGroup,
	print_snova_version,
	use_experimental_feature,
	setup_verbosity,
)


@click.group(cls=MultiCommandGroup)
@click.option(
	"--version",
	is_flag=True,
	is_eager=True,
	callback=print_snova_version,
	expose_value=False,
)
@click.option(
	"--use-feature",
	is_eager=True,
	callback=use_experimental_feature,
	expose_value=False,
)
@click.option(
	"-v",
	"--verbose",
	is_flag=True,
	callback=setup_verbosity,
	expose_value=False,
)
def snova_command(snova_path="."):
	import snova

	snova.set_sparrow_version(snova_path=snova_path)


from snova.commands.make import (
	drop,
	exclude_app_for_update,
	get_app,
	include_app_for_update,
	init,
	new_app,
	pip,
	remove_app,
)

snova_command.add_command(init)
snova_command.add_command(drop)
snova_command.add_command(get_app)
snova_command.add_command(new_app)
snova_command.add_command(remove_app)
snova_command.add_command(exclude_app_for_update)
snova_command.add_command(include_app_for_update)
snova_command.add_command(pip)


from snova.commands.update import (
	retry_upgrade,
	switch_to_branch,
	switch_to_develop,
	update,
)

snova_command.add_command(update)
snova_command.add_command(retry_upgrade)
snova_command.add_command(switch_to_branch)
snova_command.add_command(switch_to_develop)


from snova.commands.utils import (
	backup_all_sites,
	snova_src,
	disable_production,
	download_translations,
	find_snovaes,
	migrate_env,
	renew_lets_encrypt,
	restart,
	set_mariadb_host,
	set_nginx_port,
	set_redis_cache_host,
	set_redis_queue_host,
	set_redis_socketio_host,
	set_ssl_certificate,
	set_ssl_certificate_key,
	set_url_root,
	start,
)

snova_command.add_command(start)
snova_command.add_command(restart)
snova_command.add_command(set_nginx_port)
snova_command.add_command(set_ssl_certificate)
snova_command.add_command(set_ssl_certificate_key)
snova_command.add_command(set_url_root)
snova_command.add_command(set_mariadb_host)
snova_command.add_command(set_redis_cache_host)
snova_command.add_command(set_redis_queue_host)
snova_command.add_command(set_redis_socketio_host)
snova_command.add_command(download_translations)
snova_command.add_command(backup_all_sites)
snova_command.add_command(renew_lets_encrypt)
snova_command.add_command(disable_production)
snova_command.add_command(snova_src)
snova_command.add_command(find_snovaes)
snova_command.add_command(migrate_env)

from snova.commands.setup import setup

snova_command.add_command(setup)


from snova.commands.config import config

snova_command.add_command(config)

from snova.commands.git import remote_reset_url, remote_set_url, remote_urls

snova_command.add_command(remote_set_url)
snova_command.add_command(remote_reset_url)
snova_command.add_command(remote_urls)

from snova.commands.install import install

snova_command.add_command(install)
