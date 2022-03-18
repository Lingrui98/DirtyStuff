import os
import sys
import os.path as osp
import datetime

import load_balance as lb
from common import local_config as lc
from cptdesc import CptBatchDescription
from emutasks import EmuTasksConfig

# `emu` 自动化测试

debug = False
# num_threads = 30
ver = '06'

emu_threads = 8

data_dir = f'{lc.cpt_top}/take_cpt/' # cpt dir
top_output_dir = '/home53/glr/spec_output/' # output dir

workload_filter = []
print(data_dir)
# exit()
cpt_desc = CptBatchDescription(data_dir, top_output_dir, ver,
        is_simpoint=True,
        is_uniform=False,
        simpoints_file=lc.simpoints_file[ver])

parser = cpt_desc.parser

parser.add_argument('-t', '--debug-tick', action='store', type=int)
parser.add_argument('-C', '--config', action='store', type=str)

parser.add_argument('--exe', action='store', type=str)
parser.add_argument('--threads', action='store', type=int)
parser.add_argument('--avoid-cores', action='store', type=str)
parser.add_argument('--selected-cores', action='store', type=str)


args = cpt_desc.parse_args()

if args.threads:
    emu_threads = args.threads

def extract_name(exe):
    assert(exe is not None)
    return exe.split('/')[-1]

# cores should be in type string
# cores should be in the format below
# [n|n-m][,[n|n-m]]*
def extract_cores(cores, prefix):
    assert(cores is not None)
    intervals = cores.split(',')
    res = []
    for i in intervals:
        start_to_end = i.split('-')
        if len(start_to_end) == 1:
            res += [int(start_to_end[0])]
        elif len(start_to_end) == 2:
            s, t = start_to_end
            assert(int(s) <= int(t))
            res += [c for c in range(int(s), int(t))]
        else:
            print(f"{prefix}_cores syntax error, input is {cores}")
            exit()
    res = list(set(res))
    print(res)
    return res

# print(args.avoid_cores)
avoid_cores = None
if args.avoid_cores:
    avoid_cores = extract_cores(args.avoid_cores, "avoid")
selected_cores = None
if args.selected_cores:
    selected_cores = extract_cores(args.selected_cores, "selected")
print(f"avoid cores:{avoid_cores}")
print(f"select cores:{selected_cores}")

# exit()

today=datetime.date.today()
CurConf = EmuTasksConfig
param = extract_name(args.exe)
task_name = f'xs_simpoint_batch/SPEC{ver}_{CurConf.__name__}_{param}_{str(today)}'
# task_name = f'xs_simpoint_batch/SPEC{ver}_{CurConf.__name__}_{param}_2021-10-06'
print(task_name)
cpt_desc.set_task_filter()
# cpt_desc.set_workload_blacklist(['mcf'])
cpt_desc.set_conf(CurConf, task_name)
cpt_desc.filter_tasks(hashed=True, n_machines=3)

cpt_desc.set_numactl(emu_threads=emu_threads, avoid_cores=avoid_cores, selected_cores=selected_cores)
# cpt_desc.set_numactl(emu_threads=emu_threads, avoid_cores=avoid_cores, selected_cores=None)
debug_tick = None

bp_list = [
    "perlbench", "povray", "astar", "gcc",
    "omnetpp", "mcf", "soplex", "bzip2",
    "namd", "sjeng", "hmmer", "xalancbmk", "sphinx3"
]

if args.debug_tick is not None:
    debug_tick = args.debug_tick
    debug_flags = frontend_flags + backend_flags


for task in cpt_desc.tasks:
    task.sub_workload_level_path_format()
    task.set_trivial_workdir()
    task.avoid_repeat = True

    task.add_direct_options([])
    task.add_dict_options({
        '-W': str(20*10**6),
        '-I': str(40*10**6),
        '-i': task.cpt_file,
        # '--gcpt-restorer': '/home/zyy/projects/NEMU/resource/gcpt_restore/build/gcpt.bin',
        # '--gcpt-warmup': str(50*10**6),
    })
    task.format_options(space=True)
print(f'Output dir {top_output_dir}/{task_name}')
valid_tasks = 0
for t in cpt_desc.tasks:
    if t.valid:
        # print(t.code_name)
        valid_tasks += 1
print(valid_tasks)
# exit()
cpt_desc.run(lb.get_machine_threads(), debug)

