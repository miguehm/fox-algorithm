import os
import numpy as np

from sys import argv
from mpi4py import MPI
from time import perf_counter

isLinux = os.name == 'posix'

if isLinux:
    from resource import getrusage, RUSAGE_SELF

exponent = int (argv[1])
isInt    = bool(argv[2])

comm = MPI.COMM_WORLD  # get the communicator object
size = comm.Get_size() # total number of processes
rank = comm.Get_rank() # rank of this process

if rank == 0: # if the process is the master 
    MATRIX_SIZE = 2**exponent
    # generate two random matrix of size MATRIX_SIZE
    if isInt:
        matrix_A    = np.random.randint(1_000, 2_000, (MATRIX_SIZE, MATRIX_SIZE)) 
        matrix_B    = np.random.randint(1_000, 2_000, (MATRIX_SIZE, MATRIX_SIZE)) 
        # initialize the matrix C with zeros
        matrix_C    = np.zeros((MATRIX_SIZE, MATRIX_SIZE), dtype=int)
    else:
        matrix_A    = np.random.uniform(1_000, 2_000, (MATRIX_SIZE, MATRIX_SIZE))
        matrix_B    = np.random.uniform(1_000, 2_000, (MATRIX_SIZE, MATRIX_SIZE))
        # initialize the matrix C with zeros
        matrix_C    = np.zeros((MATRIX_SIZE, MATRIX_SIZE))
    
    data = (MATRIX_SIZE, matrix_A, matrix_B, matrix_C)

else:
    data = None

data = comm.bcast(data, root=0)                  # broadcast the data to all processes
MATRIX_SIZE, matrix_A, matrix_B, matrix_C = data # unpack the data
start_time = perf_counter()

for x in range(MATRIX_SIZE): 
    # Each process calculates a row of the matrix C
    # The process with rank i calculates the row i of the matrix C
    # The row i of the matrix C is the sum of the rows of the matrix A multiplied by the matrix B

    # this ensures that each process calculates a row of the matrix C without repeating rows
    if rank == x % size: 
        for i in range(MATRIX_SIZE):
            # a[row_i, row_i] gets shifted to the right by i positions
            # and b[row_i] gets shifted to the bottom by i positions
            y = (x + i) % MATRIX_SIZE
            matrix_C[i] += matrix_A[i, y] * matrix_B[y] 

# The rows of the matrix C are distributed among the processes using the MPI_Allreduce function
# The MPI_Allreduce function sums the rows of the matrix C calculated by each process
comm.Allreduce(MPI.IN_PLACE, matrix_C, op=MPI.SUM)

if rank == 0:
    print(perf_counter() - start_time)
    print(getrusage(RUSAGE_SELF).ru_maxrss) if isLinux else print(0)