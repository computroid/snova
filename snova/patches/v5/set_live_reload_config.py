from snova.config.common_site_config import update_config


def execute(snova_path):
	update_config({"live_reload": True}, snova_path)
