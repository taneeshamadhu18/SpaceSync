"""
Width Rule - Validates space width constraints

This rule ensures that if a space has dimensions, the width meets
minimum and maximum requirements.
"""

from .base import BaseRule


class WidthRule(BaseRule):
    """
    Validates that space width is within acceptable bounds.
    
    Configuration:
        min_width: Minimum allowed width (default: 1)
        max_width: Maximum allowed width (default: 1000)
        allow_zero: Allow width to be 0 (no dimensions) (default: True)
    """
    
    name = "width_rule"
    description = "Validates space width is within acceptable bounds"
    severity = "error"
    
    def __init__(self, min_width=1, max_width=1000, allow_zero=True):
        """
        Initialize WidthRule with constraints.
        
        Args:
            min_width: Minimum allowed width (must be > 0)
            max_width: Maximum allowed width (must be > min_width)
            allow_zero: If True, allow width to be 0 (represents no dimensions)
        """
        super().__init__()
        
        if min_width <= 0:
            raise ValueError("min_width must be greater than 0")
        if max_width <= min_width:
            raise ValueError("max_width must be greater than min_width")
        
        self.min_width = min_width
        self.max_width = max_width
        self.allow_zero = allow_zero
    
    def validate(self, space):
        """
        Validate space width.
        
        Args:
            space: Space instance
        
        Returns:
            list: Violation messages (empty if valid)
        
        Violations:
            - Width is less than minimum
            - Width is greater than maximum
            - Width is 0 when allow_zero is False
        """
        violations = []
        
        if space.width == 0:
            # Width is 0 (no dimensions)
            if not self.allow_zero:
                violations.append(
                    f"Space '{space.name}' has width=0, but dimensions are required"
                )
        else:
            # Width has a value, check bounds
            if space.width < self.min_width:
                violations.append(
                    f"Space '{space.name}' width={space.width} is below minimum {self.min_width}"
                )
            
            if space.width > self.max_width:
                violations.append(
                    f"Space '{space.name}' width={space.width} exceeds maximum {self.max_width}"
                )
        
        return violations
    
    def apply(self, space):
        """
        Apply width constraints (optional transformation).
        
        This method clamps the width to valid bounds.
        
        Args:
            space: Space instance
        
        Returns:
            space: Space with clamped width
        """
        if space.width == 0 and not self.allow_zero:
            space.width = self.min_width
        elif space.width < self.min_width and space.width > 0:
            space.width = self.min_width
        elif space.width > self.max_width:
            space.width = self.max_width
        
        return space
