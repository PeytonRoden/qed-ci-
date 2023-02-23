"""
Helper Classes for Cavity Quantum Electrodynamics Configuration Interaction methods.
Adapted from a helper class for Configuration Interaction by the Psi4Numpy Developers, specifically
Tianyuan Zhang, Jeffrey B. Schriber, and Daniel G. A. Smith.

References:
- Equations from [Szabo:1996], [Foley:2022], [Koch:2020]
"""

__authors__ = "Jonathan J. Foley IV"
__credits__ = ["Tianyuan Zhang", "Jeffrey B. Schriber", "Daniel G. A. Smith"]

__copyright__ = "(c) 2014-2023, The Psi4NumPy Developers, Foley Lab, Mapol Project"
__license__ = "GNU-GPL-3"
__date__ = "2023-01-21"

import psi4
from helper_cqed_rhf import cqed_rhf
from itertools import combinations

def compute_excitation_level(ket, ndocc):
    level = 0
    homo = ndocc-1
    for i in range(0, len(ket)):
        if ket[i] > homo:
            level += 1
    return level
def spin_idx_to_spat_idx_and_spin(P):
    """ function to take the numeric label of a spin orbital
        and return the spatial index and the spin index separately.
        Starts counting from 0:
        
        Arguments
        ---------
        P : int
            spin orbital label
        
        Returns
        -------
        [p, spin] : numpy array of ints
            p is the spatial orbital index and spin is the spin index.
            spin = 1  -> alpha
            spin = -1 -> beta
            
        Example
        -------
        >>> spin_idx_to_spat_idx_and_spin(0)
        >>> [0, 1]
        >>> spin_idx_to_spat_idx_and_spin(3)
        >>> [1, -1]
        
    """
    spin = 1
    if P % 2 == 0:
        p = P / 2
        spin = 1
    else:
        p = (P-1) / 2
        spin = -1
    return np.array([p, spin], dtype=int)


def map_spatial_to_spin(tei_spatial, I, J, K, L):
    """ function to take two electron integrals in the spatial orbital basis
        in chemist notation along with 4 indices I, J, K, L and return
        the corresponding two electron integral in the spin orbital basis
        in phycisit notation, <IJ||KL>
    
    """
    # Phys to Chem: <IJ||KL> -> [IK|JL] - [IL|JK]
    i_s = spin_idx_to_spat_idx_and_spin(I)
    k_s = spin_idx_to_spat_idx_and_spin(K)
    j_s = spin_idx_to_spat_idx_and_spin(J)
    l_s = spin_idx_to_spat_idx_and_spin(L)
    
    #print(i_s[1])
    # (ik|jl)
    spat_ikjl = tei_spatial[i_s[0], k_s[0], j_s[0], l_s[0]] * ( i_s[1] == k_s[1] ) *  ( j_s[1] == l_s[1] )
    
    # (il|jk)
    spat_iljk = tei_spatial[i_s[0], l_s[0], j_s[0], k_s[0]] * ( i_s[1] == l_s[1] ) *  ( j_s[1] == k_s[1] )
    
    return spat_ikjl - spat_iljk

def map_spatial_dipole_to_spin(mu, I, J, K, L):
    """ function to take the dipole matrix (a 1-electron matrix) 
        and return the product of dipole matrix elements such that it matches
        the <IJ||KL> convention.  
    
    """
    # Phys to Chem: <IJ||KL> -> [IK|JL] - [IL|JK]
    i_s = spin_idx_to_spat_idx_and_spin(I)
    k_s = spin_idx_to_spat_idx_and_spin(K)
    j_s = spin_idx_to_spat_idx_and_spin(J)
    l_s = spin_idx_to_spat_idx_and_spin(L)
    
    #print(i_s[1])
    # (ik|jl)
    spat_ikjl = mu[i_s[0], k_s[0]] * mu[j_s[0], l_s[0]] * ( i_s[1] == k_s[1] ) *  ( j_s[1] == l_s[1] )
    
    # (il|jk)
    spat_iljk = mu[i_s[0], l_s[0]] * mu[j_s[0], k_s[0]] * ( i_s[1] == l_s[1] ) *  ( j_s[1] == k_s[1] )
    
    return spat_ikjl - spat_iljk

       

