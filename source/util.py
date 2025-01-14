import json
import os
import shutil
import sys
import time  # 8药删了，qq了
import math
import numpy as np
import gettext
from loguru import logger
import cv2
import win32gui, win32process, psutil
import ctypes, pickle
from PIL import Image, ImageDraw, ImageFont

time.time()  # 防自动删除
global GLOBAL_LANG, GLOBAL_DEVICE
GLOBAL_LANG = "$locale$" # $locale$, zh_CN, en_US
DESKTOP_CN = "Desktop_CN"
DESKTOP_EN = "Desktop_EN"
MOBILE_CN = "Mobile_CN"
MOBILE_EN = "Mobile_EN"
DEVICE = DESKTOP_CN
INTERACTION_DESKTOP = "Desktop"
INTERACTION_EMULATOR = "Emulator"
INTERACTION_DESKTOP_BACKGROUND = "DesktopBackground"
INTERACTION_MODE = INTERACTION_DESKTOP # Normal, Adb, Dm
BBG = 100001
ANGLE_NORMAL = 0
ANGLE_NEGATIVE_Y = 1
ANGLE_NEGATIVE_X = 2
ANGLE_NEGATIVE_XY = 3
PROCESS_NAME = ["YuanShen.exe", "GenshinImpact.exe"]
SCREEN_CENTER_X = 1920/2
SCREEN_CENTER_Y = 1080/2

# configure paths
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_PATH = ROOT_PATH + '\\source'
ASSETS_PATH = ROOT_PATH + '\\assets'
if sys.path[0] != ROOT_PATH:
    sys.path.insert(0, ROOT_PATH)
if sys.path[1] != SOURCE_PATH:
    sys.path.insert(1, SOURCE_PATH)
from source.path_lib import *
# configure paths over



# load config file
def load_json(json_name='config.json', default_path='config\\settings') -> dict:
    # if "$lang$" in default_path:
    #     default_path = default_path.replace("$lang$", GLOBAL_LANG)
    try:
        return json.load(open(os.path.join(ROOT_PATH, default_path, json_name), 'r', encoding='utf-8'))
    except:
        json.dump({}, open(os.path.join(ROOT_PATH, default_path, json_name), 'w', encoding='utf-8'))
        return json.load(open(os.path.join(ROOT_PATH, default_path, json_name), 'r', encoding='utf-8'))
try:
    config_json = load_json("config.json")
    DEBUG_MODE = config_json["DEBUG"] if "DEBUG" in config_json else False
    GLOBAL_LANG = config_json["lang"]
except:
    logger.error("config文件导入失败，可能由于初次安装。跳过导入。 ERROR_IMPORT_CONFIG_001")
    DEBUG_MODE = False
    GLOBAL_LANG = "$locale$"

try:
    INTERACTION_MODE = load_json("config.json", CONFIG_PATH_SETTING)["interaction_mode"]
    if INTERACTION_MODE not in [INTERACTION_EMULATOR, INTERACTION_DESKTOP_BACKGROUND, INTERACTION_DESKTOP]:
        logger.warning("UNKNOWN INTERACTION MODE. SET TO \'Desktop\' Default.")
        INTERACTION_MODE = INTERACTION_DESKTOP
except:
    logger.error("config文件导入失败，可能由于初次安装。跳过导入。 ERROR_IMPORT_CONFIG_002")
    INTERACTION_MODE = INTERACTION_DESKTOP
IS_DEVICE_PC = (INTERACTION_MODE == INTERACTION_DESKTOP_BACKGROUND)or(INTERACTION_MODE == INTERACTION_DESKTOP)
# load config file over



# configure loguru
logger.remove(handler_id=None)
logger.add(os.path.join(ROOT_PATH, os.path.join(ROOT_PATH, 'Logs', "{time:YYYY-MM-DD}.log")), level="TRACE", backtrace=True, retention='15 days')
if DEBUG_MODE:
    logger.add(sys.stdout, level="TRACE", backtrace=True)
else:
    logger.add(sys.stdout, level="INFO", backtrace=True)


def hr(title, level=3):
    title = str(title).upper()
    if level == 1:
        logger.info('=' * 20 + ' ' + title + ' ' + '=' * 20)
    if level == 2:
        logger.info('-' * 20 + ' ' + title + ' ' + '-' * 20)
    if level == 3:
        logger.info('<' * 3 + ' ' + title + ' ' + '>' * 3)
    if level == 0:
        middle = '|' + ' ' * 20 + title + ' ' * 20 + '|'
        border = '+' + '-' * (len(middle) - 2) + '+'
        logger.info(border)
        logger.info(middle)
        logger.info(border)


def attr(name, text):
    logger.info('[%s] %s' % (str(name), str(text)))


