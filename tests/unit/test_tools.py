import pickle

import numpy as np
import pytest

import elfi


def test_vectorize_decorator():
    batch_size = 3
    a = np.array([1,2,3])
    b = np.array([3,2,1])

    @elfi.tools.vectorize
    def simulator(a, b, random_state=None, index_in_batch=None):
        return a*b

    assert np.array_equal(a * b, simulator(a, b, batch_size=batch_size))

    @elfi.tools.vectorize(constants=1)
    def simulator(a, constant, random_state=None, index_in_batch=None):
        return a*constant

    assert np.array_equal(a * 5, simulator(a, 5, batch_size=batch_size))

    @elfi.tools.vectorize(1)
    def simulator(a, constant, random_state=None, index_in_batch=None):
        return a*constant

    assert np.array_equal(a * 5, simulator(a, 5, batch_size=batch_size))

    @elfi.tools.vectorize(constants=(0, 2))
    def simulator(constant0, b, constant2, random_state=None, index_in_batch=None):
        return constant0*b*constant2

    assert np.array_equal(2 * b * 7, simulator(2, b, 7, batch_size=batch_size))

    # Invalid batch size in b
    with pytest.raises(ValueError):
        simulator(2, b, 7, batch_size=2*batch_size)


def simulator():
    pass


def test_vectorized_pickling():
    sim = elfi.tools.vectorize(simulator)
    pickle.dumps(sim)


def test_external_operation():
    # Note that the test string has intentionally not uniform formatting with spaces
    op = elfi.tools.external_operation('echo 1 {0} 4  5    6 {seed}')
    constant = elfi.Constant(123)
    simulator = elfi.Simulator(op, constant)
    v = simulator.generate(1)
    assert np.array_equal(v[:5], [1, 123, 4, 5, 6])

    # Can be pickled
    pickle.dumps(op)


@pytest.mark.usefixtures('with_all_clients')
def test_vectorized_and_external_combined():
    constant = elfi.Constant(123)
    kwargs_sim = elfi.tools.external_operation('echo {seed} {batch_index} {index_in_batch} {submission_index}',
                                               process_result='int32')
    kwargs_sim = elfi.tools.vectorize(kwargs_sim)
    sim = elfi.Simulator(kwargs_sim, constant)

    with pytest.raises(Exception):
        sim.generate(3)

    sim['_uses_meta'] = True
    g = sim.generate(3)

    # Test uniqueness of seeds
    assert len(np.unique(g[:, 0]) == 3)

    assert len(np.unique(g[:, 1]) == 1)

    # Test index_in_batch
    assert np.array_equal(g[:, 2], [0, 1, 2])

    # Test submission_index (all belong to the same submission)
    assert len(np.unique(g[:, 3]) == 1)


