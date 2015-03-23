import sys
from mpi4py import MPI

def mpi_call(func,args,ncore=None):
    # the func should be in such form:
    # func(mpid,ncore,args)
    # where the args are tuples of arguments.


    def enum(*sequential, **named):
        """
        Handy way to fake an enumerated type in Python
        """
        enums = dict(zip(sequential, range(len(sequential))), **named)
        return type('Enum', (), enums)

    tags = enum('READY', 'DONE', 'EXIT', 'START')

    # Initializations and preliminaries
    comm = MPI.COMM_WORLD   # get MPI communicator object
    size = comm.size        # total number of processes
    rank = comm.rank        # rank of this process
    status = MPI.Status()   # get MPI status object

    if ncore == None:
        ncore = size

    if rank == 0:
        # Master process executes code below
        ntask = ncore-1
        task_index = 0
        num_workers = ncore - 1
        closed_workers = 0
        print("Master starting with %d workers" % num_workers)
        while closed_workers < num_workers:
            data = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
            source = status.Get_source()
            tag = status.Get_tag()
            if tag == tags.READY:
                # Worker is ready, so send it a task
                if task_index < ntask:
                    comm.send((task_index,ncore,args), dest=source, tag=tags.START)
                    print("Sending task %d to worker %d" % (task_index, source))
                    task_index += 1
                else:
                    comm.send(None, dest=source, tag=tags.EXIT)
            elif tag == tags.DONE:
                print("Got data from worker %d" % source)
            elif tag == tags.EXIT:
                print("Worker %d exited." % source)
                closed_workers += 1

        print("Master finishing")

    elif rank < ncore:

        # Worker processes execute code below
        name = MPI.Get_processor_name()
        print("I am a worker with rank %d on %s." % (rank, name))
        while True:
            comm.send(None, dest=0, tag=tags.READY)
            task = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
            tag = status.Get_tag()

            if tag == tags.START:
                # Do the work here
                mpid,ncore,args = task
                func(mpid,ncore,args)
                result = 0
                comm.send(result, dest=0, tag=tags.DONE)
            elif tag == tags.EXIT:
                break

        comm.send(None, dest=0, tag=tags.EXIT)

