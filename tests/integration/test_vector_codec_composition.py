import hashlib
import io

import numpy as np

from slaif_raggedized_helper.vector_codec import decode, encode


def test_numpy_writer_and_codec_consumer():
    matrix = np.zeros((1, 1024), dtype='<f4')
    matrix[0, 17] = 1
    buffer = io.BytesIO()
    np.lib.format.write_array(buffer, matrix, version=(1, 0), allow_pickle=False)
    data = buffer.getvalue()
    result = decode(data, hashlib.sha256(data).hexdigest())
    assert np.array_equal(encode(result.matrix).matrix, matrix)
