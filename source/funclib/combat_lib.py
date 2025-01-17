from source.manager import img_manager, posi_manager, asset
from source.util import *
from source.common.base_threading import BaseThreading
import numpy as np
from common import timer_module
from source.common import character
from source.interaction.interaction_core import itt
from source.interaction import interaction_core

"""
战斗相关常用函数库。
"""

global only_arrow_timer, characters, load_err_times
only_arrow_timer = timer_module.Timer()
characters = load_json("character.json", default_path="config\\tactic")
load_err_times = 0

def default_stop_func():
    return False

class TacticKeyNotFoundError(RuntimeError):
    def __init__(self, arg):
        self.args = [arg]

class TacticKeyEmptyError(RuntimeError):
    def __init__(self, arg):
        self.args = [arg]

CREATE_WHEN_NOTFOUND = 0
RAISE_WHEN_NOTFOUND = 1


def get_param(team_item, para_name, auto_fill_flag, chara_name="", exception_mode = RAISE_WHEN_NOTFOUND, value_when_empty = None):
    global load_err_times
    if para_name not in team_item:
        if exception_mode == RAISE_WHEN_NOTFOUND:
            logger.error(f"{t2t('Tactic ERROR: INDEX NOT FOUND')}")
            logger.error(f"{t2t('parameter name')}: {para_name}; {t2t('character name')}: {chara_name}")
            raise TacticKeyNotFoundError(f"Key: {para_name}")
        elif exception_mode == CREATE_WHEN_NOTFOUND:
            pass
    else:
        if not auto_fill_flag:
            r = team_item[para_name]
        else:
            r = characters[chara_name]
    
    if r == '' or r == None:
        if value_when_empty != None:
            r = value_when_empty
        else:
            logger.error(f"{t2t('Tactic ERROR: Key Empty')}")
            logger.error(f"{t2t('parameter name')}: {para_name}; {t2t('character name')}: {chara_name}")
            load_err_times+=1
            # raise TacticKeyEmptyError(f"Key: {para_name}")
    logger.trace(f"character: {chara_name} para_name: {para_name} value: {r}")
    return r

def get_chara_list(team_name='team.json'):
    global load_err_times
    load_err_times = 0
    team_name = load_json("auto_combat.json",CONFIG_PATH_SETTING)["teamfile"]
    dpath = "config\\tactic"
    
    team = load_json(team_name, default_path=dpath)
    
    for team_n in team:
        team_item = team[team_n]
        team_item.setdefault("name", None)
        team_item.setdefault("position", None)
        team_item.setdefault("priority", None)
        team_item.setdefault("E_short_cd_time", None)
        team_item.setdefault("E_long_cd_time", None)
        team_item.setdefault("Elast_time", None)
        team_item.setdefault("Ecd_float_time", None)
        team_item.setdefault("n", None)
        team_item.setdefault("trigger", None)
        team_item.setdefault("Epress_time", None)
        team_item.setdefault("Qlast_time", None)
        team_item.setdefault("Qcd_time", None)
        team_item.setdefault("vision", None)
    save_json(team, team_name, default_path=dpath)
    
    # characters = load_json("character.json", default_path=dpath)
    chara_list = []
    for team_name in team:
        team_item = team[team_name]
        autofill_flag = False
        # autofill_flag = team_item["autofill"]
        cname = get_param(team_item, "name", autofill_flag, chara_name="", )
        c_position = get_param(team_item, "position", autofill_flag, chara_name=cname, value_when_empty='')
        c_priority = get_param(team_item, "priority", autofill_flag, chara_name=cname)
        cE_short_cd_time = get_param(team_item, "E_short_cd_time", autofill_flag, chara_name=cname)
        cE_long_cd_time = get_param(team_item, "E_long_cd_time", autofill_flag, chara_name=cname)
        cElast_time = get_param(team_item, "Elast_time", autofill_flag, chara_name=cname)
        cEcd_float_time = get_param(team_item, "Ecd_float_time", autofill_flag, chara_name=cname)
        cn = get_param(team_item, "n", autofill_flag, chara_name=cname)
        try:
            c_tactic_group = team_item["tactic_group"]
        except:
            c_tactic_group = team_item["tastic_group"]
            logger.warning(t2t("请将配对文件中的tastic_group更名为tactic_group. 已自动识别。"))
            
        c_trigger = get_param(team_item, "trigger", autofill_flag, chara_name=cname, value_when_empty="e_ready")
        cEpress_time = get_param(team_item, "Epress_time", autofill_flag, chara_name=cname)
        cQlast_time = get_param(team_item, "Qlast_time", autofill_flag, chara_name=cname)
        cQcd_time = get_param(team_item, "Qcd_time", autofill_flag, chara_name=cname)
        c_vision = get_param(team_item, "vision", autofill_flag, chara_name=cname)
        
        
        if cEcd_float_time > 0:
            logger.info(t2t("角色 ") + cname + t2t(" 的Ecd_float_time大于0，请确定该角色不是多段e技能角色。"))
    
        chara_list.append(
            character.Character(
                name=cname, position=c_position, n=cn, priority=c_priority,
                E_short_cd_time=cE_short_cd_time, E_long_cd_time=cE_long_cd_time, Elast_time=cElast_time,
                Ecd_float_time=cEcd_float_time, tactic_group=c_tactic_group, trigger=c_trigger,
                Epress_time=cEpress_time, Qlast_time=cQlast_time, Qcd_time=cQcd_time, vision = c_vision
            )
        )
    if load_err_times>0:
        raise TacticKeyEmptyError(t2t("Character Key Empty Error"))
        
    return chara_list

