"""
Pollinexus - Data-Driven Pollinator Conservation for Environmental Agencies

A comprehensive data science platform for analyzing pollinator data and
providing evidence-based recommendations for conservation efforts.
"""

__version__ = "0.1.0"
__author__ = "Pollinexus Contributors"
__email__ = "contact@pollinexus.org"

from . import api
from . import core
from . import models
from . import services
from . import tasks
from . import utils

__all__ = [
    "api",
    "core", 
    "models",
    "services",
    "tasks",
    "utils",
] 