class Determinant:
    """
    A class for a bit-Determinant.
    """

    def __init__(self, alphaObtBits=0, betaObtBits=0, alphaObtList=None, betaObtList=None):
        """
        Constructor for the Determinant
        """

        if alphaObtBits == 0 and alphaObtList != None:
            alphaObtBits = Determinant.obtIndexList2ObtBits(alphaObtList)
        if betaObtBits == 0 and betaObtList != None:
            betaObtBits = Determinant.obtIndexList2ObtBits(betaObtList)
        self.alphaObtBits = alphaObtBits
        self.betaObtBits = betaObtBits

    def getNumOrbitals(self):
        """
        Return the number of orbitals (alpha, beta) in this determinant
        """

        return Determinant.countNumOrbitalsInBits(self.alphaObtBits), Determinant.countNumOrbitalsInBits(
            self.betaObtBits)

    def getOrbitalIndexLists(self):
        """
        Return lists of orbital index
        """

        return Determinant.obtBits2ObtIndexList(self.alphaObtBits), Determinant.obtBits2ObtIndexList(self.betaObtBits)

    def getOrbitalMixedIndexList(self):
        """
        Return lists of orbital in mixed spin index alternating alpha and beta
        """

        return Determinant.obtBits2ObtMixSpinIndexList(self.alphaObtBits, self.betaObtBits)

    @staticmethod
    def countNumOrbitalsInBits(bits):
        """
        Return the number of orbitals in this bits
        """

        count = 0
        while bits != 0:
            if bits & 1 == 1:
                count += 1
            bits >>= 1
        return count

    @staticmethod
    def countNumOrbitalsInBitsUpTo4(bits):
        """
        Return the number of orbitals in this bits
        """

        count = 0
        while bits != 0 and count < 4:
            if bits & 1 == 1:
                count += 1
            bits >>= 1
        return count

    @staticmethod
    def obtBits2ObtIndexList(bits):
        """
        Return the corresponding list of orbital numbers from orbital bits
        """

        i = 0
        obts = []
        while bits != 0:
            if bits & 1 == 1:
                obts.append(i)
            bits >>= 1
            i += 1
        return obts

    @staticmethod
    def mixIndexList(alphaList, betaList):
        """
        Mix the alpha and beta orbital index list to one mixed list
        """

        return [elem * 2 for elem in alphaList] + [elem * 2 + 1 for elem in betaList]

    @staticmethod
    def obtBits2ObtMixSpinIndexList(alphaBits, betaBits):
        """
        Return the corresponding list of orbital numbers of orbital bits
        """

        alphaList, betaList = Determinant.obtBits2ObtIndexList(alphaBits), Determinant.obtBits2ObtIndexList(betaBits)
        return Determinant.mixIndexList(alphaList, betaList)

    @staticmethod
    def obtIndexList2ObtBits(obtList):
        """
        Return the corresponding orbital bits of list from orbital numbers
        """

        if len(obtList) == 0:
            return 0
        obtList = sorted(obtList, reverse=True)
        iPre = obtList[0]
        bits = 1
        for i in obtList:
            bits <<= iPre - i
            bits |= 1
            iPre = i
        bits <<= iPre
        return bits

    @staticmethod
    def getOrbitalPositions(bits, orbitalIndexList):
        """
        Return the position of orbital in determinant
        """

        count = 0
        index = 0
        positions = []
        for i in orbitalIndexList:
            while index < i:
                if bits & 1 == 1:
                    count += 1
                bits >>= 1
                index += 1
            positions.append(count)
            continue
        return positions

    def getOrbitalPositionLists(self, alphaIndexList, betaIndexList):
        """
        Return the positions of indexes in lists
        """

        return Determinant.getOrbitalPositions(self.alphaObtBits, alphaIndexList), Determinant.getOrbitalPositions(
            self.betaObtBits, betaIndexList)

    def addAlphaOrbital(self, orbitalIndex):
        """
        Add an alpha orbital to the determinant
        """

        self.alphaObtBits |= 1 << orbitalIndex

    def addBetaOrbital(self, orbitalIndex):
        """
        Add an beta orbital to the determinant
        """

        self.betaObtBits |= 1 << orbitalIndex

    def removeAlphaOrbital(self, orbitalIndex):
        """
        Remove an alpha orbital from the determinant
        """

        self.alphaObtBits &= ~(1 << orbitalIndex)

    def removeBetaOrbital(self, orbitalIndex):
        """
        Remove an beta orbital from the determinant
        """

        self.betaObtBits &= ~(1 << orbitalIndex)

    def numberOfCommonOrbitals(self, another):
        """
        Return the number of common orbitals between this determinant and another determinant
        """

        return Determinant.countNumOrbitalsInBits(self.alphaObtBits &
                                                  another.alphaObtBits), Determinant.countNumOrbitalsInBits(
                                                      self.betaObtBits & another.betaObtBits)

    def getCommonOrbitalsInLists(self, another):
        """Return common orbitals between this determinant and another determinant in lists"""
        return Determinant.obtBits2ObtIndexList(self.alphaObtBits &
                                                another.alphaObtBits), Determinant.obtBits2ObtIndexList(
                                                    self.betaObtBits & another.betaObtBits)

    def getCommonOrbitalsInMixedSpinIndexList(self, another):
        alphaList, betaList = self.getCommonOrbitalsInLists(another)
        return Determinant.mixIndexList(alphaList, betaList)

    def numberOfDiffOrbitals(self, another):
        """
        Return the number of different alpha and beta orbitals between this determinant and another determinant
        """

        diffAlpha, diffBeta = Determinant.countNumOrbitalsInBits(
            self.alphaObtBits ^ another.alphaObtBits), Determinant.countNumOrbitalsInBits(
                self.betaObtBits ^ another.betaObtBits)
        return diffAlpha / 2, diffBeta / 2

    def numberOfTotalDiffOrbitals(self, another):
        """
        Return the number of different orbitals between this determinant and another determinant
        """

        diffAlpha, diffBeta = self.numberOfDiffOrbitals(another)
        return diffAlpha + diffBeta

    def diff2OrLessOrbitals(self, another):
        """
        Return true if two determinants differ 2 or less orbitals
        """

        diffAlpha, diffBeta = Determinant.countNumOrbitalsInBitsUpTo4(
            self.alphaObtBits ^ another.alphaObtBits), Determinant.countNumOrbitalsInBitsUpTo4(
                self.betaObtBits ^ another.betaObtBits)
        return (diffAlpha + diffBeta) <= 4

    @staticmethod
    def uniqueOrbitalsInBits(bits1, bits2):
        """
        Return the unique bits in two different bits
        """

        common = bits1 & bits2
        return bits1 ^ common, bits2 ^ common

    @staticmethod
    def uniqueOrbitalsInLists(bits1, bits2):
        """
        Return the unique bits in two different bits
        """

        bits1, bits2 = Determinant.uniqueOrbitalsInBits(bits1, bits2)
        return Determinant.obtBits2ObtIndexList(bits1), Determinant.obtBits2ObtIndexList(bits2)

    def getUniqueOrbitalsInLists(self, another):
        """
        Return the unique orbital lists in two different determinants
        """

        alphaList1, alphaList2 = Determinant.uniqueOrbitalsInLists(self.alphaObtBits, another.alphaObtBits)
        betaList1, betaList2 = Determinant.uniqueOrbitalsInLists(self.betaObtBits, another.betaObtBits)
        return (alphaList1, betaList1), (alphaList2, betaList2)

    def getUnoccupiedOrbitalsInLists(self, nmo):
        """
        Return the unoccupied orbitals in the determinants
        """

        alphaBits = ~self.alphaObtBits
        betaBits = ~self.betaObtBits
        alphaObts = []
        betaObts = []
        for i in range(nmo):
            if alphaBits & 1 == 1:
                alphaObts.append(i)
            alphaBits >>= 1
            if betaBits & 1 == 1:
                betaObts.append(i)
            betaBits >>= 1
        return alphaObts, betaObts

    def getSignToMoveOrbitalsToTheFront(self, alphaIndexList, betaIndexList):
        """
        Return the final sign if move listed orbitals to the front
        """

        sign = 1
        alphaPositions, betaPositions = self.getOrbitalPositionLists(alphaIndexList, betaIndexList)
        for i in range(len(alphaPositions)):
            if (alphaPositions[i] - i) % 2 == 1:
                sign = -sign
        for i in range(len(betaPositions)):
            if (betaPositions[i] - i) % 2 == 1:
                sign = -sign
        return sign

    def getUniqueOrbitalsInListsPlusSign(self, another):
        """
        Return the unique orbital lists in two different determinants and the sign of the maximum coincidence determinants
        """

        alphaList1, alphaList2 = Determinant.uniqueOrbitalsInLists(self.alphaObtBits, another.alphaObtBits)
        betaList1, betaList2 = Determinant.uniqueOrbitalsInLists(self.betaObtBits, another.betaObtBits)
        sign1, sign2 = self.getSignToMoveOrbitalsToTheFront(alphaList1,
                                                            betaList1), another.getSignToMoveOrbitalsToTheFront(
                                                                alphaList2, betaList2)
        return (alphaList1, betaList1), (alphaList2, betaList2), sign1 * sign2

    def getUniqueOrbitalsInMixIndexListsPlusSign(self, another):
        """
        Return the unique orbital lists in two different determinants and the sign of the maximum coincidence determinants
        """

        (alphaList1, betaList1), (alphaList2, betaList2), sign = self.getUniqueOrbitalsInListsPlusSign(another)
        return Determinant.mixIndexList(alphaList1, betaList1), Determinant.mixIndexList(alphaList2, betaList2), sign

    def toIntTuple(self):
        """
        Return a int tuple
        """

        return (self.alphaObtBits, self.betaObtBits)

    @staticmethod
    def createFromIntTuple(intTuple):
        return Determinant(alphaObtBits=intTuple[0], betaObtBits=intTuple[1])

    def generateSingleExcitationsOfDet(self, nmo):
        """
        Generate all the single excitations of determinant in a list
        """

        alphaO, betaO = self.getOrbitalIndexLists()
        alphaU, betaU = self.getUnoccupiedOrbitalsInLists(nmo)
        dets = []

        for i in alphaO:
            for j in alphaU:
                det = self.copy()
                det.removeAlphaOrbital(i)
                det.addAlphaOrbital(j)
                dets.append(det)

        for k in betaO:
            for l in betaU:
                det = self.copy()
                det.removeBetaOrbital(k)
                det.addBetaOrbital(l)
                dets.append(det)

        return dets

    def generateDoubleExcitationsOfDet(self, nmo):
        """
        Generate all the double excitations of determinant in a list
        """

        alphaO, betaO = self.getOrbitalIndexLists()
        alphaU, betaU = self.getUnoccupiedOrbitalsInLists(nmo)
        dets = []

        for i in alphaO:
            for j in alphaU:
                for k in betaO:
                    for l in betaU:
                        det = self.copy()
                        det.removeAlphaOrbital(i)
                        det.addAlphaOrbital(j)
                        det.removeBetaOrbital(k)
                        det.addBetaOrbital(l)
                        dets.append(det)

        for i1, i2 in combinations(alphaO, 2):
            for j1, j2 in combinations(alphaU, 2):
                det = self.copy()
                det.removeAlphaOrbital(i1)
                det.addAlphaOrbital(j1)
                det.removeAlphaOrbital(i2)
                det.addAlphaOrbital(j2)
                dets.append(det)

        for k1, k2 in combinations(betaO, 2):
            for l1, l2 in combinations(betaU, 2):
                det = self.copy()
                det.removeBetaOrbital(k1)
                det.addBetaOrbital(l1)
                det.removeBetaOrbital(k2)
                det.addBetaOrbital(l2)
                dets.append(det)
        return dets

    def generateSingleAndDoubleExcitationsOfDet(self, nmo):
        """
        Generate all the single and double excitations of determinant in a list
        """

        return self.generateSingleExcitationsOfDet(nmo) + self.generateDoubleExcitationsOfDet(nmo)

    def copy(self):
        """
        Return a deep copy of self
        """

        return Determinant(alphaObtBits=self.alphaObtBits, betaObtBits=self.betaObtBits)

    def __str__(self):
        """
        Print a representation of the Determinant
        """
        a, b = self.getOrbitalIndexLists()
        return "|" + str(a) + str(b) + ">"


