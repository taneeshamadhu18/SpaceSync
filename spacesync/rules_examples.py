"""
Example: Custom Rule Implementation

This script demonstrates how easy it is to add a 5th, 6th, or more rules
to the SpaceSync rule engine.

Run this in Django shell:
    python manage.py shell < rules_examples.py
"""

from core.rules import RuleManager
from core.rules.base import BaseRule
from core.models import Space

# ============================================================================
# Example 1: Adding a Custom AreaRule
# ============================================================================

class AreaRule(BaseRule):
    """Validates that space area (width × length) is within bounds."""
    
    name = "area_rule"
    description = "Ensures space area doesn't exceed limits"
    severity = "warning"
    
    def __init__(self, max_area=500):
        super().__init__()
        self.max_area = max_area
    
    def validate(self, space):
        violations = []
        
        if space.width > 0 and space.length > 0:
            area = space.width * space.length
            if area > self.max_area:
                violations.append(
                    f"Space '{space.name}' area={area:.2f} exceeds max {self.max_area}"
                )
        
        return violations


# ============================================================================
# Example 2: Adding a Custom NameRule
# ============================================================================

class NameRule(BaseRule):
    """Validates space name meets requirements."""
    
    name = "name_rule"
    description = "Validates space name is not empty and within length limits"
    severity = "error"
    
    def __init__(self, min_length=1, max_length=100):
        super().__init__()
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, space):
        violations = []
        
        if not space.name or len(space.name.strip()) == 0:
            violations.append("Space name cannot be empty")
        elif len(space.name) > self.max_length:
            violations.append(
                f"Space name must be {self.max_length} characters or less"
            )
        elif len(space.name) < self.min_length:
            violations.append(
                f"Space name must be at least {self.min_length} character"
            )
        
        return violations


# ============================================================================
# Example 3: Adding a Custom RatioRule
# ============================================================================

class RatioRule(BaseRule):
    """Ensures width-to-length ratio is within acceptable bounds."""
    
    name = "ratio_rule"
    description = "Validates width-to-length ratio is reasonable"
    severity = "warning"
    
    def __init__(self, min_ratio=0.5, max_ratio=2.0):
        super().__init__()
        self.min_ratio = min_ratio
        self.max_ratio = max_ratio
    
    def validate(self, space):
        violations = []
        
        if space.width > 0 and space.length > 0:
            ratio = space.width / space.length
            if ratio < self.min_ratio or ratio > self.max_ratio:
                violations.append(
                    f"Space '{space.name}' width-to-length ratio {ratio:.2f} "
                    f"outside acceptable range [{self.min_ratio}, {self.max_ratio}]"
                )
        
        return violations


# ============================================================================
# Test the Custom Rules
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("DEMONSTRATION: Adding Custom Rules to SpaceSync")
    print("=" * 70)
    
    # Create manager
    manager = RuleManager()
    
    # Register custom rules
    print("\n[Step 1] Registering custom rules...")
    manager.register(AreaRule(max_area=300))
    manager.register(NameRule(min_length=2, max_length=50))
    manager.register(RatioRule(min_ratio=0.8, max_ratio=2.5))
    
    print(f"  ✓ Registered 3 custom rules")
    
    # List all rules
    print("\n[Step 2] Available rules:")
    for i, rule_info in enumerate(manager.list_rules(), 1):
        print(f"  {i}. {rule_info['name']}")
        print(f"     Description: {rule_info['description']}")
        print(f"     Severity: {rule_info['severity']}")
    
    # Get test spaces
    print("\n[Step 3] Testing rules on actual spaces...")
    spaces = Space.objects.all()[:3]
    
    for space in spaces:
        print(f"\n  Space: {space.name} (width={space.width}, length={space.length})")
        
        # Get report
        report = manager.get_report(space)
        
        if report['status'] == 'valid':
            print(f"    Status: ✓ VALID")
        else:
            print(f"    Status: ✗ INVALID ({report['violation_count']} violations)")
            
            for rule_name, messages in report['violations'].items():
                for msg in messages:
                    print(f"      - [{rule_name}] {msg}")
    
    # Show how easy it is to add another rule
    print("\n" + "=" * 70)
    print("HOW TO ADD A 4TH, 5TH, OR MORE RULES:")
    print("=" * 70)
    print("""
    1. Create a new rule class inheriting from BaseRule:
    
        class MyNewRule(BaseRule):
            name = "my_rule"
            description = "..."
            
            def validate(self, space):
                violations = []
                # Your validation logic here
                return violations
    
    2. Register it with the manager:
    
        manager.register(MyNewRule(param1=value1))
    
    3. That's it! The rule is now active and will be run on all validations.
    
    Key Benefits:
    ✓ Easy to add new rules without modifying existing code
    ✓ Rules are reusable across different parts of the app
    ✓ Each rule is independently testable
    ✓ Rules can have their own configuration
    ✓ Follows the Open-Closed Principle (open for extension, closed for modification)
    """)
    
    print("=" * 70)


if __name__ == '__main__':
    main()
