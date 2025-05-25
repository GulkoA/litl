import os

import torch
import numpy as np
import torcheval.metrics as metrics
# from torchmetrics.image import StructuralSimilarityIndexMeasure
from pytorch_msssim import ssim

from .datawrapper import DataWrapper
from .blobs import Blob

class Evaluator():

  def quality(original: DataWrapper, reconstructed: DataWrapper) -> dict:
    """
    Returns the quality metrics of the reconstructed data compared to the original data
    """
    original_data = original.tensor()
    reconstructed_data = reconstructed.tensor()

    mse = metrics.MeanSquaredError()
    psnr = metrics.PeakSignalNoiseRatio(data_range=original_data.max().item())

    mse_metric = mse.update(reconstructed_data.flatten(), original_data.flatten()).compute().item()
    del mse

    psnr_metric = psnr.update(reconstructed_data.flatten(), original_data.flatten()).compute().item()
    del psnr

    ssim_metric = ssim(reconstructed_data, original_data, data_range=original_data.max().item()).item()

    l1_metric = torch.mean(torch.abs(reconstructed_data - original_data)).item()

    return {
      'mse': mse_metric,
      'psnr': psnr_metric,
      'ssim': ssim_metric,
      'l1': l1_metric,
    }

  def size(compressed_bytes: bytes, original_size: int) -> int:
    """
    Returns the size metrics of the blob
    """
    blob_size = len(compressed_bytes)

    return {
      'original_size': original_size,
      'compressed_size': blob_size,
      'compression_ratio': original_size / blob_size,
    }
