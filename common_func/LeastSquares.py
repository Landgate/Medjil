'''

   © 2023 Western Australian Land Information Authority

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

'''
import numpy as np
from math import sqrt
from scipy.stats.distributions import chi2
from scipy.stats import t, f
from common_func.Convert import list2dict


def LSA(A, x, P):
    A = np.array(A)
    x = np.array(x)
    P = np.array(P)
    dof = len(A) - len(A.T)
    # (ISO 17123-4:2012 eq.11 & 12 & 15)
    Q = np.linalg.inv(A.T @ P @ A)
    y = (Q @ A.T @ P @ x)

    # (ISO 17123-4:2012 eq.9)
    r = A @ y - x
    # (Baseline Eq eq.7.2)
    variance_factor = (r.T @ P @ r) / dof
    # (ISO 17123-4:2012 eq.14 & Baseline Eq eq.7.5)
    So = sqrt((r.T @ r) / dof)

    # Standard residuals
    # (Baseline Eq eq.7.15)
    sigma_vv = np.linalg.inv(P) - A @ Q @ A.T
    std_residuals = r / np.sqrt(np.diagonal(sigma_vv))

    # chi-squared test
    chi_upper = max((dof * variance_factor) / chi2.ppf(0.975, dof),
                    (dof * variance_factor) / chi2.ppf(0.025, dof))
    chi_lower = min((dof * variance_factor) / chi2.ppf(0.975, dof),
                    (dof * variance_factor) / chi2.ppf(0.025, dof))
    chi_test = {'chi_lower': chi_lower,
                'So': So,
                'Variance': variance_factor,
                'chi_upper': chi_upper,
                'dof': dof,
                'k': t.ppf(1 - 0.025, df=dof)}
    if chi_lower < variance_factor and variance_factor < chi_upper:
        chi_test['test'] = 'Passes'
    else:
        chi_test['test'] = 'Fails'

    matrix_y = []
    # ref ISO 17123:4 eq 29
    critical_t = t.ppf(1 - 0.025, df=dof)
    for vlue, v2 in zip(y, np.diagonal(Q)):
        hypothesis = '%s <= %s' % (float('%.2g' % abs(vlue)),
                                    float('%.2g' % (So * sqrt(v2) * critical_t)))
        t_test = abs(vlue) <= (So * sqrt(v2) * critical_t)

        matrix_y.append({
            'value': vlue,
            'std_dev': sqrt(v2),
            'uncertainty':sqrt(v2) * chi_test['k'],
            'hypothesis': hypothesis,
            't_test': t_test})
    
    residuals = np.vstack((r, std_residuals)).T
    residuals = list2dict(residuals.tolist(), ['residual', 'std_residual'])

    return matrix_y, Q, chi_test, residuals


def ISO_test_a(Insts, chi_test, Rnge=[{'distance': 100}]):
    k0 = float(Insts['edm'].edm_specs.manu_unc_k)
    ppm = float(Insts['edm'].edm_specs.manu_unc_ppm) / k0
    c0 = float(Insts['edm'].edm_specs.manu_unc_const) / k0
    k1 = float(Insts['prism'].prism_specs.manu_unc_k)
    c1 = float(Insts['prism'].prism_specs.manu_unc_const) / k1
    dof = chi_test['dof']
    # Convert So to mm
    # ISO 17123:4-2012 B.3 Calculation 
    # Please note the worked example converts the So to mm. The value of 
    So = chi_test['So'] /1000
    
    for d in Rnge:
        d['Manu_Spec'] = (
            sqrt( c1**2 + (c0 + d['distance'] * ppm / 1000)**2)) / 1000
        d['test_value'] = (chi2.ppf(0.95, dof) / dof) * d['Manu_Spec']
        d['accept'] = So < d['test_value']
    test_a = {
        'test': 'A',
        'hypothesis': 'The experimental standard deviation, s, is smaller than or equal to the manufacturers specifications for the Instrument and prism combination.',
        'test_ranges': Rnge,
        'accept': False not in [a['accept'] for a in Rnge]
    }
    return test_a


def ISO_test_b(prev_chi_test, chi_test):
    if chi_test['dof'] == prev_chi_test['dof']:
        test_value = chi_test['Variance'] / prev_chi_test['Variance']
        lower_lmt = 1 / (f.ppf(0.975, chi_test['dof'], chi_test['dof']))
        upper_lmt = f.ppf(0.975, chi_test['dof'], chi_test['dof'])
        test_b = {
            'test': 'B',
            'hypothesis': 'The standard deviation, s belong to the same population as the standard deviation obtained in the previous report for this instrumentation',
            'accept': lower_lmt <= test_value <= upper_lmt
        }
    else:
        test_b = {
            'test': 'B',
            'hypothesis': 'Test could not be performed because the two samples have different degrees of freedom',
            'accept': ''
        }
    return test_b


def ISO_test_c(zpc, zpc_std_dev, chi_test):
    exp_std_dev = sqrt(chi_test['Variance'])
    std_uc = zpc_std_dev * exp_std_dev
    test_value = t.ppf(0.975, chi_test['dof']) * std_uc
    test_c = {
        'test': 'C',
        'hypothesis': (
            'The zero-point correction, δ, is equal to zero \n'
            + f'zero-point correction: {round(zpc,5)}m \n'
            + f'zero-point correction standard deviation: {round(zpc_std_dev,5)}m'),
        'accept': zpc <= test_value
    }
    return test_c

