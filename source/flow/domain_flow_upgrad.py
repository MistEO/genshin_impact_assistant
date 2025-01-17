from source.util import *
from source.flow.flow_template import FlowController, FlowTemplate, FlowConnector, EndFlowTemplate
import source.flow.flow_code as FC
from source.controller import combat_loop
from common import timer_module
from source.funclib import generic_lib, movement, combat_lib
from source.funclib.err_code_lib import *
from source.manager import posi_manager as PosiM, asset
from source.interaction.interaction_core import itt
from source.api import yolox_api
from source.flow import flow_state as ST

class DomainFlowConnector(FlowConnector):
    """
    各个类之间的变量中继器。
    """
    def __init__(self):
        super().__init__()
        self.checkup_stop_func = None
        chara_list = combat_lib.get_chara_list()
        self.combat_loop = combat_loop.Combat_Controller(chara_list)
        self.combat_loop.setDaemon(True)

        self.combat_loop.pause_threading()
        self.combat_loop.start()
        
        self.lockOnFlag = 0
        self.move_timer = timer_module.Timer()
        self.ahead_timer = timer_module.Timer()
        domain_json = load_json("auto_domain.json")
        self.isLiYue = domain_json["isLiYueDomain"]
        self.resin_mode = domain_json["resin"]
        self.fast_mode = domain_json["fast_mode"]
    
    def reset(self):
        self.lockOnFlag = 0
        self.move_timer = timer_module.Timer()
        self.ahead_timer = timer_module.Timer()
        domain_json = load_json("auto_domain.json")
        self.isLiYue = domain_json["isLiYueDomain"]
        self.resin_mode = domain_json["resin"]
        self.fast_mode = domain_json["fast_mode"]
    
class MoveToChallenge(FlowTemplate):
    """
    移动到开始挑战目标点。
    """
    def __init__(self, upper:DomainFlowConnector):
        super().__init__(upper, flow_id=ST.INIT_MOVETO_CHALLENGE, next_flow_id=ST.INIT_CHALLENGE)
        self.upper = upper
        
    def state_init(self):
        """
        检查并关闭可能的弹窗。
        """
        logger.info(t2t('正在开始挑战秘境'))
        movement.reset_view()
        if itt.get_text_existence(asset.LEYLINEDISORDER):
            self._next_rfc()
        if itt.get_img_existence(asset.IN_DOMAIN):
            self._next_rfc()
        
        self.rfc = 1
    
    def state_before(self):
        while 1:
            if itt.get_img_existence(asset.IN_DOMAIN):
                break
            if itt.get_text_existence(asset.LEYLINEDISORDER):
                itt.move_and_click([PosiM.posi_domain['CLLD'][0], PosiM.posi_domain['CLLD'][1]], delay=1)
        time.sleep(0.5)
        movement.reset_view()
        time.sleep(2)
        movement.view_to_angle_domain(-90, self.upper.checkup_stop_func)
        self._next_rfc()
        if self.upper.fast_mode:
            itt.key_down('w')
    
    def state_in(self):
        movement.view_to_angle_domain(-90, self.upper.checkup_stop_func)
        if self.upper.fast_mode:
            pass
        else:
            movement.move(movement.AHEAD, 4)

        if generic_lib.f_recognition():
            itt.key_up('w')
            self._next_rfc()


class Challenge(FlowTemplate):
    def __init__(self, upper:DomainFlowConnector):
        super().__init__(upper, flow_id=ST.INIT_CHALLENGE, next_flow_id=ST.INIT_FINGING_TREE)
        self.upper = upper
        
    def state_init(self):
        logger.info(t2t('正在开始战斗'))
        self.upper.combat_loop.continue_threading()
        itt.key_press('f')
        time.sleep(0.1)
        
        self.upper.while_sleep = 2
        
        self._next_rfc()
    
    def state_in(self):
        if itt.get_text_existence(asset.LEAVINGIN):
            self.rfc = FC.AFTER
        else:
            self.rfc = FC.IN
    
    def state_after(self):
        
        self.upper.while_sleep = 0.1
        
        logger.info(t2t('正在停止战斗'))
        self.upper.combat_loop.pause_threading()
        time.sleep(5)
        logger.info(t2t('等待岩造物消失'))
        time.sleep(5)
        self._next_rfc()

