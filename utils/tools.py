# -*- coding: utf-8 -*-
import os, time, sys
from logging import info, debug
from datetime import datetime
from pylibs.utils.text import toUnicode

def kill_process(mask):
    c = 0
    tPid = str(os.getpid())
    command = "ps aux | grep '"+str(mask)+"' | grep -v 'defunct' | grep -v grep | grep -v "+str(tPid)+""
    info("kill_process command: %s" % command)
    processes = os.popen(command).read().strip()
    info("kill_process processes: %s" % processes)
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
        info("processecControl command: %s" % command)
        processes = os.popen(command).read().strip()
        info("processecControl processes: %s" % processes)
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



def rus_date_to_datetime(dt_str):
    u"""Работает с форматом "1 января 2018"
    """
    dt_str = toUnicode(dt_str)
    dt_str_list = dt_str.strip().split(" ")
    if len(dt_str_list) != 3:
        raise ValueError("Bad format of date: %s" % dt_str)
    month_name = dt_str_list[1].strip()
    monthes = {u"января":'01', u"февраля":'02', u"марта":'03', u"апреля":'04', u"мая":'05', u"июня":'06', u"июля":'07', u"августа":'08', u"сентября":'09', u"октября":'10', u"ноября":'11', u"декабря":'12'}
    return datetime.strptime(dt_str.replace(month_name, monthes[month_name]), "%d %m %Y").date()