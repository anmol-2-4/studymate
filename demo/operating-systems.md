# Operating Systems — Unit 3 notes

A process is a program in execution. Each process has its own address space,
program counter, and open files. A thread is the smallest unit of CPU
scheduling; threads of the same process share the address space but have their
own stack and registers.

Deadlock occurs when a set of processes are blocked forever, each waiting for
a resource held by another. The four Coffman conditions required for deadlock
are: mutual exclusion, hold and wait, no preemption, and circular wait.
Deadlock can be prevented by breaking any one of these conditions. The
Banker's algorithm is a deadlock avoidance algorithm that checks whether
granting a request leaves the system in a safe state.

CPU scheduling algorithms: First Come First Serve (FCFS) is non-preemptive and
suffers from the convoy effect. Shortest Job First (SJF) gives minimum average
waiting time but needs burst-time prediction. Round Robin gives each process a
fixed time quantum and is preemptive — good for time-sharing systems. Priority
scheduling can cause starvation, which is solved by aging.

Virtual memory lets a process use more memory than physically available by
keeping only active pages in RAM. Paging divides memory into fixed-size frames
and pages; the page table maps virtual pages to physical frames. The TLB
(Translation Lookaside Buffer) caches page-table entries to speed up address
translation. A page fault occurs when a referenced page is not in memory, and
the OS loads it from disk. Thrashing happens when the system spends more time
paging than executing.
