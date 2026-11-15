class StorageError(Exception):
    pass


class InvalidFileError(StorageError):
    pass


class FileTooLargeError(StorageError):
    pass
