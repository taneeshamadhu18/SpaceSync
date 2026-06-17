"""
Base Rule Class for the Rule Engine

This module defines the abstract base class for all validation rules.
All rule implementations should inherit from BaseRule and override
the validate() and/or apply() methods.
"""

from abc import ABC, abstractmethod


class BaseRule(ABC):
    """
    Abstract base class for validation rules.
    
    Attributes:
        name: Unique identifier for the rule
        description: Human-readable description of what the rule does
        severity: 'error', 'warning', or 'info' (default: 'error')
    
    Methods:
        validate(space): Check if space violates this rule. Return list of violations.
        apply(space): Apply rule logic to space (e.g., transformations). Optional.
    
    Example:
        class MyCustomRule(BaseRule):
            name = "my_rule"
            description = "Checks something custom"
            severity = "error"
            
            def validate(self, space):
                violations = []
                if some_condition(space):
                    violations.append("Space violates my_rule")
                return violations
            
            def apply(self, space):
                # Optional: Apply transformations
                space.some_field = some_value
                return space
    """
    
    name: str
    description: str
    severity: str = 'error'  # 'error', 'warning', or 'info'
    
    def __init__(self):
        """Initialize the rule."""
        if not hasattr(self, 'name') or not self.name:
            raise ValueError(f"{self.__class__.__name__} must define a 'name' attribute")
        if not hasattr(self, 'description') or not self.description:
            raise ValueError(f"{self.__class__.__name__} must define a 'description' attribute")
        
        if self.severity not in ['error', 'warning', 'info']:
            raise ValueError(f"severity must be one of: error, warning, info")
    
    @abstractmethod
    def validate(self, space):
        """
        Validate a space object against this rule.
        
        Args:
            space: Space model instance to validate
        
        Returns:
            list: List of violation messages (empty if no violations)
        
        Example:
            def validate(self, space):
                violations = []
                if space.width < 10:
                    violations.append(f"Width {space.width} is less than minimum 10")
                return violations
        """
        pass
    
    def apply(self, space):
        """
        Optional: Apply rule logic to transform or modify space.
        Override this method if your rule needs to modify the space.
        
        Args:
            space: Space model instance to transform
        
        Returns:
            space: Modified space instance (or original if no changes)
        
        Note:
            This method is NOT called automatically. Use it in your business logic
            when you need to apply transformations based on rules.
        
        Example:
            def apply(self, space):
                # Round dimensions to nearest 0.5
                space.width = round(space.width * 2) / 2
                space.length = round(space.length * 2) / 2
                return space
        """
        return space
    
    def __repr__(self):
        """String representation of the rule."""
        return f"{self.__class__.__name__}(name={self.name}, severity={self.severity})"
    
    def __str__(self):
        """Human-readable description."""
        return f"{self.name}: {self.description}"
