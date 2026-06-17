# Rule Engine Documentation

## Overview

The Rule Engine provides a plugin-based system for validating and transforming Space objects. It's designed to be:
- **Extensible**: Add new rules by creating a new class
- **Reusable**: Rules can be composed and reused
- **Testable**: Each rule is independent and testable
- **Configurable**: Rules can be parameterized

## Architecture

```
core/rules/
├── __init__.py           - Package exports
├── base.py               - BaseRule abstract class
├── width_rule.py         - Example rule (width validation)
├── length_rule.py        - Example rule (length validation)
└── manager.py            - RuleManager orchestration
```

## Quick Start

### Basic Usage

```python
from core.rules import RuleManager

# Create manager (loads default rules)
manager = RuleManager()

# Validate a space
space = Space.objects.get(id=1)
violations = manager.validate(space)

if violations:
    print("Space has violations:")
    for rule_name, messages in violations.items():
        print(f"  {rule_name}:")
        for msg in messages:
            print(f"    - {msg}")
```

### Get Report

```python
report = manager.get_report(space)
print(f"Status: {report['status']}")
print(f"Violations: {report['violation_count']}")
print(f"Rules checked: {report['rules_checked']}")
```

### List Available Rules

```python
for rule_info in manager.list_rules():
    print(f"{rule_info['name']}: {rule_info['description']}")
    print(f"  Severity: {rule_info['severity']}")
```

## Creating Custom Rules

### Step 1: Create New Rule File

Create a new file in `core/rules/`:

```python
# core/rules/area_rule.py

from .base import BaseRule

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
                    f"Space '{space.name}' area={area} exceeds max {self.max_area}"
                )
        
        return violations
```

### Step 2: Import and Register

```python
from core.rules import RuleManager
from core.rules.area_rule import AreaRule

# Create manager
manager = RuleManager()

# Add custom rule
manager.register(AreaRule(max_area=1000))

# Use it
violations = manager.validate(space)
```

### Step 3: Update `__init__.py`

Add your rule to the package exports:

```python
# core/rules/__init__.py

from .area_rule import AreaRule

__all__ = [
    'BaseRule',
    'WidthRule',
    'LengthRule',
    'AreaRule',    # ← Add here
    'RuleManager',
]
```

## Built-in Rules

### WidthRule

Validates space width is within bounds.

```python
from core.rules import WidthRule

# Default: min=1, max=1000, allow_zero=True
rule = WidthRule()

# Custom bounds
rule = WidthRule(min_width=2, max_width=500, allow_zero=False)
```

Violations:
- Width below minimum
- Width above maximum
- Width is 0 when not allowed

### LengthRule

Validates space length is within bounds.

```python
from core.rules import LengthRule

rule = LengthRule(min_length=1, max_length=1000, allow_zero=True)
```

Violations:
- Length below minimum
- Length above maximum
- Length is 0 when not allowed

## Advanced Usage

### Custom Configuration

```python
manager = RuleManager(auto_register_defaults=False)

# Register only specific rules with custom config
manager.register(WidthRule(min_width=5, max_width=100))
manager.register(LengthRule(min_length=5, max_length=100))
```

### Selective Validation

```python
# Run only specific rules
violations = manager.validate(space, rule_names=['width_rule'])
```

### Apply Transformations

```python
# Rules can transform spaces (e.g., clamping values)
space = manager.apply_all(space)
space.save()
```

### Rule Severity Levels

Rules have a `severity` attribute:
- **'error'**: Critical constraint
- **'warning'**: Should be addressed
- **'info'**: Informational only

```python
class MyRule(BaseRule):
    severity = "warning"  # Non-critical
```

## Integration Examples

### In Views

```python
from rest_framework.response import Response
from core.rules import RuleManager

@api_view(['POST'])
def validate_space(request, space_id):
    space = Space.objects.get(id=space_id)
    
    manager = RuleManager()
    violations = manager.validate(space)
    
    if violations:
        return Response({'violations': violations}, status=400)
    
    return Response({'status': 'valid'}, status=200)
```

