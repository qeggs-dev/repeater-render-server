from enum import StrEnum

class CompressionMode(StrEnum):
    GZ = "gz"
    BZ2 = "bz2"
    XZ = "xz"
    LZMA = "lzma"
    TAR = "tar"
    TAR_GZ = "tar.gz"
    TAR_BZ2 = "tar.bz2"
    TAR_XZ = "tar.xz"
    ZIP = "zip"