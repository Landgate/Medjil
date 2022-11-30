import numpy as np
from math import sqrt
from scipy.stats.distributions import chi2
from scipy.stats import t, f
from common_func.Convert import list2dict

def LSA(A, x, P):
    A = np.array(A)
    x = np.array(x)
    P = np.array(P)
    dof = len(A)-len(A.T)
    critical_t = t.ppf(1-0.025,df=dof)
    #(ISO 17123-4:2012 eq.11 & 12 & 15)
    Q = np.linalg.inv(A.T @ P @ A)
    y = (Q @ A.T @ P @ x)
        
    #(ISO 17123-4:2012 eq.9)
    r = A @ y - x
    #(ISO 17123-4:2012 eq.14)
    So = sqrt((r.T @ P @ r) / dof)
    
    #Standard residuals
    #(Baseline Eq eq.7.15)
    sigma_vv = np.linalg.inv(P) - A @ Q @ A.T
    std_residuals = r / np.sqrt(np.diagonal(sigma_vv))
    
    #chi-squared test
    chi_upper = max((dof * So**2) / chi2.ppf(0.975,dof),
                    (dof * So**2) / chi2.ppf(0.025,dof))
    chi_lower = min((dof * So**2) / chi2.ppf(0.975,dof),
                    (dof * So**2) / chi2.ppf(0.025,dof))
    chi_test = {'chi_lower':chi_lower,
                'Variance':So**2, 
                'chi_upper':chi_upper,
                'dof':dof,
                'k': t.ppf(1-0.025,df=dof)}
    if chi_lower < So**2 and So**2 < chi_upper:
        chi_test['test'] = 'Passes'
    else:
        chi_test['test'] = 'Fails'
    
    matrix_y=[]
    for v , v2 in zip(y, np.diagonal(Q)):
         matrix_y.append({'value':v, 
                          'std_dev':sqrt(v2),
                          't_value':abs(v)/sqrt(v2*So**2),
                          't_test':(abs(v)/sqrt(v2*So**2))<critical_t})

    residuals=np.vstack((r, std_residuals)).T
    residuals=list2dict(residuals.tolist(),['residual','std_residual'])

    return matrix_y, Q, chi_test, residuals

#ref ISO 17123:4 eq 21
def ISO_test_a(Insts, chi_test, Rnge=[{'distance':100}]):
    ppm = float(Insts['edm'].edm_specs.manu_unc_ppm)
    c = float(Insts['edm'].edm_specs.manu_unc_const)
    dof = chi_test['dof']
    exp_std_dev = sqrt(chi_test['Variance'])
    for d in Rnge:
        d['Manu_Spec'] =(c+d['distance']*ppm/1000)/1000
        d['test_value']=(chi2.ppf(0.95,dof)/dof)*d['Manu_Spec']
        d['accept'] = exp_std_dev<d['test_value']
    test_a = {'test':'A',
              'hypothesis':'The experimental standard deviation, s, is smaller than or equal to the manufacturers specifications',
              'test_ranges':Rnge,
              'accept':False not in [a['accept'] for a in Rnge]}
    
    return test_a


#ref ISO 17123:4 eq 25
def ISO_test_b(prev_chi_test, chi_test):
    if chi_test['dof'] == prev_chi_test['dof']:
        test_value = chi_test['Variance']/prev_chi_test['Variance']
        lower_lmt = 1/(f.ppf(0.975, chi_test['dof'], chi_test['dof']))
        upper_lmt = f.ppf(0.975, chi_test['dof'], chi_test['dof'])
        test_b={'test':'B',
                'hypothesis': 'The standard deviation, s belong to the same population as the standard deviation obtained in the previous report for this instrumentation',
                'accept': lower_lmt <= test_value <= upper_lmt}
    else:
        test_b={'test':'B',
                'hypothesis': 'Test could not be performed because the two samples have different degrees of freedom',
                'accept': ''}
    
    return test_b
        

#ref ISO 17123:4 eq 29
def ISO_test_c(zpc, zpc_std_dev, chi_test):
    exp_std_dev = sqrt(chi_test['Variance'])
    std_uc = zpc_std_dev * exp_std_dev
    test_value = chi2.ppf(0.975,chi_test['dof'])*std_uc
    test_c={'test':'C',
            'hypothesis': 'The zero-point correction, δ, is equal to zero',
            'accept': zpc <= test_value}
    
    return test_c
        
    
    
    