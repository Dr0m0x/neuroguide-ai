---
name: SHAP multi-class TreeExplainer output format
description: SHAP >= 0.45 changed the return shape for multi-class RF; must handle both old list and new 3D array.
---

In SHAP < 0.45, `TreeExplainer.shap_values(X)` for a multi-class RandomForest returns a **list** of arrays, one per class, each shape `(n_samples, n_features)`. Access: `shap_values[class_idx][sample_idx]`.

In SHAP >= 0.45, it returns a single **3D ndarray** of shape `(n_samples, n_features, n_classes)`. Access: `shap_values[sample_idx, :, class_idx]`.

**Why:** Breaking API change in SHAP 0.45 that caused "index N is out of bounds for axis 0 with size 1" runtime error in production.

**How to apply:** Always branch on `isinstance(shap_values, list)` before indexing:
```python
if isinstance(shap_values, list):
    class_shap = shap_values[pred_class][0]
else:
    class_shap = shap_values[0, :, pred_class]
```
