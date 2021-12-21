"""
HHL Benchmark Program - Qiskit
"""

import sys
import time

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

sys.path[1:1] = [ "_common", "_common/qiskit" ]
sys.path[1:1] = [ "../../_common", "../../_common/qiskit" ]
import execute as ex
import metrics as metrics

np.random.seed(0)

verbose = False

# Variable for number of resets to perform after mid circuit measurements
num_resets = 1

# saved circuits for display
QC_ = None
Uf_ = None

############### Circuit Definition
'''
def create_oracle(num_qubits, input_size, secret_int):
    # Initialize first n qubits and single ancilla qubit
    qr = QuantumRegister(num_qubits)
    qc = QuantumCircuit(qr, name=f"Uf")

    # perform CX for each qubit that matches a bit in secret string
    s = ('{0:0' + str(input_size) + 'b}').format(secret_int)
    for i_qubit in range(input_size):
        if s[input_size - 1 - i_qubit] == '1':
            qc.cx(qr[i_qubit], qr[input_size])
    return qc
'''   

   
def qft_dagger(qc, clock, n):      
    qc.h(clock[1]);
    for j in reversed(range(n)):
      for k in reversed(range(j+1,n)):
        qc.cu1(-np.pi/float(2**(k-j)), clock[k], clock[j]);
    qc.h(clock[0]);
    qc.swap(clock[0], clock[1]);

def qft(qc, clock, n):
    qc.swap(clock[0], clock[1]);
    qc.h(clock[0]);
    for j in reversed(range(n)):
      for k in reversed(range(j+1,n)):
        qc.cu1(np.pi/float(2**(k-j)), clock[k], clock[j]);
    qc.h(clock[1]);
 
def qpe(qc, clock, target):
    qc.barrier()

    # e^{i*A*t}
    qc.cu(np.pi/2, -np.pi/2, np.pi/2, 3*np.pi/4, clock[0], target, label='U');
    
    # e^{i*A*t*2}
    qc.cu(np.pi, np.pi, 0, 0, clock[1], target, label='U2');

    qc.barrier();
    
    # Perform an inverse QFT on the register holding the eigenvalues
    qft_dagger(qc, clock, 2)
    
def inv_qpe(qc, clock, target):
    
    # Perform a QFT on the register holding the eigenvalues
    qft(qc, clock, 2)

    qc.barrier()

    # e^{i*A*t*2}
    qc.cu(np.pi, np.pi, 0, 0, clock[1], target, label='U2');

    # e^{i*A*t}
    qc.cu(np.pi/2, np.pi/2, -np.pi/2, -3*np.pi/4, clock[0], target, label='U');

    qc.barrier()

def hhl_routine(qc, ancilla, clock, input, measurement):
    
    qpe(qc, clock, input)

    qc.barrier()
    
    # This section is to test and implement C = 1
    qc.cry(np.pi, clock[0], ancilla)
    qc.cry(np.pi/3, clock[1], ancilla)

    qc.barrier()
    
    qc.measure(ancilla, measurement[0])
    qc.barrier()
    inv_qpe(qc, clock, input)
    