class FindingTree(FlowTemplate):
    def __init__(self, upper:DomainFlowConnector):
        super().__init__(upper, flow_id=ST.INIT_FINGING_TREE, next_flow_id=ST.INIT_MOVETO_TREE)
        self.upper = upper
        self.move_num = 0

    def get_tree_posi(self):
        cap =itt.capture(jpgmode=0)
        # cv2.imshow('123',cap)
        # cv2.waitKey(0)
        addition_info, ret2 = yolox_api.yolo_tree.predicte(cap)
        # logger.debug(addition_info)
        if addition_info is not None:
            if addition_info[0][1][0] >= 0.5:
                tree_x, tree_y = yolox_api.yolo_tree.get_center(addition_info)
                return tree_x, tree_y
        return False

    def align_to_tree(self):
        movement.view_to_angle_domain(-90, self.upper.checkup_stop_func)
        t_posi = self.get_tree_posi()
        if t_posi:
            dx = int(t_posi[0] - SCREEN_CENTER_X)
            logger.debug(dx)

            if dx >= 0:
                movement.move(movement.RIGHT, self.move_num)
            else:
                movement.move(movement.LEFT, self.move_num)
            if abs(dx) <= 20:
                self.upper.lockOnFlag += 1
                self.move_num = 1
            return True
        else:
            self.move_num = 4
            return False
    
    def state_init(self):
        logger.info(t2t('正在激活石化古树'))
        self.upper.lockOnFlag = 0
        self._next_rfc()

    def state_in(self):
        if self.upper.lockOnFlag <= 5:
            is_tree = self.align_to_tree()
            self.upper.ahead_timer.reset()
            if not is_tree:
                movement.view_to_angle_domain(-90, self.upper.checkup_stop_func)

                if self.upper.isLiYue:  # barrier treatment
                    if self.upper.move_timer.get_diff_time() >= 20:
                        direc = not direc
                        self.upper.move_timer.reset()
                    if direc:
                        movement.move(movement.LEFT, distance=4)
                    else:
                        movement.move(movement.RIGHT, distance=4)

                else:  # maybe can't look at tree
                    logger.debug('can not find tree. moving back.')
                    movement.move(movement.BACK, distance=2)
        else:
            self._next_rfc()

class MoveToTree(FlowTemplate):
    def __init__(self, upper:DomainFlowConnector):
        super().__init__(upper, flow_id=ST.INIT_MOVETO_TREE, next_flow_id=ST.INIT_ATTAIN_REAWARD)
        self.upper = upper

    def state_before(self):
        itt.key_down('w')
        self._next_rfc()

    def state_in(self):
        
        if self.upper.ahead_timer.get_diff_time() >= 5:
            itt.key_press('spacebar')
            self.upper.ahead_timer.reset()

        movement.view_to_angle_domain(-90, self.upper.checkup_stop_func)
        if generic_lib.f_recognition(itt):
            self._next_rfc()

    def state_after(self):
        itt.key_up('w')
        self._next_rfc()

class AttainReward(FlowTemplate):
    def __init__(self, upper:DomainFlowConnector):
        super().__init__(upper, flow_id=ST.INIT_ATTAIN_REAWARD, next_flow_id=ST.END_DOMAIN)
        self.upper = upper

    def state_before(self):
        itt.key_press('f')
        time.sleep(0.2)
        if not generic_lib.f_recognition():
            self._next_rfc()

    def state_in(self):
        if self.upper.resin_mode == '40':
            itt.appear_then_click(asset.USE_20X2RESIN_DOUBLE_CHOICES)
        elif self.upper.resin_mode == '20':
            itt.appear_then_click(asset.USE_20RESIN_DOUBLE_CHOICES)

        if itt.get_text_existence(asset.domain_obtain):
            self._next_rfc()

class DomainFlowEnd(EndFlowTemplate):
    def __init__(self, upper: FlowConnector):
        super().__init__(upper, flow_id = ST.END_DOMAIN, err_code_id = ERR_PASS)

class DomainFlowController(FlowController):
    def __init__(self):
        super().__init__(flow_connector=DomainFlowConnector(),
                         current_flow_id=ST.INIT_MOVETO_CHALLENGE,
                         flow_name="DomainFlow")
        self.flow_connector = self.flow_connector #type: DomainFlowConnector
        
        self.append_flow(MoveToChallenge(self.flow_connector))
        self.append_flow(Challenge(self.flow_connector))
        self.append_flow(FindingTree(self.flow_connector))
        self.append_flow(MoveToTree(self.flow_connector))
        self.append_flow(AttainReward(self.flow_connector))
        self.append_flow(DomainFlowEnd(self.flow_connector))

    def reset(self):
        self.flow_connector.reset()
        self.current_flow_id = ST.INIT_MOVETO_CHALLENGE
        self.reset_err_code()


    


        
    