import threading
import time
from source.funclib.err_code_lib import ERR_NONE
from source.util import *

class BaseThreading(threading.Thread):
    """
    基本线程类，实现了暂停线程、继续线程、终止线程。其他具体参考基本线程规范。
    """
    def __init__(self, thread_name = None):
        super().__init__()
        self.pause_threading_flag = False
        self.stop_threading_flag = False
        self.working_flag = False
        self.while_sleep = 0.2
        self.last_err_code = ERR_NONE
        self.stop_func_list = []
        self.sub_threading_list = []
        if thread_name != None:
            self.setName(thread_name)

    def pause_threading(self):
        if self.pause_threading_flag != True:
            logger.debug(f"{self.name} pause threading")
            self.pause_threading_flag = True

    def continue_threading(self):
        if self.pause_threading_flag != False:
            logger.debug(f"{self.name} continue threading")
            self.pause_threading_flag = False

    def stop_threading(self):
        self.stop_threading_flag = True
        for i in self.sub_threading_list:
            i.stop_threading()

    def checkup_stop_threading(self):
        if self.stop_threading_flag:
            return True

    def get_working_statement(self):
        return self.working_flag

    def checkup_stop_func(self):
        if self.pause_threading_flag or self.stop_threading_flag:
            return True
        for i in self.stop_func_list:
            if i():
                return True

    def add_stop_func(self, x):
        self.stop_func_list.append(x)
    
    def get_last_err_code(self):
        return self.last_err_code
    
    def reset_err_code(self):
        self.last_err_code = ERR_NONE
    
    def _add_sub_threading(self, threading_obj, start=True):
        threading_obj.setDaemon(True)
        threading_obj.add_stop_func(self.checkup_stop_func)
        threading_obj.pause_threading()
        threading_obj.start()
        self.sub_threading_list.append(threading_obj)
        logger.debug(f"sub threading {threading_obj.name} has been add.")

    def loop(self):
        pass
    
    def run(self):
        while 1:
            time.sleep(self.while_sleep)
            if self.stop_threading_flag:
                return

            if self.pause_threading_flag:
                if self.working_flag:
                    self.working_flag = False
                time.sleep(1)
                continue

            if not self.working_flag:
                self.working_flag = True
                
            if self.checkup_stop_func():
                self.pause_threading_flag = True
                continue

            self.loop()