def HHL (num_qubits, secret_int, beta, method = 1):
    
    # Create the various registers needed
    clock = QuantumRegister(2, name='clock')
    input = QuantumRegister(1, name='b')
    ancilla = QuantumRegister(1, name='ancilla')
    measurement = ClassicalRegister(2, name='c')

    # Create an empty circuit with the specified registers
    qc = QuantumCircuit(ancilla, clock, input, measurement)

    # size of input is one less than available qubits
    input_size = num_qubits - 1

    if method == 1:
        # allocate qubits
        '''
        qr = QuantumRegister(num_qubits); cr = ClassicalRegister(input_size); qc = QuantumCircuit(qr, cr, name="main")

        # put ancilla in |1> state
        qc.x(qr[input_size])

        # start with Hadamard on all qubits, including ancilla
        for i_qubit in range(num_qubits):
             qc.h(qr[i_qubit])

        qc.barrier()

        #generate Uf oracle
        Uf = create_oracle(num_qubits, input_size, secret_int)
        qc.append(Uf,qr)

        qc.barrier()

        # start with Hadamard on all qubits, including ancilla
        for i_qubit in range(num_qubits):
             qc.h(qr[i_qubit])

        # uncompute ancilla qubit, not necessary for algorithm
        qc.x(qr[input_size])

        qc.barrier()

        # measure all data qubits
        for i in range(input_size):
            qc.measure(i, i)

        global Uf_
        if Uf_ == None or num_qubits <= 6:
            if num_qubits < 9: Uf_ = Uf
        '''
        qc.barrier()
        
        # State preparation. (various initial values)
        # intial_state = [0,1]
        # intial_state = [1,0]
        # intial_state = [1/np.sqrt(2),1/np.sqrt(2)]
        # intial_state = [np.sqrt(0.9),np.sqrt(0.1)]
        
        ##intial_state = [np.sqrt(1 - beta), np.sqrt(beta)]
        ##qc.initialize(intial_state, 3)
        
        # use an RY rotation to initialize the input state between 0 and 1
        qc.ry(2 * np.arcsin(np.sqrt(beta)), input)

        ##qc.barrier()

        # Put clock qubits into uniform superposition
        qc.h(clock)

        hhl_routine(qc, ancilla, clock, input, measurement)

        # Perform a Hadamard Transform
        qc.h(clock)

        qc.barrier()

        qc.measure(input, measurement[1])


    elif method == 2:
        # allocate qubits
        qr = QuantumRegister(2); cr = ClassicalRegister(input_size);
        qc = QuantumCircuit(qr, cr, name="main")

        # put ancilla in |-> state
        qc.x(qr[1])
        qc.h(qr[1])

        qc.barrier()

        # perform CX for each qubit that matches a bit in secret string
        s = ('{0:0' + str(input_size) + 'b}').format(secret_int)
        for i in range(input_size):
            if s[input_size - 1 - i] == '1':
                qc.h(qr[0])
                qc.cx(qr[0], qr[1])
                qc.h(qr[0])
            qc.measure(qr[0], cr[i])

            # Perform num_resets reset operations
            qc.reset([0]*num_resets)

    # save smaller circuit example for display
    global QC_
    if QC_ == None or num_qubits <= 6:
        if num_qubits < 9: QC_ = qc

    # return a handle on the circuit
    return qc

 
############### Result Data Analysis

saved_result = None

# Analyze and print measured results
# Expected result is always the secret_int, so fidelity calc is simple

# NOTE: for the hard-coded matrix A:  [ 1, -1/3, -1/3, 1 ]
#       x - y/3 = 1 - beta
#       -x/3 + y = beta
#  ==
#       x = 9/8 - 3*beta/4
#       y = 3/8 + 3*beta/4
#
#   and beta is stored as secret_int / 10000
#   This allows us to calculate the expected distribution
#
#   NOTE: we are not actually calculating the distribution, since it would have to include the ancilla
#   For now, we just return a distribution of only the 01 and 11 counts
#   Then we compare the ratios obtained with expected ratio to determine fidelity (incorrectly)

def compute_expectation(beta, num_shots):
    x = 9/8 - (3 * beta)/4
    y = 3/8 + (3 * beta)/4
    ratio = x / y
    ratio_sq = ratio * ratio
    #print(f"  ... x,y = {x, y} ratio={ratio} ratio_sq={ratio_sq}")
    
    iy = int(num_shots / (1 + ratio_sq))
    ix = num_shots - iy
    #print(f"    ... ix,iy = {ix, iy}")

    return { '01':ix, '11': iy }

def analyze_and_print_result (qc, result, num_qubits, secret_int, num_shots):
    global saved_result
    saved_result = result
    
    # obtain counts from the result object
    counts = result.get_counts(qc)
    if verbose: print(f"For secret int {secret_int} measured: {counts}")
    
    # compute beta from secret_int, and get expected distribution
    # compute ratio of 01 to 11 measurements for both expected and obtained
    beta = secret_int / 10000
    expected_dist = compute_expectation(beta, num_shots)
    #print(f"... expected = {expected_dist}")
    
    ratio_exp = expected_dist['01'] / expected_dist['11']
    ratio_counts = counts['01'] / counts['11']
    print(f"  ... ratio_exp={ratio_exp}  ratio_counts={ratio_counts}")
    
    # (NOTE: we should use this fidelity calculation, but cannot since we don't know actual expected)
    # use our polarization fidelity rescaling
    ##fidelity = metrics.polarization_fidelity(counts, expected_dist)
    
    # instead, approximate fidelity by comparing ratios
    if ratio_exp > ratio_counts:
        fidelity = ratio_counts / ratio_exp
    else:
        fidelity = ratio_exp / ratio_counts
    if verbose: print(f"  ... fidelity = {fidelity}")
    
    return counts, fidelity

