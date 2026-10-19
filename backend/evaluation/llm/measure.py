import psutil
import torch


def get_memory_usage():
    # 物理メモリ(RAM)消費量(GB換算)
    ram_gb = psutil.Process().memory_info().rss / (1024**3)
    # Apple shilicon GPU(MPS) 該当メモリ量(GB換算)
    mps_gb = torch.mps.current_allocated_memory() / (1024**3) if torch.backends.mps.is_available() else 0.0
    return ram_gb, mps_gb
