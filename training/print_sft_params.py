from trl import SFTConfig
import inspect

sig = inspect.signature(SFTConfig.__init__)
print("Parameters in SFTConfig:")
for p in sig.parameters:
    print(p)