### In Serializers

```python
from rest_framework import serializers
from core.rules import RuleManager

class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = ['id', 'name', 'width', 'length']
    
    def validate(self, data):
        space = Space(**data)
        
        manager = RuleManager()
        violations = manager.validate(space)
        
        if violations:
            raise serializers.ValidationError(violations)
        
        return data
```

### In Signals

```python
from django.db.models.signals import pre_save
from django.dispatch import receiver
from core.rules import RuleManager

@receiver(pre_save, sender=Space)
def validate_space_on_save(sender, instance, **kwargs):
    manager = RuleManager()
    violations = manager.validate(instance)
    
    if violations:
        raise ValueError(f"Space validation failed: {violations}")
```

## Testing Rules

```python
from django.test import TestCase
from core.models import Space, Project, Workspace
from core.rules import WidthRule

class WidthRuleTestCase(TestCase):
    def setUp(self):
        self.workspace = Workspace.objects.create(name='Test', owner_id=1)
        self.project = Project.objects.create(name='Test', workspace=self.workspace)
        self.space = Space.objects.create(
            name='Test', project=self.project, width=10, length=20
        )
        self.rule = WidthRule(min_width=5, max_width=100)
    
    def test_valid_width(self):
        violations = self.rule.validate(self.space)
        self.assertEqual(violations, [])
    
    def test_width_too_small(self):
        self.space.width = 2
        violations = self.rule.validate(self.space)
        self.assertGreater(len(violations), 0)
    
    def test_width_too_large(self):
        self.space.width = 200
        violations = self.rule.validate(self.space)
        self.assertGreater(len(violations), 0)
```

## Examples: Adding More Rules

Here's how to add more rules easily:

### Rule 3: NameRule

```python
from .base import BaseRule

class NameRule(BaseRule):
    name = "name_rule"
    description = "Validates space name format"
    
    def validate(self, space):
        violations = []
        if not space.name or len(space.name.strip()) == 0:
            violations.append("Space name cannot be empty")
        if len(space.name) > 100:
            violations.append("Space name must be 100 characters or less")
        return violations
```

### Rule 4: DescriptionRule

```python
from .base import BaseRule

class DescriptionRule(BaseRule):
    name = "description_rule"
    description = "Validates space description"
    
    def validate(self, space):
        violations = []
        if len(space.description) > 500:
            violations.append("Description must be 500 characters or less")
        return violations
```

### Rule 5: RatioRule

```python
from .base import BaseRule

class RatioRule(BaseRule):
    name = "ratio_rule"
    description = "Ensures width-to-length ratio is reasonable"
    
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
                    f"Width-to-length ratio {ratio:.2f} outside acceptable range "
                    f"[{self.min_ratio}, {self.max_ratio}]"
                )
        
        return violations
```

## Best Practices

1. **One Rule, One Responsibility**: Each rule should validate one concept
2. **Clear Naming**: Rule names should be descriptive (e.g., `width_rule`, not `rule1`)
3. **Configurable**: Make rules flexible with constructor parameters
4. **Idempotent**: Running a rule multiple times should produce the same result
5. **Documentation**: Document what your rule validates and any side effects
6. **Testing**: Write tests for each rule
7. **Error Messages**: Provide clear, actionable violation messages

## Performance Considerations

- Rules are executed sequentially
- Each rule validates the entire space
- For performance-critical paths, validate only specific rules:
  ```python
  violations = manager.validate(space, rule_names=['width_rule', 'length_rule'])
  ```

## Future Extensions

Possible enhancements:
- Rule dependencies (Rule A must run before Rule B)
- Rule groups (group related rules)
- Async rule execution
- Rule configuration from database
- Rule versioning
- Rule impact analysis