################ Benchmark Loop

# Execute program with default parameters
def run (min_qubits=3, max_qubits=6, max_circuits=3, num_shots=100,
        backend_id='qasm_simulator', method = 1, provider_backend=None,
        hub="ibm-q", group="open", project="main", exec_options=None):

    print("HHL Benchmark Program - Qiskit")

    # validate parameters (smallest circuit is 4 qubits)
    max_qubits = max(4, max_qubits)
    min_qubits = min(max(4, min_qubits), max_qubits)
    #print(f"min, max qubits = {min_qubits} {max_qubits}")

    # Variable for new qubit group ordering if using mid_circuit measurements
    mid_circuit_qubit_group = []

    # If using mid_circuit measurements, set transform qubit group to true
    transform_qubit_group = True if method ==2 else False
    
    # Initialize metrics module
    metrics.init_metrics()

    # Define custom result handler
    def execution_handler (qc, result, num_qubits, s_int, num_shots):  
     
        # determine fidelity of result set
        num_qubits = int(num_qubits)
        counts, fidelity = analyze_and_print_result(qc, result, num_qubits, int(s_int), num_shots)
        metrics.store_metric(num_qubits, s_int, 'fidelity', fidelity)

    # Initialize execution module using the execution result handler above and specified backend_id
    ex.init_execution(execution_handler)
    ex.set_execution_target(backend_id, provider_backend=provider_backend,
            hub=hub, group=group, project=project, exec_options=exec_options)

    # for noiseless simulation, set noise model to be None
    # ex.set_noise_model(None)

    # Execute Benchmark Program N times for multiple circuit sizes
    # Accumulate metrics asynchronously as circuits complete
    for num_qubits in range(min_qubits, max_qubits + 1):
            
        # determine number of circuits to execute for this group
        num_circuits = min(2**(num_qubits), max_circuits)
        
        print(f"************\nExecuting [{num_circuits}] circuits with num_qubits = {num_qubits}")
        
        ''' 
        #beta range not calculated dynamically yet
        num_counting_qubits = 1
        
        # determine range of secret strings to loop over
        if 2**(num_counting_qubits) <= max_circuits:
            beta_range = [i/(2**(num_counting_qubits)) for i in list(range(num_circuits))]
        else:
            beta_range = [i/(2**(num_counting_qubits)) for i in np.random.choice(2**(num_counting_qubits), num_circuits, False)]
        '''
        
        # supply hard-coded beta array (during initial testing)
        beta_range = [ 1.0, 0.0, 0.9, 0.1, 0.8, 0.2 ]
        if max_circuits < len(beta_range): beta_range = beta_range[:max_circuits]   
        
        # loop over limited # of inputs for this
        for i in range(len(beta_range)):
            beta = beta_range[i]
            
            # create integer that represents beta to precision 4; use s_int as circuit id
            s_int = int(beta * 10000)
            print(f"  ... i={i} s_int={s_int}  beta={beta}")
            
            # create the circuit for given qubit size and secret string, store time metric
            ts = time.time()
            qc = HHL(num_qubits, s_int, beta, method)
            metrics.store_metric(num_qubits, s_int, 'create_time', time.time()-ts)

            # collapse the sub-circuit levels used in this benchmark (for qiskit)
            qc2 = qc.decompose()

            # submit circuit for execution on target (simulator, cloud simulator, or hardware)
            ex.submit_circuit(qc2, num_qubits, s_int, shots=num_shots)
        
        # Wait for some active circuits to complete; report metrics when groups complete
        ex.throttle_execution(metrics.finalize_group)
        
    # Wait for all active circuits to complete; report metrics when groups complete
    ex.finalize_execution(metrics.finalize_group)

    # print a sample circuit
    print("Sample Circuit:"); print(QC_ if QC_ != None else "  ... too large!")
    #if method == 1: print("\nQuantum Oracle 'Uf' ="); print(Uf_ if Uf_ != None else " ... too large!")

    # Plot metrics for all circuit sizes
    metrics.plot_metrics(f"Benchmark Results - HHL ({method}) - Qiskit",
                         transform_qubit_group = transform_qubit_group, new_qubit_group = mid_circuit_qubit_group)

# if main, execute method
if __name__ == '__main__': run()
   
