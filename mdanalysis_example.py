"""
Example code to demonstrate aligning a trajectory to a reference structure and
calculating the rmsd using PyQCPROT

Requires MDAnalysis
http://code.google.com/p/mdanalysis

"""

import numpy
import MDAnalysis as mda
from MDAnalysis.tests.datafiles import PSF, DCD, PDB_small
import pyqcprot as qcp

ref = mda.Universe(PSF, PDB_small)   # reference structure 1AKE
traj = mda.Universe(PSF, DCD)         # trajectory of change 1AKE->4AKE

# align using the backbone atoms
select = 'backbone'
selections = {'reference':select,'target':select}

frames = traj.trajectory
nframes = len(frames)
rmsd = numpy.zeros((nframes,))

# Setup writer to write aligned dcd file
writer = mda.coordinates.DCD.DCDWriter(
    'rmsfit.dcd',frames.numatoms,
    frames.start_timestep,
    frames.skip_timestep,
    frames.delta,
    remarks='RMS fitted trajectory to ref')

ref_atoms = ref.selectAtoms(selections['reference'])
traj_atoms = traj.selectAtoms(selections['target'])
natoms = traj_atoms.numberOfAtoms()

# if performing a mass-weighted alignment/rmsd calculation
#masses = ref_atoms.masses()
#weight = masses/numpy.mean(masses)

# reference centre of mass system
ref_com = ref_atoms.centerOfMass()
ref_coordinates = ref_atoms.coordinates() - ref_com

# allocate the array for selection atom coords
traj_coordinates = traj_atoms.coordinates().copy()

# R: rotation matrix that aligns r-r_com, x~-x~com
#    (x~: selected coordinates, x: all coordinates)
# Final transformed traj coordinates: x' = (x-x~_com)*R + ref_com
for k,ts in enumerate(frames):
    # shift coordinates for rotation fitting
    # selection is updated with the time frame
    x_com = traj_atoms.centerOfMass()
    traj_coordinates[:] = traj_atoms.coordinates() - x_com
    R = numpy.zeros((9,),dtype=numpy.float64)
    # Need to transpose coordinates such that the coordinate array is
    # 3xN instead of Nx3. Also qcp requires that the dtype be float64
    a = ref_coordinates.T.astype('float64')
    b = traj_coordinates.T.astype('float64')
    rmsd[k] = qcp.CalcRMSDRotationalMatrix(a,b,natoms,R,None)

    R = numpy.matrix(R.reshape(3,3))

    # Transform each atom in the trajectory (use inplace ops to avoid copying arrays)
    ts._pos   -= x_com
    ts._pos[:] = ts._pos * R # R acts to the left & is broadcasted N times.
    ts._pos   += ref_com
    writer.write(traj.atoms) # write whole input trajectory system

numpy.savetxt('rmsd.out',rmsd)
