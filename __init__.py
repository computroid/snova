VERSION = "5.18.0"
PROJECT_NAME = "sparrow-snova"
SPARROW_VERSION = None
current_path = None
updated_path = None
LOG_BUFFER = []


def set_sparrow_version(snova_path="."):
	from .utils.app import get_current_sparrow_version

	global SPARROW_VERSION
	if not SPARROW_VERSION:
		SPARROW_VERSION = get_current_sparrow_version(snova_path=snova_path)
