import unittest
import numpy as np
from src.fantasy.simulation import simulate_counts,poisson_diagnostics


class SimulationTests(unittest.TestCase):
    def test_integer_draws_identities_and_expected_means(self):
        means=dict(shots=2.7,goals=.3,assists=.5,hits=1.,pp_points=.2)
        x=simulate_counts(means,draws=100000,key='player')
        for e,values in x.items():
            self.assertTrue(np.issubdtype(values.dtype,np.integer))
            self.assertTrue((values>=0).all())
            expected=means.get(e,.8)
            self.assertAlmostEqual(values.mean(),expected,delta=.025)
        self.assertTrue((x['goals']<=x['shots']).all())
        self.assertTrue((x['pp_points']<=x['points']).all())
        np.testing.assert_array_equal(x['points'],x['goals']+x['assists'])

    def test_reproducible_and_zero_means(self):
        means=dict(shots=0,goals=0,assists=0,hits=0,pp_points=0)
        a=simulate_counts(means,key='a'); b=simulate_counts(means,key='a')
        for e in a:
            np.testing.assert_array_equal(a[e],b[e])
            self.assertEqual(a[e].sum(),0)
        means['goals']=1
        with self.assertRaises(ValueError): simulate_counts(means)

    def test_poisson_diagnostic_reference(self):
        d=poisson_diagnostics([0,1],[1,1])
        self.assertAlmostEqual(d['mean_nll'],1)
        self.assertAlmostEqual(d['positive_mean_pearson_second_moment'],.5)
        zero=poisson_diagnostics([0,1],[0,0])
        self.assertEqual(zero['zero_mean_positive_actual'],1)
        self.assertTrue(np.isinf(zero['mean_nll']))


if __name__=='__main__': unittest.main()
