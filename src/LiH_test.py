import psi4
from helper_PFCI import PFHamiltonianGenerator
import numpy as np


mol_str = """
Li
H 1 1.4
symmetry c1
"""

options_dict = {
        "basis": "sto-3g",
        "scf_type": "pk",
        "e_convergence": 1e-10,
        "d_convergence": 1e-10,
}


cavity_dict = {
        'omega_value' : 0.,
        'lambda_vector' : np.array([0, 0, 0.0]),
        'ci_level' : 'fci',
        'number_of_photons' : 0,
        "full_diagonalization" : True
}

test_pf = PFHamiltonianGenerator(
        mol_str,
        options_dict,
        cavity_dict
)

test_pf.compute_1_and_2_electron_energy(0)
test_pf.compute_1_and_2_electron_energy(1)
test_pf.compute_1_and_2_electron_energy(2)
test_pf.compute_1_and_2_electron_energy(3)
test_pf.compute_1_and_2_electron_energy(4)
