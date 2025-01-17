from source.util import *
import keyboard
from source.task.task_template import TaskTemplate
from source.common.base_threading import BaseThreading


COLLECTION_PATH_TASK = "CollectionPathTask"
DOMAIN_TASK = "DomainTask"
    
class TaskManager(BaseThreading):
    def __init__(self) -> None:
        super().__init__(thread_name="TaskManager")
        self.reg_task_flag = False
        self.curr_task = TaskTemplate()
        self.task_list = []
        self.get_task_list = lambda:[]
        self.start_tasklist_flag = False
    
    def append_task(self, task_name):
        self.task_list.append(task_name)

    def set_tasklist(self, tasks):
        self.task_list = tasks

    def clear_task_list(self):
        self.task_list = []

    def stop_tasklist(self):
        self.start_tasklist_flag = False
    
    def get_task_statement(self):
        if not self.start_tasklist_flag:
            return t2t("No Task Running")
        elif self.start_tasklist_flag and not self.reg_task_flag:
            return t2t("Loading")
        else:
            return self.curr_task.get_flow_statement()
    
    def remove_task(self, task_name) -> bool:
        for i in range(len(self.task_list)):
            if self.task_list[i] == task_name:
                del(self.task_list[i])
                return True
        return False
        
    def start_stop_tasklist(self):
        self.start_tasklist_flag = not self.start_tasklist_flag

    def start_stop_task(self, task_name):
        if not self.reg_task_flag:
            
            # if self.curr_task.stop_threading_flag:
            #     logger.info(t2t("End Task"))
            #     self.curr_task.end_task()
            #     self.reg_task_flag = not self.reg_task_flag
            
            if task_name == COLLECTION_PATH_TASK:
                from source.task.collection_path_task import CollectionPathTask
                self.curr_task = CollectionPathTask()
                self.curr_task.start()
                self.reg_task_flag = True
                logger.info(t2t("Task CollectionPathTask Start."))

            elif task_name == DOMAIN_TASK:
                from source.task.domain_task import DomainTask
                self.curr_task = DomainTask()
                self.curr_task.start()
                self.reg_task_flag = True
                logger.info(t2t("Task DomainTask Start."))
            elif task_name == 'CollectorTask':
                pass
        else:
            logger.info(t2t("End Task"))
            self.curr_task.end_task()
            self.reg_task_flag = not self.reg_task_flag


    def run(self):
        '''if you're using this class, copy this'''
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
            '''write your code below'''

            if self.start_tasklist_flag:
                # self.task_list = self.get_task_list()
                if len(self.task_list)>0:
                    for i in self.task_list:
                        if self.checkup_stop_func():
                            break
                        if self.start_tasklist_flag == False:
                            break
                        self.start_stop_task(i)
                        while 1:
                            if not self.reg_task_flag:
                                break
                            if self.checkup_stop_func():
                                break
                            if self.start_tasklist_flag == False:
                                break
                            if self.curr_task.pause_threading_flag or self.curr_task.stop_threading_flag:
                                break
                            time.sleep(1)
                        logger.info(f"task {i} end.")
                    logger.info(f"all task end.")
                    self.stop_tasklist()
                    # self.pause_threading()

if __name__ == '__main__':
    tm = TaskManager()
    keyboard.add_hotkey(load_json("keymap.json", f"{CONFIG_PATH_SETTING}")["task"], tm.start_stop_task, args=("CollectionPathTask",))
    while 1:
        time.sleep(1)
    