import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != here]

import mlx.core as mx

seed = int(sys.argv.pop(1))
_original = mx.random.seed
mx.random.seed = lambda _ignored: _original(seed)

from moshi_mlx import run_tts

sys.argv[0] = "run_tts"
run_tts.main()
