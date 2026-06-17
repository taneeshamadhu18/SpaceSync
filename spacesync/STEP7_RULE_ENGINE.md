# Step 7: Rule Engine Implementation ✅

## Summary

Successfully implemented an extensible **Rule Engine** that validates and transforms Space objects. The system is designed to make it trivial to add new rules.

## Architecture

```
core/rules/
├── __init__.py           - Package exports
├── base.py               - BaseRule abstract class
├── width_rule.py         - Width validation rule
├── length_rule.py        - Length validation rule
└── manager.py            - RuleManager orchestration
```

## What Makes It Extensible

### Key Design Principle: Plugin Architecture

Each rule is:
1. **Completely Independent** - No dependencies on other rules
2. **Self-Contained** - All logic in one file
3. **Parameterized** - Configuration passed to constructor
4. **Testable** - Can be tested in isolation

### Adding a New Rule (3 Steps)

**Step 1: Create rule file** (e.g., `core/rules/area_rule.py`)
```python
from .base import BaseRule

class AreaRule(BaseRule):
    name = "area_rule"
    description = "Validates space area"
    
    def __init__(self, max_area=500):
        super().__init__()
        self.max_area = max_area
    
    def validate(self, space):
        violations = []
        if space.width > 0 and space.length > 0:
            area = space.width * space.length
            if area > self.max_area:
                violations.append(f"Area exceeds {self.max_area}")
        return violations
```

**Step 2: Register rule**
```python
from core.rules import RuleManager
from core.rules.area_rule import AreaRule

manager = RuleManager()
manager.register(AreaRule(max_area=1000))
```

**Step 3: Use it**
```python
violations = manager.validate(space)
```

## Built-in Rules

### 1. WidthRule
- Validates width is within bounds (default: 1-1000)
- Configurable min/max
- Can allow width=0 (no dimensions)

### 2. LengthRule
- Validates length is within bounds (default: 1-1000)
- Configurable min/max
- Can allow length=0 (no dimensions)

## How to Add 5+ Rules

The architecture makes it trivial:

```
Rule 3: AreaRule             → core/rules/area_rule.py
Rule 4: RatioRule            → core/rules/ratio_rule.py
Rule 5: NameRule             → core/rules/name_rule.py
Rule 6: DescriptionRule      → core/rules/description_rule.py
Rule 7: CustomBusinessRule   → core/rules/custom_business_rule.py
```

Just create one file per rule, no changes to existing code!

## Core Classes

### BaseRule (abstract)

```python
class BaseRule(ABC):
    name: str                    # Rule identifier
    description: str             # Human-readable description
    severity: str                # 'error', 'warning', 'info'
    
    def validate(space) → List   # Return list of violations
    def apply(space) → space     # Optional: transform space
```

### RuleManager

```python
manager = RuleManager()
manager.register(rule)                          # Add rule
manager.unregister("rule_name")                 # Remove rule
violations = manager.validate(space)            # Run all rules
violations = manager.validate(space, ["rule1"]) # Run specific rules
report = manager.get_report(space)              # Full report
space = manager.apply_all(space)                # Apply transformations
manager.list_rules()                            # List all rules
```

## Test Results

✅ All rules working correctly:

```
Registered Rules:
  1. width_rule: Validates space width is within acceptable bounds
  2. length_rule: Validates space length is within acceptable bounds
  3. area_rule: Ensures space area doesn't exceed limits

Testing on spaces:
  Room E (0x0): VALID ✓
  Room D (12x18, area=216): VALID ✓
  Room C (15x25, area=375): INVALID ✗ (area > 300 max)
```

## Key Features

### 1. Extensibility
- Add new rules without modifying existing code
- Plugin architecture
- No coupling between rules

### 2. Configurability
- Rules accept constructor parameters
- Per-instance configuration
- Easy to create rule variants

### 3. Testability
- Each rule is independently testable
- No side effects
- Deterministic validation

### 4. Composability
- Rules can be combined
- Selective rule execution
- No rule dependencies (future: can add if needed)

### 5. Reporting
- Detailed violation reports
- Severity levels (error/warning/info)
- Rule statistics

## Integration Examples

### In Views
```python
from core.rules import RuleManager

@api_view(['POST'])
def create_space(request):
    space = Space.objects.create(...)
    
    manager = RuleManager()
    violations = manager.validate(space)
    
    if violations:
        return Response({'violations': violations}, 400)
    return Response({'success': True}, 201)
```

### In Serializers
```python
class SpaceSerializer(serializers.ModelSerializer):
    def validate(self, data):
        from core.rules import RuleManager
        
        space = Space(**data)
        manager = RuleManager()
        violations = manager.validate(space)
        
        if violations:
            raise serializers.ValidationError(violations)
        
        return data
```

### In Models (Signals)
```python
from django.db.models.signals import pre_save

@receiver(pre_save, sender=Space)
def validate_space(sender, instance, **kwargs):
    from core.rules import RuleManager
    
    manager = RuleManager()
    violations = manager.validate(instance)
    
    if violations:
        raise ValueError(f"Validation failed: {violations}")
```

## Documentation

- **RULE_ENGINE_GUIDE.md** - Comprehensive documentation with:
  - Quick start examples
  - Step-by-step custom rule creation
  - Advanced usage patterns
  - Integration examples
  - Testing examples
  - Best practices
  - Performance considerations

- **rules_examples.py** - Runnable examples showing:
  - How to add AreaRule
  - How to add NameRule
  - How to add RatioRule
  - Testing custom rules
  - How easy it is to add more

## Files Created

```
core/rules/
├── __init__.py          (50 lines) - Exports and docstring
├── base.py             (100+ lines) - Abstract base class
├── width_rule.py       (70+ lines) - Width validation
├── length_rule.py      (70+ lines) - Length validation
└── manager.py         (200+ lines) - Rule orchestration

Documentation:
├── RULE_ENGINE_GUIDE.md (300+ lines) - Complete guide
└── rules_examples.py    (150+ lines) - Runnable examples
```

## Why This Satisfies "Easy to Add 5th Rule"

✅ **No Code Modification Required**
- Add new rule without touching BaseRule, Manager, or existing rules

✅ **Simple Template**
- All rules follow the same pattern
- Copy-paste template from any existing rule

✅ **Pluggable**
- Just create file + inherit BaseRule + override validate()
- Register with manager in 1 line

✅ **Isolated**
- New rule can't break existing rules
- Each rule has its own file

✅ **Testable**
- Can write unit tests for new rule independently

## Example: Adding the 5th Rule

Create `core/rules/occupancy_rule.py`:

```python
from .base import BaseRule

class OccupancyRule(BaseRule):
    name = "occupancy_rule"
    description = "Validates space can accommodate required occupancy"
    
    def __init__(self, sqft_per_person=100):
        super().__init__()
        self.sqft_per_person = sqft_per_person
    
    def validate(self, space):
        violations = []
        if space.width > 0 and space.length > 0:
            area = space.width * space.length
            max_occupancy = area / self.sqft_per_person
            # Your validation logic...
        return violations
```

Register it:
```python
from core.rules.occupancy_rule import OccupancyRule
manager.register(OccupancyRule(sqft_per_person=150))
```

Done! ✅

## Next Steps

1. ✅ Rule Engine - DONE
2. ⏭️ Integrate rules into SpaceViewSet (validation before save)
3. ⏭️ Add rule API endpoint (list/execute rules)
4. ⏭️ Create rule history/audit log
5. ⏭️ Add rule scheduling (run rules at specific times)
