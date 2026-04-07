from .BCRP import BCRPDataSeries, BCRPSeries

# from .inei.fetcher import MicrodatosINEIFetcher
from .utils import print_tree
from .version import version as __version__

__all__ = ["BCRPDataSeries", "BCRPSeries", "print_tree", "__version__"]
