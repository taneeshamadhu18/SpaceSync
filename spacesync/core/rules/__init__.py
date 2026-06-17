"""
Rule Engine for Space Validation

This module provides a plugin-based rule system for validating and processing
space objects. Rules can be easily extended by creating new rule classes that
inherit from BaseRule.

Usage:
    from core.rules import RuleManager
    
    manager = RuleManager()
    space = Space.objects.get(id=1)
    violations = manager.validate(space)
    
    if violations:
        print("Space has violations:")
        for violation in violations:
            print(f"  - {violation}")
"""

from .base import BaseRule
from .width_rule import WidthRule
from .length_rule import LengthRule
from .manager import RuleManager

__all__ = [
    'BaseRule',
    'WidthRule',
    'LengthRule',
    'RuleManager',
]
