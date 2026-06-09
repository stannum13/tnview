"""Terminal-native viewer for tensor-network dynamics telemetry."""

from tnview.interface import view
from tnview.recorder import Recorder

__all__ = ["Recorder", "__version__", "view"]

__version__ = "0.1.0"
