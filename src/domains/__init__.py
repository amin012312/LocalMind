"""
Domains Package for LocalMind

Contains domain-specific modules for education, healthcare, and general assistance.
"""

from .education import EducationDomain
from .healthcare import HealthcareDomain
from .general import GeneralDomain

__all__ = ['EducationDomain', 'HealthcareDomain', 'GeneralDomain']
