"""
Rule Manager - Orchestrates rule execution

This module provides the RuleManager class which manages and executes
multiple validation rules against space objects.
"""

from typing import List, Dict, Any
from .base import BaseRule
from .width_rule import WidthRule
from .length_rule import LengthRule


class RuleManager:
    """
    Manages and executes validation rules.
    
    The RuleManager maintains a registry of rules and can:
    1. Validate spaces against all registered rules
    2. Apply rule transformations
    3. Generate validation reports
    
    Usage:
        # Create manager with default rules
        manager = RuleManager()
        
        # Add custom rule
        from my_rules import CustomRule
        manager.register(CustomRule(param1=value1))
        
        # Validate a space
        violations = manager.validate(space)
        
        # Apply all rules
        space = manager.apply_all(space)
        
        # Get report
        report = manager.get_report(space)
    """
    
    def __init__(self, auto_register_defaults=True):
        """
        Initialize the RuleManager.
        
        Args:
            auto_register_defaults: If True, automatically register built-in rules
        """
        self.rules: Dict[str, BaseRule] = {}
        
        if auto_register_defaults:
            # Register built-in rules
            self.register(WidthRule())
            self.register(LengthRule())
    
    def register(self, rule: BaseRule) -> None:
        """
        Register a new validation rule.
        
        Args:
            rule: Rule instance (must inherit from BaseRule)
        
        Raises:
            TypeError: If rule does not inherit from BaseRule
            ValueError: If rule name is already registered
        
        Example:
            from core.rules import RuleManager, WidthRule
            manager = RuleManager(auto_register_defaults=False)
            manager.register(WidthRule(min_width=2, max_width=500))
        """
        if not isinstance(rule, BaseRule):
            raise TypeError(f"Rule must inherit from BaseRule, got {type(rule)}")
        
        if rule.name in self.rules:
            raise ValueError(f"Rule '{rule.name}' is already registered")
        
        self.rules[rule.name] = rule
    
    def unregister(self, rule_name: str) -> None:
        """
        Unregister a validation rule.
        
        Args:
            rule_name: Name of the rule to unregister
        
        Raises:
            KeyError: If rule is not registered
        """
        if rule_name not in self.rules:
            raise KeyError(f"Rule '{rule_name}' is not registered")
        
        del self.rules[rule_name]
    
    def get_rule(self, rule_name: str) -> BaseRule:
        """
        Get a registered rule by name.
        
        Args:
            rule_name: Name of the rule
        
        Returns:
            BaseRule: The rule instance
        
        Raises:
            KeyError: If rule is not registered
        """
        if rule_name not in self.rules:
            raise KeyError(f"Rule '{rule_name}' is not registered")
        
        return self.rules[rule_name]
    
    def list_rules(self) -> List[Dict[str, Any]]:
        """
        Get information about all registered rules.
        
        Returns:
            list: List of dicts with rule info (name, description, severity)
        
        Example:
            for rule_info in manager.list_rules():
                print(f"{rule_info['name']}: {rule_info['description']}")
        """
        return [
            {
                'name': rule.name,
                'description': rule.description,
                'severity': rule.severity,
                'class': rule.__class__.__name__,
            }
            for rule in self.rules.values()
        ]
    
    def validate(self, space, rule_names: List[str] = None) -> Dict[str, List[str]]:
        """
        Validate a space against registered rules.
        
        Args:
            space: Space instance to validate
            rule_names: Optional list of specific rule names to run.
                       If None, runs all registered rules.
        
        Returns:
            dict: {rule_name: [violations]} or empty dict if valid
        
        Example:
            violations = manager.validate(space)
            
            if violations:
                for rule_name, messages in violations.items():
                    print(f"{rule_name}:")
                    for msg in messages:
                        print(f"  - {msg}")
        """
        violations = {}
        
        rules_to_run = self.rules.values()
        if rule_names:
            rules_to_run = [self.get_rule(name) for name in rule_names]
        
        for rule in rules_to_run:
            rule_violations = rule.validate(space)
            if rule_violations:
                violations[rule.name] = rule_violations
        
        return violations
    
    def apply_all(self, space):
        """
        Apply all registered rules to a space (transformations).
        
        This runs the optional apply() method on each rule to transform
        the space object.
        
        Args:
            space: Space instance to transform
        
        Returns:
            space: Transformed space instance
        
        Warning:
            This modifies the space in-place. Call space.save() to persist.
        
        Example:
            space = manager.apply_all(space)
            space.save()
        """
        for rule in self.rules.values():
            space = rule.apply(space)
        
        return space
    
    def get_report(self, space) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report for a space.
        
        Args:
            space: Space instance to validate
        
        Returns:
            dict: Report with overall status, violations, and rule details
        
        Example:
            report = manager.get_report(space)
            print(f"Status: {report['status']}")
            print(f"Violations: {report['violation_count']}")
        """
        violations = self.validate(space)
        
        report = {
            'space_id': space.id,
            'space_name': space.name,
            'status': 'valid' if not violations else 'invalid',
            'violation_count': sum(len(v) for v in violations.values()),
            'violations': violations,
            'rules_checked': list(self.rules.keys()),
            'total_rules': len(self.rules),
        }
        
        return report
    
    def __repr__(self):
        """String representation."""
        return f"RuleManager(rules={len(self.rules)})"
    
    def __str__(self):
        """Human-readable representation."""
        rules_str = ', '.join(self.rules.keys())
        return f"RuleManager with rules: [{rules_str}]"
