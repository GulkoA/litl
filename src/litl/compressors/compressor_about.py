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