def unconventionality_situation_detection(itt: interaction_core.InteractionBGD,
                                           autoDispose=True):
    # unconventionality situlation detection
    # situlation 1: coming_out_by_space

    situation_code = -1

    while itt.get_img_existence(asset.COMING_OUT_BY_SPACE):
        situation_code = 1
        itt.key_press('spacebar')
        logger.debug('Unconventionality Situation: COMING_OUT_BY_SPACE')
        time.sleep(0.1)
    while itt.get_img_existence(asset.motion_swimming):
        situation_code = 2
        itt.key_down('w')
        logger.debug('Unconventionality Situation: SWIMMING')
        if autoDispose:
            time.sleep(5)
        itt.key_up('w')
        time.sleep(0.1)

    return situation_code

def get_character_busy(itt: interaction_core.InteractionBGD, stop_func, print_log = True):
    cap = itt.capture(jpgmode=2)
    # cap = itt.png2jpg(cap, channel='ui')
    t1 = 0
    t2 = 0
    for i in range(4):
        if stop_func():
            return 0
        p = posi_manager.chara_head_list_point[i]
        if cap[p[0], p[1]][0] > 0 and cap[p[0], p[1]][1] > 0 and cap[p[0], p[1]][2] > 0:
            t1 += 1
    for i in range(4):
        p = posi_manager.chara_num_list_point[i]
        # print(min(cap[p[0], p[1]]))
        if min(cap[p[0], p[1]]) > 248:
            t2 += 1
    
    # elif t == 4:
    #     logger.debug("function: get_character_busy: t=4： 测试中功能，如果导致换人失败，反复输出 waiting 请上报。")
    #     return True
    
    if t1 >= 3 and t2 == 3:
        return False
    else:
        if print_log:
            logger.trace(f"waiting: character busy: t1{t1} t2{t2}")
        return True

def chara_waiting(itt:interaction_core.InteractionBGD, stop_func, mode=0, max_times = 1000):
    unconventionality_situation_detection(itt)
    i=0
    while get_character_busy(itt, stop_func) and (not stop_func()):
        i+=1
        if stop_func():
            logger.debug('chara_waiting stop')
            return 0
        # logger.debug('waiting')
        itt.delay(0.1)
        if i>=max_times:
            break

def get_current_chara_num(itt: interaction_core.InteractionBGD, stop_func = default_stop_func, max_times = 1000):
    """获得当前所选角色序号。

    Args:
        itt (InteractionBGD): InteractionBGD对象

    Returns:
        int: character num.
    """
    chara_waiting(itt, stop_func, max_times = max_times)
    cap = itt.capture(jpgmode=2)
    for i in range(4):
        p = posi_manager.chara_num_list_point[i]
        # print(min(cap[p[0], p[1]]))
        if min(cap[p[0], p[1]]) > 248:
            continue
        else:
            return i + 1
        
    logger.warning(t2t("获得当前角色编号失败"))
    return 0