def attr_align(name, text, front='', align=22):
    name = str(name).rjust(align)
    if front:
        name = front + name[len(front):]
    logger.info('%s: %s' % (name, str(text)))


logger.hr = hr
logger.attr = attr
logger.attr_align = attr_align
# configurate loguru over



# load translation module
def get_local_lang():
    import locale
    lang = locale.getdefaultlocale()[0]
    logger.debug(f"locale: {locale.getdefaultlocale()}")
    if lang in ["zh_CN", "zh_SG", "zh_MO", "zh_HK"]:
        return "zh_CN"
    else:
        return "en_US"

if GLOBAL_LANG == "$locale$":
    GLOBAL_LANG = get_local_lang()
    logger.info(f"language set as: {GLOBAL_LANG}")
l10n = gettext.translation(GLOBAL_LANG, localedir=os.path.join(ROOT_PATH, "translation/locale"), languages=[GLOBAL_LANG])
l10n.install()
t2t = l10n.gettext
# load translation module over



# verify path
if not os.path.exists(ROOT_PATH):
    logger.error(t2t("目录不存在：") + ROOT_PATH + t2t(" 请检查"))
if not os.path.exists(SOURCE_PATH):
    logger.error(t2t("目录不存在：") + SOURCE_PATH + t2t(" 请检查"))
# verify path over



# verify administration
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
if not is_admin():
    logger.error(t2t("请用管理员权限运行"))
# verify administration over


# functions
def list_text2list(text: str) -> list:
    if text is not None:  # 判断是否为空
        try:  # 尝试转换
            rt_list = json.loads(text)
        except:
            rt_list = []

        if type(rt_list) != list:  # 判断类型(可能会为dict)
            rt_list = list(rt_list)

    else:
        rt_list = []

    return rt_list

def list2list_text(lst: list) -> str:
    if lst is not None:  # 判断是否为空
        try:  # 尝试转换
            rt_str = json.dumps(lst, ensure_ascii=False)
        except:
            rt_str = str(lst)

    else:
        rt_str = str(lst)

    return rt_str


def list2format_list_text(lst: list, inline = False) -> str:
    if lst is not None:  # 判断是否为空
        try:  # 尝试转换
            rt_str = json.dumps(lst, sort_keys=False, indent=4, separators=(',', ':'), ensure_ascii=False)
        except:
            rt_str = str(lst)

    else:
        rt_str = str(lst)
    # print(rt_str)
    if inline:
        rt_str = rt_str.replace('\n', ' ')
    return rt_str


def is_json_equal(j1: str, j2: str) -> bool:
    try:
        return json.dumps(json.loads(j1), sort_keys=True) == json.dumps(json.loads(j2), sort_keys=True)
    except:
        return False

def add_logger_to_GUI(cb_func):
    if DEBUG_MODE:
        logger.add(cb_func, level="DEBUG", backtrace=True, colorize=True)
    else:
        logger.add(cb_func, level="INFO", backtrace=True, colorize=True)



def is_int(x):
    try:
        int(x)
    except ValueError:
        return False
    else:
        return True



def points_angle(p1, p2, coordinate=ANGLE_NORMAL):
    # p1: current point
    # p2: target point
    x = p1[0]
    y = p1[1]
    tx = p2[0]
    ty = p2[1]
    if coordinate == ANGLE_NEGATIVE_Y:
        y = -y
        ty = -ty
    k = (ty - y) / (tx - x)
    degree = math.degrees(math.atan(k))
    if degree < 0:
        degree += 180
    if ty < y:
        degree += 180

    degree -= 90
    if degree > 180:
        degree -= 360
    return degree

def save_json(x, json_name='config.json', default_path='config', sort_keys=True, auto_create=False):
    if not os.path.exists(default_path):
        logger.error(f"CANNOT FIND PATH: {default_path}")
    if sort_keys:
        json.dump(x, open(os.path.join(default_path, json_name), 'w', encoding='utf-8'), sort_keys=True, indent=2,
              ensure_ascii=False)
    else:
        json.dump(x, open(os.path.join(default_path, json_name), 'w', encoding='utf-8'),
              ensure_ascii=False)


def loadfileP(filename):
    with open('wordlist//' + filename + '.wl', 'rb') as fp:
        list1 = pickle.load(fp)
    return list1


def savefileP(filename, item):
    with open('wordlist//' + filename + '.wl', 'w+b') as fp:
        pickle.dump(item, fp)


def refresh_config():
    global config_json
    config_json = load_json("config.json")

def euclidean_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def euclidean_distance_plist(p1, plist) -> np.ndarray:
    if not isinstance(p1, np.ndarray):
        p1 = np.array(p1)
    if not isinstance(plist, np.ndarray):
        plist = np.array(plist)
    return np.sqrt((p1[0] - plist[:,0]) ** 2 + (p1[1] - plist[:,1]) ** 2)

