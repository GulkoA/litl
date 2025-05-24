# __package__ = "litl.compressors"

from ..datawrapper import DataWrapper
from ..blobs import Blob

import pydantic

class CompressorAbout(pydantic.BaseModel):
  """
  Pydantic model that defines the metadata for a compressor.
  """
  name: str
  description: str
  version: str
  author: str = None
  license: str = None
  url: str = None


class Compressor():
  """
  Interface for all compressors
  """

  @classmethod
  def about(cls) -> CompressorAbout:
    """
    Returns metadata about the compressor, including its name, description, version, author, license, and URL
    """
    raise NotImplementedError()
  
  @classmethod
  def optuna_suggest_config(cls, trial):
    """
    Optional method that can be used to suggest hyperparameters for the compressor using Optuna
    """
    raise NotImplementedError()
  

  @classmethod
  def blob_class(cls) -> Blob:
    """
    Returns the type of Blob object that the Compressor uses to store compressed data
    """
    raise NotImplementedError()

  @classmethod
  def compress(cls, data: DataWrapper, config: pydantic.BaseModel=None) -> tuple[Blob, pydantic.BaseModel]:
    """
    Compresses the data in the given DataWrapper object

    Args:
      data (DataWrapper): The data to be compressed
      config (pydantic.BaseModel): The configuration for the compressor

    Returns:
      tuple[Blob, pydantic.BaseModel]: A tuple containing the compressed data in a Blob object and the configuration used for compression
    """
    raise NotImplementedError()

  @classmethod
  def decompress(cls, data: Blob, meta: dict) -> DataWrapper:
    """
    Decompresses the data in the given Blob object

    Args:
      data (Blob): The compressed data to be decompressed, guaranteed to be the same type as the one returned by compress
      meta (dict): The metadata associated with the compressed data, guaranteed to be the same as the one used during compression

    Returns:
      DataWrapper: The decompressed data
    """
    raise NotImplementedError()

