import os

from hypothesis import settings

settings.register_profile("ci", max_examples=120, deadline=None)
settings.register_profile("deep", max_examples=2000, deadline=None)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "ci"))