def manhattan_distance(p1, p2):
    return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])

def manhattan_distance_plist(p1, p2) -> np.ndarray:
    return abs(p1[0]-p2[:,0]) + abs(p1[1]-p2[:,1])

def quick_euclidean_distance_plist(p1, p2, max_points_num = 50)-> np.ndarray:
    if not isinstance(p1, np.ndarray):
        p1 = np.array(p1)
    if not isinstance(p2, np.ndarray):
        p2 = np.array(p2)
    # 计算当前点到所有优先点的曼哈顿距离
    md = manhattan_distance_plist(p1, p2)
    nearly_pp_arg = np.argsort(md)
    # 计算当前点到距离最近的50个优先点的欧拉距离
    cache_num = min(max_points_num, len(nearly_pp_arg))
    nearly_pp = p2[nearly_pp_arg[:cache_num]]
    ed = euclidean_distance_plist(p1, nearly_pp)

    return ed

    # 将点按欧拉距离升序排序
    nearly_pp_arg = np.argsort(ed)
    nearly_pp = nearly_pp[nearly_pp_arg]
    # print(currentp, closest_pp)
    return nearly_pp
    


    return np.sqrt((p1[0] - p2[:,0]) ** 2 + (p1[1] - p2[:,1]) ** 2)



def is_number(s):
    """
    懒得写,抄的
    https://www.runoob.com/python3/python3-check-is-number.html
    """
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False



def get_active_window_process_name():
    try:
        pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
        return(psutil.Process(pid[-1]).name())
    except:
        pass

def maxmin(x,nmax,nmin):
    x = min(x, nmax)
    x = max(x, nmin)
    return x

def crop(image, area):
    """
    Crop image like pillow, when using opencv / numpy.
    Provides a black background if cropping outside of image.
    Args:
        image (np.ndarray):
        area:
    Returns:
        np.ndarray:
    """
    x1, y1, x2, y2 = map(int, map(round, area))
    h, w = image.shape[:2]
    border = np.maximum((0 - y1, y2 - h, 0 - x1, x2 - w), 0)
    x1, y1, x2, y2 = np.maximum((x1, y1, x2, y2), 0)
    image = image[y1:y2, x1:x2].copy()
    if sum(border) > 0:
        image = cv2.copyMakeBorder(image, *border, borderType=cv2.BORDER_CONSTANT, value=(0, 0, 0))
    return image

def recorp(image, size, area):
    r = np.zeros((size[1], size[0], size[2]), dtype='uint8')
    r[area[1]:area[3], area[0]:area[2], :] = image
    return r
    

def get_color(image, area):
    """Calculate the average color of a particular area of the image.
    Args:
        image (np.ndarray): Screenshot.
        area (tuple): (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y)
    Returns:
        tuple: (r, g, b)
    """
    temp = crop(image, area)
    color = cv2.mean(temp)
    return color[:3]


def get_bbox(image, black_offset=15):
    """
    A numpy implementation of the getbbox() in pillow.
    Args:
        image (np.ndarray): Screenshot.
    Returns:
        tuple: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y)
    """
    if image_channel(image) == 3:
        image = np.max(image, axis=2)
    x = np.where(np.max(image, axis=0) > black_offset)[0]
    y = np.where(np.max(image, axis=1) > black_offset)[0]
    return (x[0], y[0], x[-1] + 1, y[-1] + 1)

def area_offset(area, offset):
    """
    Args:
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        offset: (x, y).
    Returns:
        tuple: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
    """
    return tuple(np.array(area) + np.append(offset, offset))

def image_channel(image):
    """
    Args:
        image (np.ndarray):
    Returns:
        int: 0 for grayscale, 3 for RGB.
    """
    return image.shape[2] if len(image.shape) == 3 else 0


def image_size(image):
    """
    Args:
        image (np.ndarray):
    Returns:
        int, int: width, height
    """
    shape = image.shape
    return shape[1], shape[0]

def convert_text_to_img(text=""):
    # 加载一个中文字体文件
    font = ImageFont.truetype("simhei.ttf", 32)

    # 获取一段中文文字的宽度和高度
    width, height = font.getsize(text)

    # 创建一个白色背景的图片，大小刚好能容纳文字
    img = Image.new("RGB", (width, height), "white")

    # 创建一个绘图对象
    draw = ImageDraw.Draw(img)

    # 在图片上绘制文字，位置为左上角
    draw.text((0, 0), text, font=font, fill="black")

    # 将图片转换回OpenCV格式
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    return img

