'''

   © 2025 Western Australian Land Information Authority

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


def LSA(A, x, P=None):
    A = np.array(A)
    x = np.array(x)
    if P:
        P = np.array(P)
    else:
        P = np.eye(A.shape[0])
    dof = len(A) - len(A.T)
    # (ISO 17123-4:2012 eq.11 & 12 & 15)
    try:
        # the cofactor matrix of the unknown parameters
        # Rueger 1984e eq 27
        Q = np.linalg.inv(A.T @ P @ A)
    except:
        # Return None for Singular matrix and not enough observations.
        return None, None, None, None
    # Rueger 1984e eq 23
    y = (Q @ A.T @ P @ x)

    # (ISO 17123-4:2012 eq.9) & Rueger 1984e eq 24b
    r = A @ y - x
    # (Baseline Eq eq.7.2) & Rueger 1984e eq 25
    # the a posteriori variance factor
    variance_factor = (r.T @ P @ r) / dof
    # variance-covariance matrix of parameters
    vcv = variance_factor * Q
    
    # (ISO 17123-4:2012 eq.14 & Baseline Eq eq.7.5)
    # Make sure that the Weight matrix is scaled so that max value is 1.
    # Ghilani (2017) 16.10 & Example 16.6 (4)
    W = P / np.max(P)
    So = sqrt((r.T @ W @ r) / dof)

    # Standard residuals
    # (Baseline Eq eq.7.15)
    sigma_vv = np.linalg.inv(P) - A @ Q @ A.T
    std_residuals = r / np.sqrt(np.diagonal(sigma_vv))

    # chi-squared test
    chi_upper = max((dof * variance_factor) / chi2.ppf(0.975, dof),
                    (dof * variance_factor) / chi2.ppf(0.025, dof))
    chi_lower = min((dof * variance_factor) / chi2.ppf(0.975, dof),
                    (dof * variance_factor) / chi2.ppf(0.025, dof))
    lsa_stats = {'chi_lower': chi_lower,
                'So': So,
                'Variance': variance_factor,
                'variance_covariance':vcv,
                'chi_upper': chi_upper,
                'dof': dof,
                'k': t.ppf(1 - 0.025, df=dof)}
    if chi_lower < variance_factor and variance_factor < chi_upper:
        lsa_stats['test'] = 'Passes'
    else:
        lsa_stats['test'] = 'Fails'

    matrix_y = []
    # Statistical significance of the unknown parameters
    # ref ISO 17123:4 eq 29 & Rueger 1984e eq 27
    critical_t = t.ppf(1 - 0.025, df=dof)
    for vlue, v2 in zip(y, np.diagonal(Q)):
        hypothesis = '%s <= %s' % (float('%.2g' % abs(vlue)),
                                    float('%.2g' % (So * sqrt(v2) * critical_t)))
        t_test = abs(vlue) <= (So * sqrt(v2) * critical_t)

        matrix_y.append({
            'value': vlue,
            'std_dev': sqrt(variance_factor) * sqrt(v2),   # ref Ghilani (2017) 16.11
            'uncertainty': sqrt(variance_factor) * sqrt(v2) * lsa_stats['k'],
            'hypothesis': hypothesis,
            't_test': t_test})
    
    residuals = np.vstack((r, std_residuals)).T
    residuals = list2dict(residuals.tolist(), ['residual', 'std_residual'])

    return matrix_y, Q, lsa_stats, residuals


def ISO_test_a(Insts, lsa_stats, Rnge=[{'distance': 100}]):
    try:
        # Please note the database units for specifications are in mm
        k0 = float(Insts.edm.edm_specs.manu_unc_k)
        ppm = float(Insts.edm.edm_specs.manu_unc_ppm) / k0
        c0 = (float(Insts.edm.edm_specs.manu_unc_const)/1000) / k0
        k1 = float(Insts.prism.prism_specs.manu_unc_k)
        c1 = (float(Insts.prism.prism_specs.manu_unc_const)/1000) / k1
        dof = lsa_stats['dof']
        
        for d in Rnge:
            edm_spec = c0 + d['distance'] * ppm /1000000
            d['Manu_Spec'] = sqrt( c1**2 + edm_spec**2)
            # ref ISO 17123:4 eq 21
            d['test_value'] = sqrt(chi2.ppf(0.95, dof) / dof) * d['Manu_Spec']
            d['accept'] = lsa_stats['So'] < d['test_value']
        test_a = {
            'test': 'A',
            'hypothesis': 'The experimental standard deviation, s, is smaller than or equal to the manufacturers specifications for the Instrument and prism combination.',
            'test_ranges': Rnge,
            'accept': False not in [a['accept'] for a in Rnge]
        }
    except Exception as e:
        test_a = {
            'test': 'A',
            'hypothesis': f'Insufficient instrumentation parameters suppllied to complete Test A: {e}',
            'test_ranges': '',
            'accept': False
        }
    
    return test_a


def ISO_test_b(prev_lsa_stats, lsa_stats):
    if (lsa_stats['dof'] == prev_lsa_stats['dof']
        and lsa_stats['So'] and prev_lsa_stats['So']):
        test_value = (lsa_stats['So']**2) / (prev_lsa_stats['So']**2)
        lower_lmt = 1 / (f.ppf(0.975, lsa_stats['dof'], lsa_stats['dof']))
        upper_lmt = f.ppf(0.975, lsa_stats['dof'], lsa_stats['dof'])
        test_b = {
            'test': 'B',
            'hypothesis': 'The experimental standard deviation, s belong to the same population as the standard deviation obtained in the previous report for this instrumentation',
            'accept': lower_lmt <= test_value <= upper_lmt
        }
    else:
        test_b = {
            'test': 'B',
            'hypothesis': 'Test could not be performed because the two samples have different degrees of freedom',
            'accept': ''
        }
    return test_b


def ISO_test_c(zpc, zpc_std_dev, lsa_stats):
    exp_std_dev = lsa_stats['So']
    try:
        std_uc = zpc_std_dev * exp_std_dev
        test_value = t.ppf(0.975, lsa_stats['dof']) * std_uc
        test_c = {
            'test': 'C',
            'hypothesis': (
                'The zero-point correction, δ, is equal to zero \n'
                + f'zero-point correction: {round(zpc,5)}m \n'
                + f'zero-point correction standard deviation: {round(zpc_std_dev,5)}m'),
            'accept': zpc <= test_value
        }
    except:
        test_c = {
            'test': 'C',
            'hypothesis': 'Test could not be performed.',
            'accept': ''
        }
    return test_c

# References
# Rüeger, J. M. 1996. Electronic Distance Measurement - An Introduction, 4th corrected edition, 
# Springer-Verlag, Berlin-Heidelberg, xix+276 pages, ISBN 978-3-540-61159-2 (softcover), 
# ISBN 978-3-642-80233-1 (eBook) (https://www.springer.com/gp/book/9783540611592) [Rue1996a]

# Rüeger, J.M., 1984e. Instructions on the Verification of Electrooptical Short Range Distance 
# Meters on Subsidiary Standards of Length in the Form of EDM Calibration Baselines.
# April, 1984, 63 pages  [Rue1984e]

# Ghilani, Charles D., & Wolf, Paul R. (2017). Elementary Surveying - An introduction to geomatics (15th edition)

# Ghilani Charles D. (2010) Adjustment Computations Spatial Data Analysis 4th Edition

# ISO. 2012. Field Procedures for Testing Geodetic and Surveying Instruments – Part 4: 
# Electro-Optical Distance Meters (EDM Measurements to Reflectors), ISO 17123-4:2012(E), 
# International Organization for Standardization, Geneva, Switzerland, 22 pages.