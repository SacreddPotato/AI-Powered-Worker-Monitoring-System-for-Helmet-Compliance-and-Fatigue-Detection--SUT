import os

import torch


def resolve_inference_device() -> str:
    configured = os.environ.get("SAFEVISION_INFERENCE_DEVICE", "auto").strip()
    if configured and configured.lower() != "auto":
        return configured
    return "cuda:0" if torch.cuda.is_available() else "cpu"


def torch_device_name(device: str) -> str:
    if str(device).isdigit():
        return f"cuda:{device}"
    return str(device)
