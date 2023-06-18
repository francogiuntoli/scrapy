import deeplake
import warnings

# warnings.warn(
#     "Hub is deprecated. Use Deep Lake instead:\n!pip install deeplake\nimport deeplake",
#     DeprecationWarning,
# )
globals().update(deeplake.__dict__)  # Forgive me
