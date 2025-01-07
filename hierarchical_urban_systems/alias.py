from typing import Union

import numpy as np
import scipy.sparse as sp  # type: ignore[import-untyped]

NodeCode = str
NodeName = str

FlowMatrix = Union[sp.spmatrix, np.ndarray]
