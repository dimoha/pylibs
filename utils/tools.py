# -*- coding: utf-8 -*-
import os, time, sys
from logging import info, debug

def kill_process(mask):
    c = 0
    tPid = str(os.getpid())
    command = "ps aux | grep '"+str(mask)+"' | grep -v 'defunct' | grep -v grep | grep -v "+str(tPid)+""
    debug("kill_process command: %s" % command)
    processes = os.popen(command).read().strip()
    debug("kill_process processes: %s" % processes)
    for onestr in processes.split("\n"):
        try:
            thisStrPid = onestr.split()[1]
            if thisStrPid!=tPid:
                if mask in onestr:
                    c += 1
                    os.popen("kill -9 "+str(thisStrPid))
        except Exception as e:
            pass
    info('killed %s processes' % c)

def processecControl(name, numcopies, args = None, no_exit = False):


    cntRes = ['', '', '']
    all_processes = ''

    tPid = str(os.getpid())
    if args is not None:
        eArgs = []
        canCollect = False
        command = "ps aux | grep '"+str(name)+"' | grep -v grep | grep -v 'bin/sh' | grep -v "+str(tPid)
        debug("processecControl command: %s" % command)
        processes = os.popen(command).read().strip()
        debug("processecControl processes: %s" % processes)
        alist = processes.split(" ")
        for v in alist:
            v = v.strip()
            if v==name:
                canCollect = True
                continue
            if canCollect==True:
                eArgs.append(v)

        cntProcesses = 0
        for eArg in eArgs:
            if eArg in args:
                cntProcesses += 1
    else:

        cntRes = []
        for i in range(3):
            cntProcesses = os.popen( "ps aux | grep '"+str(name)+"' | grep -v grep | grep -v 'defunct' | grep -v 'bin/sh' | grep -v "+str(tPid)+" | wc -l").read().strip()
            cntRes.append(int(cntProcesses))
            time.sleep(0.1)

        cntProcesses = max(cntRes)


        cntSecondMethod = 0
        if cntProcesses==0:
            all_processes = os.popen("ps aux").read().strip()
            for onestr in all_processes.split("\n"):
                try:
                    thisStrPid = onestr.split()[1]
                    if thisStrPid!=tPid and 'bin/sh' not in onestr and 'defunct' not in onestr:
                        if name in onestr:
                            cntSecondMethod += 1
                except Exception as e:
                    pass
            cntProcesses = cntSecondMethod

    cntProcesses = int(cntProcesses)
    if cntProcesses>=int(numcopies):
        info("Process "+str(name)+" already exist.")
        if not no_exit:
            sys.exit(1)

    return cntProcesses
