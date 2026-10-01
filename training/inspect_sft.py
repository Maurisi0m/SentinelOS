from trl import SFTConfig
import inspect

sig = inspect.signature(SFTConfig.__init__)
for name in sig.parameters:
    if any(k in name for k in ["seq", "len", "max"]):
        print("Param:", name)
