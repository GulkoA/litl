import os, struct
import zstd
import io
import importlib
import pydantic
from tqdm import tqdm
import hashlib

from .blobs import Blob

class LitlMeta(pydantic.BaseModel):
    litl_version: str
    compressor_id: str
    compressor_version: str
    compressor_meta: dict

    def serialize_value(self) -> str:
        """
        Serialize the metadata to a string
        """
        return str(list(self.model_dump().values()))
    
    @classmethod
    def deserialize_value(cls, value: str) -> 'LitlMeta':
        """
        Deserialize the metadata from a string
        """
        values_list = eval(value)
        json = dict(zip(cls.model_fields.keys(), values_list))
        return cls(**json)

class DotLitl:
    """
    A class to save and read .litl files
    """
    version = 1

    @classmethod
    def zstd_compress_bytes(cls, data: bytes) -> bytes:
        """
        Compress the data using Zstandard
        """
        level = 3
        compressed = zstd.compress(data, level)
        return compressed
    
    @classmethod
    def zstd_decompress_bytes(cls, data: bytes) -> bytes:
        """
        Decompress the data using Zstandard
        """
        return zstd.decompress(data)
    

    @classmethod
    def make_meta(cls, meta: dict, compressor_id: str, compressor_version: str) -> str:
        """
        Create a metadata dictionary
        """
        litl_version = importlib.metadata.version("litl")
        
        meta = LitlMeta(
            litl_version=litl_version,
            compressor_id=compressor_id,
            compressor_version=compressor_version,
            compressor_meta=meta
        ).serialize_value()
        return meta
    
    @classmethod
    def checksum(cls, blob_bytes: bytes, meta_bytes: bytes) -> int:
        """
        Calculate a checksum for the data
        """
        hasher = hashlib.sha256(usedforsecurity=False)
        hasher.update(blob_bytes)
        hasher.update(meta_bytes)
        checksum = hasher.digest()[:4]
        return int.from_bytes(checksum, byteorder="little")

    @classmethod
    def save(cls, path: str, blob_bytes: bytes, meta: dict, compressor_name: str, compressor_version: str) -> None:
        """
        Save the blob to a .litl file

        Byte structure is as follows:
        - 4 bytes: magic number (LITL)
        - 1 byte: version
        - 1 byte: checksum
        - 4 bytes: length of meta
        - meta: metadata (as bytes)
        - blob: blob data (as bytes)
        """
        meta_bytes = cls.zstd_compress_bytes(cls.make_meta(meta, compressor_name, compressor_version).encode('utf-8'))
        # print("Meta bytes length:", len(meta_bytes))
        blob_bytes = cls.zstd_compress_bytes(blob_bytes)
        checksum = cls.checksum(blob_bytes, meta_bytes)

        with open(path, 'wb') as f:
            f.write(b"LITL")
            f.write(struct.pack("<B", cls.version))
            f.write(struct.pack("<I", checksum))
            f.write(struct.pack("<I", len(meta_bytes)))
            f.write(meta_bytes)
            f.write(blob_bytes)

        total_size = os.path.getsize(path)

        return total_size

    @classmethod
    def read(cls, path: str) -> tuple[bytes, str, str, dict, str]:
        """
        Read the blob and metadata from a .litl file
        """
        with open(path, 'rb') as f:
            magic = f.read(4)
            if magic != b"LITL":
                raise ValueError("Invalid file format")

            version = struct.unpack("<B", f.read(1))[0]
            checksum = struct.unpack("<I", f.read(4))[0]

            if version != cls.version:
                raise ValueError(f"Unsupported version: {version}")
            
            meta_length = struct.unpack("<I", f.read(4))[0]
            # print("Meta length:", meta_length)
            meta_bytes = f.read(meta_length)
            blob_bytes = f.read()

        # checksum validation
        new_checksum = cls.checksum(blob_bytes, meta_bytes)
        if new_checksum != checksum:
            RuntimeWarning("Checksum mismatch, file may be corrupted")
        
        # decompress meta
        blob_bytes = cls.zstd_decompress_bytes(blob_bytes)
        meta_bytes = cls.zstd_decompress_bytes(meta_bytes)

        meta = LitlMeta.deserialize_value(meta_bytes.decode('utf-8'))

        return blob_bytes, meta.compressor_id, meta.compressor_version, meta.compressor_meta, meta.litl_version
