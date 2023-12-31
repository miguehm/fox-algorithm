import os
import re
import typer
import cpuinfo
import platform
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from psutil import virtual_memory

global nthreads
isLinux = os.name == 'posix'

python_path = 'python3' if isLinux else 'python'

def run_mpi_file(mpi_file_path, exponent, isInt=True):
    global nthreads
    result = subprocess.run(['mpiexec', '-n', f'{nthreads}', python_path, mpi_file_path, f'{exponent}', f'{isInt}'], stdout=subprocess.PIPE, text=True)
    return result.stdout.splitlines()

def run_sec_file(sec_file_path, exponent, isInt=True):
    result = subprocess.run([python_path, sec_file_path, f'{exponent}', f'{isInt}'], stdout=subprocess.PIPE, text=True)  
    return result.stdout.splitlines()

def get_processor_info():
    if platform.system() == "Windows":
        return cpuinfo.get_cpu_info()['brand_raw']
    
    elif platform.system() == "Darwin":
        os.environ['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/sbin'
        command ="sysctl -n machdep.cpu.brand_string"
        return subprocess.check_output(command).strip()
    
    elif platform.system() == "Linux":
        command = "cat /proc/cpuinfo"
        all_info = subprocess.check_output(command, shell=True).decode().strip()
        for line in all_info.split("\n"):
            if "model name" in line:
                return re.sub( ".*model name.*:", "", line,1)
    return ""

def save_data(data, PROCESSOR, RAM, isInt):
    global nthreads
    times_MPI, times_SEC, memory_MPI, memory_SEC = data
    columns = ['exponent', 'time_mean', 'times', 'memory_mean', 'memory']
    datype = 'int' if isInt else 'float'
    if not os.path.exists(f'results/{PROCESSOR}_{nthreads}-Threads_{RAM}GB'):
        os.makedirs(f'results/{PROCESSOR}_{nthreads}-Threads_{RAM}GB')

    if os.path.exists(f'results/{PROCESSOR}_{nthreads}-Threads_{RAM}GB/data_{datype}.csv'):
        df = pd.read_csv(f'results/{PROCESSOR}_{nthreads}-Threads_{RAM}GB/data_{datype}.csv')

        df2 = pd.DataFrame(columns=columns)
        for exponent in times_MPI:
            df2.loc[0 if pd.isnull(df2.index.max()) else df2.index.max() + 1] = [f'{exponent} MPI', np.mean(times_MPI[exponent]), times_MPI[exponent], np.mean(memory_MPI[exponent]), memory_MPI[exponent]]
        for exponent in times_SEC:
            df2.loc[df2.index.max() + 1] = [f'{exponent} SEC', np.mean(times_SEC[exponent]), times_SEC[exponent], np.mean(memory_SEC[exponent]), memory_SEC[exponent]]
        df2[['t1','t2', 't3', 't4', 't5']] = pd.DataFrame(df2.times.tolist(), index= df2.index)
        df2[['m1','m2', 'm3', 'm4', 'm5']] = pd.DataFrame(df2.memory.tolist(), index= df2.index)
        df2.drop(columns=['times', 'memory'], inplace=True)

        df.set_index('exponent', inplace=True)
        df2.set_index('exponent', inplace=True)
        if df.index.max() > df2.index.max():
            df.update(df2)
        else:
            df2.update(df)
            df = df2

        df.to_csv(f'results/{PROCESSOR}_{nthreads}-Threads_{RAM}GB/data_{datype}.csv')
        
    else:
        df = pd.DataFrame(columns=columns)
        for exponent in times_MPI:
            df.loc[0 if pd.isnull(df.index.max()) else df.index.max() + 1] = [f'{exponent} MPI', np.mean(times_MPI[exponent]), times_MPI[exponent], np.mean(memory_MPI[exponent]), memory_MPI[exponent]]
        for exponent in times_SEC:
            df.loc[df.index.max() + 1] = [f'{exponent} SEC', np.mean(times_SEC[exponent]), times_SEC[exponent], np.mean(memory_SEC[exponent]), memory_SEC[exponent]]
        df[['t1','t2', 't3', 't4', 't5']] = pd.DataFrame(df.times.tolist(),  index= df.index)
        df[['m1','m2', 'm3', 'm4', 'm5']] = pd.DataFrame(df.memory.tolist(), index= df.index)
        df.drop(columns=['times', 'memory'], inplace=True)
        df.to_csv(f'results/{PROCESSOR}_{nthreads}-Threads_{RAM}GB/data_{datype}.csv', index=False)

def data(min_e, max_e=0, isInt=True):
    times_MPI  = {}
    times_SEC  = {}
    memory_MPI = {}
    memory_SEC = {}
    iterations = 5
    
    np.random.seed(69)  # set the seed for the random numbers generator
                        # so that the same numbers are generated in each process
    for exponent in range(min_e, max_e):
        times_MPI [exponent] = np.zeros(iterations)
        times_SEC [exponent] = np.zeros(iterations)
        memory_MPI[exponent] = np.zeros(iterations)
        memory_SEC[exponent] = np.zeros(iterations)
        print(f'Calculating for {2**exponent}...')
        for i in range(iterations):
            times_MPI[exponent][i], memory_MPI[exponent][i] = run_mpi_file('src/fox_MPI.py', exponent, isInt=isInt)
            times_SEC[exponent][i], memory_SEC[exponent][i] = run_sec_file('src/fox_SEC.py', exponent, isInt=isInt)

    return times_MPI, times_SEC, memory_MPI, memory_SEC

def create_dir(path, e_range, numtype):
    if not os.path.exists(path):
        os.makedirs(path)
    if not os.path.exists(f'{path}/{numtype}_executions'):
        os.makedirs(f'{path}/{numtype}_executions')
    return f'{path}/{numtype}_executions/{e_range}_{numtype}_fox.png'

def charts(min_e, max_e, isInt=True):

    times_MPI, times_SEC, memory_MPI, memory_SEC = data(min_e, max_e, isInt=isInt)

    PROCESSOR = get_processor_info()
    RAM = round(virtual_memory().total / 1024**3)

    save_data((times_MPI, times_SEC, memory_MPI, memory_SEC), PROCESSOR, RAM, isInt)

    y_Time_MPI   = [np.mean(times_MPI [exponent]) for exponent in times_MPI ]
    y_Time_SEC   = [np.mean(times_SEC [exponent]) for exponent in times_SEC ]
    y_Memory_MPI = [np.mean(memory_MPI[exponent]) for exponent in memory_MPI]
    y_Memory_SEC = [np.mean(memory_SEC[exponent]) for exponent in memory_SEC]
    
    bar_w = 0.35
    x_Time_MPI   = np.array([exponent - bar_w/2 for exponent in times_MPI ])
    x_Time_SEC   = np.array([exponent + bar_w/2 for exponent in times_SEC ])
    x_Memory_MPI = np.array([exponent - bar_w/2 for exponent in memory_MPI])
    x_Memory_SEC = np.array([exponent + bar_w/2 for exponent in memory_SEC])

    x_Labels = [str(2**exponent) for exponent in times_MPI]
    num_type = 'enteros' if isInt else 'reales'

    if isLinux:
        fig, (Time_ax, Memory_ax) = plt.subplots(1, 2, figsize=(20, 5))
    else:
        fig, Time_ax = plt.subplots(1, 1, figsize=(10, 5))
        
    plt.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.9, wspace=0.5, hspace=0.5)
    fig.suptitle(f'Comparación de las ejecuciones del algoritmo Fox con matrices de números {num_type}.\n{PROCESSOR} - {nthreads} Threads - {RAM}GB')
    
    Time_ax.set_title ('Gráfica de tiempos de ejecuciones secuenciales y paralelas.')
    Time_ax.set_xlabel('Orden de la Matriz')
    Time_ax.set_ylabel('Tiempo de ejecución (s)')
    Time_ax.set_xticks(x_Time_MPI + bar_w/2, x_Labels)
    Time_ax.set_yticks([]) 
    bars_Time_MPI = Time_ax.bar(x_Time_MPI, 
                                y_Time_MPI, 
                                bar_w, 
                                label='MPI',        
                                color='#EA75FA')
    bars_Time_SEC = Time_ax.bar(x_Time_SEC, 
                                y_Time_SEC, 
                                bar_w, 
                                label='Secuencial', 
                                color='#4590FA')
    
    for bar in bars_Time_SEC + bars_Time_MPI :
        x_pos   = bar.get_x() + bar.get_width()/2.0
        y_value = bar.get_height()
        Time_ax.text(
            x_pos, 
            y_value, 
            f'{y_value:5.5}s', 
            va='bottom', 
            ha='center')
    Time_ax.legend()

    if isLinux:
        Memory_ax.set_title ('Gráfica de memoria (RAM) utilizada en ejecuciones secuenciales y paralelas.')
        Memory_ax.set_xlabel('Orden de la Matriz')
        Memory_ax.set_ylabel('Memoria utilizada (MB)')
        Memory_ax.set_xticks(x_Memory_MPI + bar_w/2, x_Labels)
        Memory_ax.set_yticks([])
        bars_Memory_MPI = Memory_ax.bar(x_Memory_MPI, 
                                        y_Memory_MPI, 
                                        bar_w, 
                                        label='MPI',
                                        color='#EA75FA')
        bars_Memory_SEC = Memory_ax.bar(x_Memory_SEC, 
                                        y_Memory_SEC, 
                                        bar_w, 
                                        label='Secuencial', 
                                        color='#4590FA')
        
        for bar in bars_Memory_SEC + bars_Memory_MPI :
            x_pos   = bar.get_x() + bar.get_width()/2.0
            y_value = bar.get_height()
            Memory_ax.text(
                x_pos, 
                y_value, 
                f'{(y_value/1024):5.5}MB', 
                va='bottom', 
                ha='center')
        Memory_ax.legend()

    plt.tight_layout()
    fig.savefig(create_dir('charts', f'{2**(min_e)}-{2**(max_e-1)}', 'int' if isInt else 'float'))

def main(
        min_exp: int = typer.Option(6, help="Exponent of base 2 matrix order (2^)", rich_help_panel="Matrix order range"),
        max_exp: int = typer.Option(0, help="Exponent of base 2 matrix order (2^)", rich_help_panel="Matrix order range"),
        threads: int = typer.Option(4, help="Number of processes to use", rich_help_panel="Threads to use"),
    ):
        
        if min_exp > 11 or max_exp > 11: 
            response = input('This will take a long time to run. Are you sure you want to continue? (y/n)\n')
            if response.lower() != 'y': return

        max_e = max_exp + 1 if max_exp != 0 else min_exp + 1

        if min_exp > max_e:
            print('The maximum exponent must be greater than the minimum exponent.')
            return
        
        global nthreads
        nthreads = threads
        charts(min_exp, max_e, isInt=True)
        charts(min_exp, max_e, isInt=False)

    #* There are already some graphs generated in the graphs folder.

if __name__ == '__main__':
    typer.run(main)
