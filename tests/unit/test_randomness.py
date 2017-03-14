import pytest

import numpy as np
import scipy.stats as ss

import elfi
from elfi.loader import get_sub_seed


def test_randomness(simple_model):
    k1 = simple_model['k1']

    gen1 = k1.generate(10)
    gen2 = k1.generate(10)

    assert not np.array_equal(gen1, gen2)


def test_global_random_state_usage(simple_model):
    n_gen = 10

    np.random.seed(0)
    k2 = simple_model['k2']
    k2.generate(n_gen)
    st1 = np.random.get_state()

    np.random.seed(0)
    mu = ss.uniform.rvs(0, 10, size=(n_gen, 1))
    ss.norm.rvs(mu, size=(n_gen, 3))
    st2 = np.random.get_state()

    assert random_state_equal(st1, st2)


def test_consistency_with_a_seed(simple_model):
    m = simple_model

    context = elfi.ComputationContext(seed=123)
    m.computation_context = context
    gen1 = elfi.get_client().compute_batch(m, 'k2')['k2']
    gen2 = elfi.get_client().compute_batch(m, 'k2')['k2']

    assert np.array_equal(gen1, gen2)


def test_different_states_for_different_batches(simple_model):
    m = simple_model

    context = elfi.ComputationContext(seed=123)
    m.computation_context = context
    gen1 = elfi.get_client().compute_batch(m, 'k2', batch_index=0)['k2']
    gen2 = elfi.get_client().compute_batch(m, 'k2', batch_index=1)['k2']

    assert not np.array_equal(gen1, gen2)


def test_get_sub_seed():
    n = 100
    rs = np.random.RandomState()
    state = rs.get_state()
    sub_seeds = []
    for i in range(n):
        rs.set_state(state)
        sub_seeds.append(get_sub_seed(rs, i, n))

    assert len(np.unique(sub_seeds)) == n


# Helpers


def random_state_equal(st1, st2):
    # 1. the string 'MT19937'.
    tf = st1[0] == st2[0]
    # 2. a 1-D array of 624 unsigned integer keys.
    tf = tf and np.array_equal(st1[1], st2[1])
    # 3. an integer ``pos``.
    tf = tf and st1[2] == st2[2]
    return tf