def replace_text_format(text:str):
    text = text.replace("：",":")
    text = text.replace("！","!")
    text = text.replace("？","?")
    text = text.replace("，",",")
    text = text.replace("。",".")
    text = text.replace("“","\"")
    text = text.replace("”","\"")
    text = text.replace("‘","\'")
    text = text.replace("’","\'")
    return text

def compare_texts(text1, text2, is_show_res = False, ignore_warning = False):
    # 读取两个短文本的图片
    
    if not ignore_warning:
        if len(text1) != len(text2):
            logger.trace(f"compare_texts警告：不相同的文字长度:{text1}, {text2}")
    
    font = ImageFont.truetype("simhei.ttf", 16)
    width1, height1 = font.getsize(text1)
    width2, height2 = font.getsize(text2)
    width = max(width1, width2)
    height = max(height1, height2)
    img1 = Image.new("RGB", (width, height), "white")
    img2 = Image.new("RGB", (width, height), "white")
    draw1 = ImageDraw.Draw(img1)
    draw1.text((0, 0), text1, font=font, fill="black")
    draw2 = ImageDraw.Draw(img2)
    draw2.text((0, 0), text2, font=font, fill="black")
    img1 = cv2.cvtColor(np.array(img1), cv2.COLOR_RGB2BGR)
    img2 = cv2.cvtColor(np.array(img2), cv2.COLOR_RGB2BGR)
        
    
    # 将图片转换为灰度图
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # 计算两个灰度图之间的绝对差异
    diff = cv2.absdiff(gray1, gray2)

    # 设置一个阈值，将差异大于阈值的像素标记为白色，小于阈值的像素标记为黑色
    thresh = 50
    mask = diff > thresh

    # 将掩码转换为uint8类型，并乘以255，得到二值化后的差异图像
    mask = mask.astype(np.uint8) * 255

    matching_rate = 1 - len(np.where(mask==255)[0])/len(np.where(mask!=256)[0])
    logger.trace(f"texts matching rate:{matching_rate} text1 {text1} text2 {text2}")
    if len(text1) != len(text2):
        matching_rate = max( matching_rate - 0.06*abs(len(text1) - len(text2)), 0)
        logger.trace(f"fixed matching rate:{matching_rate}")
    if is_show_res:
        # 在原始图片上绘制红色边框，表示差异区域
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            x,y,w,h = cv2.boundingRect(cnt)
            cv2.rectangle(img1,(x,y),(x+w,y+h),(0,0,255),3)
            cv2.rectangle(img2,(x,y),(x+w,y+h),(0,0,255),3)

        # 显示结果图片
        cv2.imshow("Image 1", img1)
        cv2.imshow("Image 2", img2)
        cv2.imshow("Difference", mask)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    return matching_rate

def load_jsons_from_folder(path, black_file:list=None):
    json_list = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if f[f.index('.') + 1:] == "json":
                if f[:f.index('.')] not in black_file:
                    j = json.load(open(os.path.join(path, f), 'r', encoding='utf-8'))
                    json_list.append({"label": f, "json": j})
    return json_list

# Update for a program used before version v0.5.0.424
if os.path.exists(os.path.join(ROOT_PATH, "config\\tastic")):
    logger.info("检测到tastic文件夹。")
    logger.info("版本v0.5.0.424后，tastic文件夹修正为tactic文件夹。")
    time.sleep(1)
    logger.warning("正在准备将tastic文件夹中的json文件迁移至tastic文件夹。")
    time.sleep(1)
    logger.warning("该操作可能有风险，您可以将config/tastic文件夹中的文件备份后再继续。")
    time.sleep(1)
    logger.warning("该操作将在15秒后开始。")
    time.sleep(15)
    for root, dirs, files in os.walk(os.path.join(ROOT_PATH, "config\\tastic")):
        for f in files:
            if f[f.index(".")+1:] == "json":
                shutil.copy(os.path.join(ROOT_PATH, "config\\tastic", f), os.path.join(ROOT_PATH, "config\\tactic", f))
    logger.warning("准备删除tastic文件夹。")
    time.sleep(1)
    logger.warning("该操作可能有风险，您可以将config/tastic文件夹中的文件备份后再继续。")
    time.sleep(1)
    logger.warning("该操作将在15秒后开始。")
    time.sleep(15)
    shutil.rmtree(os.path.join(ROOT_PATH, "config\\tastic"))
    logger.info("操作完成。您可以手动删除残留的config/tactic/tastic.json文件。")
    time.sleep(1)
    # os.rename(os.path.join(root_path, "config\\tactic"), os.path.join(root_path, "config\\tactic"))
# Over


if __name__ == '__main__':
    # a = load_jsons_from_folder(os.path.join(root_path, "config\\tactic"))
    print(get_active_window_process_name())
    pass
    # load_jsons_from_floder((root_path, "config\\tactic"))