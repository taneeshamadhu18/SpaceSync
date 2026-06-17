"""
Length Rule - Validates space length constraints

This rule ensures that if a space has dimensions, the length meets
minimum and maximum requirements.
"""

from .base import BaseRule


class LengthRule(BaseRule):
    """
    Validates that space length is within acceptable bounds.
    
    Configuration:
        min_length: Minimum allowed length (default: 1)
        max_length: Maximum allowed length (default: 1000)
        allow_zero: Allow length to be 0 (no dimensions) (default: True)
    """
    
    name = "length_rule"
    description = "Validates space length is within acceptable bounds"
    severity = "error"
    
    def __init__(self, min_length=1, max_length=1000, allow_zero=True):
        """
        Initialize LengthRule with constraints.
        
        Args:
            min_length: Minimum allowed length (must be > 0)
            max_length: Maximum allowed length (must be > min_length)
            allow_zero: If True, allow length to be 0 (represents no dimensions)
        """
        super().__init__()
        
        if min_length <= 0:
            raise ValueError("min_length must be greater than 0")
        if max_length <= min_length:
            raise ValueError("max_length must be greater than min_length")
        
        self.min_length = min_length
        self.max_length = max_length
        self.allow_zero = allow_zero
    
    def validate(self, space):
        """
        Validate space length.
        
        Args:
            space: Space instance
        
        Returns:
            list: Violation messages (empty if valid)
        
        Violations:
            - Length is less than minimum
            - Length is greater than maximum
            - Length is 0 when allow_zero is False
        """
        violations = []
        
        if space.length == 0:
            # Length is 0 (no dimensions)
            if not self.allow_zero:
                violations.append(
                    f"Space '{space.name}' has length=0, but dimensions are required"
                )
        else:
            # Length has a value, check bounds
            if space.length < self.min_length:
                violations.append(
                    f"Space '{space.name}' length={space.length} is below minimum {self.min_length}"
                )
            
            if space.length > self.max_length:
                violations.append(
                    f"Space '{space.name}' length={space.length} exceeds maximum {self.max_length}"
                )
        
        return violations
    
    def apply(self, space):
        """
        Apply length constraints (optional transformation).
        
        This method clamps the length to valid bounds.
        
        Args:
            space: Space instance
        
        Returns:
            space: Space with clamped length
        """
        if space.length == 0 and not self.allow_zero:
            space.length = self.min_length
        elif space.length < self.min_length and space.length > 0:
            space.length = self.min_length
        elif space.length > self.max_length:
            space.length = self.max_length
        
        return space
