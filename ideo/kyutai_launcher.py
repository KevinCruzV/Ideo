import sys

import mlx.core as mx

seed = int(sys.argv.pop(1))
_original = mx.random.seed
mx.random.seed = lambda _ignored: _original(seed)

from moshi_mlx import run_tts

sys.argv[0] = "run_tts"
run_tts.main()
