class InvalidBranchException(Exception):
	pass


class InvalidRemoteException(Exception):
	pass


class PatchError(Exception):
	pass


class CommandFailedError(Exception):
	pass


class SnovaNotFoundError(Exception):
	pass


class ValidationError(Exception):
	pass


class AppNotInstalledError(ValidationError):
	pass


class CannotUpdateReleaseSnova(ValidationError):
	pass


class FeatureDoesNotExistError(CommandFailedError):
	pass


class NotInSnovaDirectoryError(Exception):
	pass


class VersionNotFound(Exception):
	pass