import numpy as np



class PFHamiltonianGenerator:
    """
    class for Full CI matrix elements
    """
    



    def __init__(self, N_photon, molecule_string, psi4_options_dict, lambda_vector,omega_val):
        """
        Constructor for matrix elements of the PF Hamiltonian
        """

        cqed_rhf_dict = cqed_rhf(lambda_vector, molecule_string, psi4_options_dict)
        print("RAN CQED-RHF!")
        print(cqed_rhf_dict["RHF ENERGY"])

        # get the psi4 wavefunction object
        p4_wfn = cqed_rhf_dict["PSI4 WFN"]
        # get the cqed-rhf MO coefficients
        C = cqed_rhf_dict["CQED-RHF C"]

        # collect rhf wfn object as dictionary
        wfn_dict = psi4.core.Wavefunction.to_file(p4_wfn)
        # update wfn_dict with orbitals from CQED-RHF
        wfn_dict["matrix"]["Ca"] = C
        wfn_dict["matrix"]["Cb"] = C
        # update wfn object
        p4_wfn = psi4.core.Wavefunction.from_file(wfn_dict)
        Ca = p4_wfn.Ca()
        nmo = p4_wfn.nmo() 
        # get 1-e arrays in ao basis
        self.d_ao = cqed_rhf_dict["d MATRIX IN AO BASIS"]

        self.q_ao = cqed_rhf_dict["q MATRIX IN AO BASIS"]
        self.H_core_ao = cqed_rhf_dict["H-CORE IN AO BASIS"]
        d_expectation_value = cqed_rhf_dict["d_E EXPECTATION VALUE"]

        # build H_spin
        #spatial part of 1-e integrals
        H_spin = np.einsum('uj,vi,uv', Ca, Ca, self.H_core_ao -d_expectation_value * self.d_ao + self.q_ao)
        H_spin= np.repeat(H_spin, 2, axis=0)
        H_spin = np.repeat(H_spin, 2, axis=1)
        #spin part of 1-e integrals 
        spin_ind = np.arange(H_spin.shape[0], dtype=np.int) % 2
        #product of spatial and spin parts
        H_spin *= (spin_ind.reshape(-1, 1) == spin_ind)

   
        # ERIs in spin-orbital basis in physicist convention
        mints = psi4.core.MintsHelper(p4_wfn.basisset())
        l_dot_mu_el_cmo = np.einsum('uj,vi,uv', Ca, Ca, self.d_ao)
        self.antiSym2eInt = np.asarray(mints.mo_spin_eri(Ca, Ca))
        nso = 2 * nmo
        TDI_spin = np.zeros((nso, nso, nso, nso))
        # get the dipole-dipole integrals in the spin-orbital basis with physicist convention
        for i in range(nso):
            for j in range(nso):
                for k in range(nso):
                    for l in range(nso):
                        TDI_spin[i, j, k, l] = map_spatial_dipole_to_spin(l_dot_mu_el_cmo, i, j, k, l)
                        
        # add dipole-dipole integrals to ERIs
        self.antiSym2eInt += TDI_spin
        
        #build g matrix
        g = -np.sqrt(omega_val / 2) * l_dot_mu_el_cmo
        g = np.repeat(g, 2, axis=0)
        g = np.repeat(g, 2, axis=1)
        #product of spatial and spin parts
        g *= (spin_ind.reshape(-1, 1) == spin_ind)
        
        self.Hspin = H_spin
        self.gspin = g 
        #self.antiSym2eInt = pf_mo_spin_eri
        #assert np.allclose(self.antiSym2eInt2, self.antiSym2eInt, 1e-12, 1e-12)

        self.omega = omega_val
        self.Np = N_photon


    def generatePFMatrix(self, detList):
        """
        Generate the Pauli-Fierz Hamiltonian matrix
        """
        numDet = len(detList)
        numP = self.Np + 1
        PF_H_Matrix = np.zeros((numP * numDet, numP * numDet))
        for s in range(numP):
            for i in range(numDet):
                si = s * numDet + i
                for t in range(numP):
                    for j in range(numDet):
                        tj = t * numDet + j

                        #print(F's:{s}, i:{i}, si:{si}, t:{t}, j:{j}, tj:{tj}')
                        # diagonal in electronic and photonic
                        if s==t and i==j:
                            PF_H_Matrix[si, tj] = self.calcMatrixElement_delta_s_t(detList[i], detList[j]) + self.omega * s
                        # diagonal in photonic only
                        elif s==t and i!=j:
                            PF_H_Matrix[si, tj] = self.calcMatrixElement_delta_s_t(detList[i], detList[j])

                        # diagonal in electronic, off-diagonal in photonic
                        elif s==t+1:
                            print(F'DiffIn1Phot -> s:{s}, i:{i}, si:{si}, t:{t}, j:{j}, tj:{tj}')
                            PF_H_Matrix[si, tj] = self.calcMatrixElement_delta_s_t_pm_1(detList[i], detList[j]) * np.sqrt(t+1)
                        elif s == t-1:
                            print(F'DiffIn1Phot -> s:{s}, i:{i}, si:{si}, t:{t}, j:{j}, tj:{tj}')
                            PF_H_Matrix[si, tj] = self.calcMatrixElement_delta_s_t_pm_1(detList[i], detList[j]) * np.sqrt(t)
                        

        return PF_H_Matrix
        

    def calcMatrixElement_delta_s_t(self, det1, det2):
        """
        Calculate a matrix element by two determinants assuming photonic bra is equal to photonic ket: <s|t> -> <s|s>
        """
        
        numUniqueOrbitals = None
        if det1.diff2OrLessOrbitals(det2):
            numUniqueOrbitals = det1.numberOfTotalDiffOrbitals(det2)
            if numUniqueOrbitals == 0:
                #print(F' cal matrix element for {det1} and {det2}\n')
                return self.calcMatrixElementIdentialDet(det1)
            if numUniqueOrbitals == 2:
                return self.calcMatrixElementDiffIn2(det1, det2)
            elif numUniqueOrbitals == 1:
                return self.calcMatrixElementDiffIn1(det1, det2)
            else:
                # 
                return 0.0
        else:
            return 0.0
    
    def calcMatrixElement_delta_s_t_pm_1(self, det1, det2):
        """
        Calculate a matrix element by two determinants assuming photonic bra 
        differs from photonic ket by \pm 1 (<s|b + b^\dagger|t> -> \delta_{s,t+1} + \delta_{s,t-1})
        """
        
        numUniqueOrbitals = None
        if det1.diff2OrLessOrbitals(det2):
            numUniqueOrbitals = det1.numberOfTotalDiffOrbitals(det2)
            if numUniqueOrbitals == 0:
                #print(F' cal matrix element for {det1} and {det2}\n')
                return self.calcMatrixElementDiffIn1phot(det1)
            if numUniqueOrbitals == 1:
                return self.calcMatrixElementDiffIn1el1phot(det1, det2)
            else:
                # 
                return 0.0
        else:
            return 0.0

    def calcMatrixElementDiffIn2(self, det1, det2):
        """
        Calculate a matrix element by two determinants where the determinants differ by 2 spin orbitals
        """

        unique1, unique2, sign = det1.getUniqueOrbitalsInMixIndexListsPlusSign(det2)
        return sign * self.antiSym2eInt[unique1[0], unique1[1], unique2[0], unique2[1]]

    def calcMatrixElementDiffIn1(self, det1, det2):
        """
        Calculate a matrix element by two determinants where the determinants differ by 1 spin orbitals
        """

        unique1, unique2, sign = det1.getUniqueOrbitalsInMixIndexListsPlusSign(det2)
        m = unique1[0]
        p = unique2[0]
        Helem = self.Hspin[m, p]
        common = det1.getCommonOrbitalsInMixedSpinIndexList(det2)
        Relem = 0.0
        for n in common:
            Relem += self.antiSym2eInt[m, n, p, n]
        return sign * (Helem + Relem)

    def calcMatrixElementDiffIn1el1phot(self, det1, det2):
        """
        Calculate a matrix element between two determinants where the determinants
        differ by 1 electronic spin orbital and 1 photon state...
        Note: Needs generalizing before we can do arbitrary photonic states
        """
        unique1, unique2, sign = det1.getUniqueOrbitalsInMixIndexListsPlusSign(det2)
        m = unique1[0]
        p = unique2[0]
        Gelem = self.gspin[m, p]

        return sign * Gelem

    def calcMatrixElementDiffIn1phot(self, det):
        """
        Calculate a matrix element between two determinants that are idetnical
        in the electronic spin orbital occupation and differ by 1 photon state....
        Note: Needs generalizing before we can do arbitrary photonic states
        """
        spinObtList = det.getOrbitalMixedIndexList()
        Gelem = 0.0
        for m in spinObtList:
            Gelem += self.gspin[m, m]
        return Gelem


    def calcMatrixElementIdentialDet(self, det):
        """
        Calculate a matrix element by two determinants where they are identical
        """

        spinObtList = det.getOrbitalMixedIndexList()
        Helem = 0.0
        for m in spinObtList:
            Helem += self.Hspin[m, m]
        length = len(spinObtList)
        Relem = 0.0
        for m in range(length - 1):
            for n in range(m + 1, length):
                Relem += self.antiSym2eInt[spinObtList[m], spinObtList[n], spinObtList[m], spinObtList[n]]
        return Helem + Relem
