# Step 9: Bulk Endpoints — Complete

## Overview

All bulk endpoints use `django.db.transaction.atomic` for **all-or-nothing semantics**.
If any single item in the batch fails (validation, not found, access denied, version conflict),
a `ValidationError` is raised **inside** the atomic block, causing the entire transaction to roll back.

---

## Endpoints

### 1. `POST /api/spaces/bulk_create/`

Bulk create multiple spaces in a single atomic transaction.

**Request:**
```json
{
    "project": 1,
    "spaces": [
        {"name": "Space A", "description": "...", "width": 10, "length": 20},
        {"name": "Space B", "description": "...", "width": 15, "length": 25}
    ]
}
```

**Rollback triggers:**
- Any space fails dimension validation (e.g., negative width)
- Missing required `name` field
- Inconsistent dimensions (one > 0, other = 0)

---

### 2. `PUT/PATCH /api/spaces/bulk_update/`

Bulk update multiple spaces atomically. Supports partial updates and optimistic locking.

**Request:**
```json
{
    "spaces": [
        {"id": 1, "name": "Updated Name", "width": 20},
        {"id": 2, "description": "New description", "version": 3}
    ]
}
```

**Rollback triggers:**
- Any space ID not found
- Access denied to any space
- Version conflict (optimistic locking) on any space
- Validation failure on any space's fields
- No updateable fields provided for any space

---

### 3. `POST /api/spaces/bulk_delete/`

Bulk delete multiple spaces atomically.

**Request:**
```json
{
    "ids": [1, 2, 3]
}
```

**Rollback triggers:**
- Any space ID not found
- Access denied to any space
- Duplicate IDs in list

---

## How `transaction.atomic` Works Here

```python
from django.db import transaction
from rest_framework import serializers

# Inside each bulk endpoint:
with transaction.atomic():
    for item in items:
        # validate / lookup / process each item
        if something_fails:
            raise serializers.ValidationError({...})
            # ↑ This exception causes Django to ROLLBACK
            #   all database changes made within this block
        
        # perform DB write (create/update/delete)

# If we reach here, all items succeeded → transaction COMMITTED
```

Key principle: the `ValidationError` is raised **inside** the `with transaction.atomic():` block,
so Django automatically rolls back any partial writes that occurred before the error.

---

## Serializers Added

| Serializer | Purpose |
|---|---|
| `BulkSpaceSerializer` | Validates bulk create input (already existed) |
| `BulkUpdateSpaceSerializer` | Validates bulk update input (id required, dimensions optional) |
| `BulkDeleteSpaceSerializer` | Validates bulk delete input (list of integer IDs, no duplicates) |

All serializers enforce a **max batch size of 100 items**.

---

## Files Modified

| File | Changes |
|---|---|
| `core/serializers.py` | Added `BulkUpdateSpaceSerializer` and `BulkDeleteSpaceSerializer` |
| `core/views.py` | Added `bulk_update` and `bulk_delete` actions; refactored `bulk_create` to wrap validation inside `transaction.atomic()` |

---

## Testing

Run the test script:
```bash
bash test_bulk_operations.sh
```