def combat_statement_detection(itt: interaction_core.InteractionBGD):
    
    im_src = itt.capture()
    orsrc = im_src.copy()
    
    red_num = 245
    bg_num = 100

    im_src = orsrc.copy()
    im_src = itt.png2jpg(im_src, channel='ui', alpha_num=254)

    im_src[990:1080, :, :] = 0
    im_src[0:150, :, :] = 0
    im_src[:, 1650:1920, :] = 0
    
    im_src[:, :, 2][im_src[:, :, 2] < red_num] = 0
    im_src[:, :, 2][im_src[:, :, 0] > bg_num] = 0
    im_src[:, :, 2][im_src[:, :, 1] > bg_num] = 0
    # _, imsrc2 = cv2.threshold(imsrc[:, :, 2], 1, 255, cv2.THRESH_BINARY)
    
    flag_is_blood_bar_exist = im_src[:, :, 2].max() > 0
    # print('flag_is_blood_bar_exist ',flag_is_blood_bar_exist)
    if flag_is_blood_bar_exist:
        only_arrow_timer.reset()
        return True
    
    '''-----------------------------'''
    
    red_num = 250
    blue_num = 90
    green_num = 90
    float_num = 30
    im_src = orsrc.copy()
    im_src = itt.png2jpg(im_src, channel='ui', alpha_num=150)
    # img_manager.qshow(imsrc)

    '''可以用圆形遮挡优化'''

    im_src[950:1080, :, :] = 0
    im_src[0:50, :, :] = 0
    im_src[:, 1650:1920, :] = 0
    # img_manager.qshow(imsrc)
    im_src[:, :, 2][im_src[:, :, 2] < red_num] = 0
    im_src[:, :, 2][im_src[:, :, 0] > blue_num + float_num] = 0
    im_src[:, :, 2][im_src[:, :, 0] < blue_num - float_num] = 0
    im_src[:, :, 2][im_src[:, :, 1] > green_num + float_num] = 0
    im_src[:, :, 2][im_src[:, :, 1] < green_num - float_num] = 0
    
    # img_manager.qshow(imsrc[:, :, 2])
    imsrc2 = im_src.copy()
    _, imsrc2 = cv2.threshold(imsrc2[:, :, 2], 1, 255, cv2.THRESH_BINARY)
    # img_manager.qshow(imsrc2)
    ret_contours = img_manager.get_rect(imsrc2, orsrc, ret_mode=3)
    ret_range = img_manager.get_rect(imsrc2, orsrc, ret_mode=0)
    
    
    
    if False:
        if len(ret_contours) != 0:
            angle = cv2.minAreaRect(ret_contours)[2]
            print(angle)
            img = im_src.copy()[:, :, 2]
            img = img[ret_range[0]:ret_range[2],ret_range[1]:ret_range[3]]
            h, w = img.shape
            center = (w//2, h//2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)    
            cv2.imshow('123', rotated)
            cv2.waitKey(50)
        
    red_arrow_num = len(np.where(im_src[:, :, 2]>=254)[-1])
    if red_arrow_num > 180:
        return True
    # print('flag_is_arrow_exist', flag_is_arrow_exist)

    

    return False

class CombatStatementDetectionLoop(BaseThreading):
    def __init__(self):
        super().__init__()
        self.setName("CombatStatementDetectionLoop")
        self.itt = itt
        self.current_state = False
        self.state_counter = 0
        self.while_sleep = 0.1
    
    def get_combat_state(self):
        return self.current_state
    
    def run(self):
        '''if you're using this class, copy this'''
        while 1:
            time.sleep(self.while_sleep)
            if self.stop_threading_flag:
                return 0

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
            if only_arrow_timer.get_diff_time()>=30:
                if self.current_state == True:
                    logger.debug("only arrow but blood bar is not exist over 30s, ready to exit combat mode.")
                state = combat_statement_detection(self.itt)
                state = False
            else:
                state = combat_statement_detection(self.itt)
            if state != self.current_state:
                
                if self.current_state == True: # 切换到无敌人慢一点, 8s
                    self.state_counter += 1
                    self.while_sleep = 0.8
                elif self.current_state == False: # 快速切换到遇敌
                    self.while_sleep = 0.02
                    self.state_counter += 1
            else:
                self.state_counter = 0
                self.while_sleep = 0.2
            if self.state_counter >= 10:
                logger.debug('combat_statement_detection change state')
                # if self.current_state == False:
                #     only_arrow_timer.reset()
                self.state_counter = 0
                self.current_state = state
            
                

CSDL = CombatStatementDetectionLoop()
CSDL.start()

if __name__ == '__main__':
    itt = itt
    
    get_chara_list()
    print()
    
    while 1:
        time.sleep(0.5)
        print(CSDL.get_combat_state())
        # print(get_character_busy(itt, default_stop_func))
        # time.sleep(0.2)
