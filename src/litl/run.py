import argparse
import os
from functools import partial
import time

import numpy as np
import torch

from .compressors import Compressor
from .datawrapper import DataWrapper
from .blobs import Blob
from .evaluator import Evaluator
from .dot_litl import DotLitl

# import all compressors
import importlib

def _discover_compressors():
    """
    Discover all compressors in the entry points
    """
    return {
        ep.name: ep.load()
        for ep in importlib.metadata.entry_points(group="litl.compressors")
    }

global _AVAILABLE_COMPRESSORS
_AVAILABLE_COMPRESSORS = None

def get_compressor(name: str) -> Compressor:
    """
    Get a compressor by name
    """
    global _AVAILABLE_COMPRESSORS
    if not _AVAILABLE_COMPRESSORS:
        _AVAILABLE_COMPRESSORS = _discover_compressors()

    if name in _AVAILABLE_COMPRESSORS:
        # if the compressor is in the entry points, return it
        return _AVAILABLE_COMPRESSORS[name]
    else:
        # if the compressor is not in the entry points, try to load it from a file
        try:
          path, classname = name.rsplit(':', 1)

          spec = importlib.util.spec_from_file_location(path, os.path.expanduser(path))
          mod  = importlib.util.module_from_spec(spec)
          spec.loader.exec_module(mod)
          cls = getattr(mod, classname)

        except Exception as e:
          raise ValueError(f"Failed to load compressor {name}. Available compressors in pip: {list(_AVAILABLE_COMPRESSORS.keys())}, available classes in {path}: {dir(mod)}") from e
        
        if not issubclass(cls, Compressor):
            raise ValueError(f"Compressor {name} is not a subclass of Compressor")
        return cls
        

def compress(compressor_name: str, data_path: str, config: dict, litl_file_path: str=None):
    # load data
    compressor_class = get_compressor(compressor_name)

    data = DataWrapper.from_file(data_path)
    original_size = os.path.getsize(data_path)

    start_time = time.time()
    compressed_blob, meta = compressor_class.compress(data, config)
    compression_time = time.time() - start_time

    del data

    start_time = time.time()
    compressed_bytes = compressed_blob.to_bytes()
    io_time = time.time() - start_time
    
    metrics = Evaluator.size(compressed_bytes, original_size)

    metrics.update({
        'compression_time': compression_time,
        'io_time': io_time,
    })

    if litl_file_path is not None:
        # save to litl file
        total_size = DotLitl.save(litl_file_path, compressed_bytes, meta, compressor_name, compressor_class.about().version)
        metrics.update({
            'total_litl_size': total_size,
        })

    return compressed_blob, meta, metrics

def decompress(compressor_name=None, original_data_path: str=None, compressed_bytes: bytes=None, meta: dict=None, litl_file_path: str=None, decompressed_path: str=None):

    if litl_file_path is not None:
        # read from litl file
        blob_bytes, compressor_name, compressor_version, meta, litl_version = DotLitl.read(litl_file_path)
        compressor_class = get_compressor(compressor_name)

        if compressor_class.about().version != compressor_version:
            raise ImportWarning(f"Compressor version mismatch: loaded compressor is v{compressor_class.about().version}, originally compressed with v{compressor_version}")

        compressed_blob_class = compressor_class.blob_class()
        compressed_blob = compressed_blob_class.from_bytes(blob_bytes)
    elif compressed_bytes is not None and meta is not None:
        # read from bytes
        compressor_class = get_compressor(compressor_name)
        compressed_blob_class = compressor_class.blob_class()
        compressed_blob = compressed_blob_class.from_bytes(compressed_bytes)
    else:
        raise ValueError("Either compressed_bytes with meta or litl_file_path must be provided")
    
    start_time = time.time()
    decompressed_data = compressor_class.decompress(compressed_blob, meta)
    decompression_time = time.time() - start_time

    metrics = {
        'decompression_time': decompression_time,
    }

    if original_data_path is not None:
        original_data = DataWrapper.from_file(original_data_path)
    
        metrics.update(Evaluator.quality(original_data, decompressed_data))

    if decompressed_path is not None:
        # save decompressed data
        decompressed_data.save_to_file(decompressed_path)

    return decompressed_data, metrics


def evaluate(compressor_name: str, data_path: str, config, decompressed_path: str=None, litl_file_path: str=None):

    # make deterministic
    torch.manual_seed(0)
    np.random.seed(0)

    # optimize cuda
    torch.set_float32_matmul_precision("medium")

    compressor = get_compressor(compressor_name)

    metrics = {}

    # compress
    compressed_blob, meta, compress_metrics = compress(compressor_name, data_path, config, litl_file_path)
    metrics.update(compress_metrics)

    # decompress
    decompressed_data, decompress_metrics = decompress(compressor_name, data_path, compressed_blob.to_bytes(), meta, decompressed_path=decompressed_path)
    metrics.update(decompress_metrics)

    return decompressed_data, metrics
