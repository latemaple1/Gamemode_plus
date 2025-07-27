# -*- coding: utf-8 -*-
import time
import os
import json
from math import ceil, floor
from typing import Optional, Any
from threading import Thread

from mcdreforged.api.types import PluginServerInterface, PlayerCommandSource
from mcdreforged.api.command import *
from mcdreforged.api.decorator import new_thread
from mcdreforged.api.utils import Serializable

DIMENSIONS = {
    '0': 'minecraft:overworld',
    '-1': 'minecraft:the_nether',
    '1': 'minecraft:the_end',
    'overworld': 'minecraft:overworld',
    'the_nether': 'minecraft:the_nether',
    'the_end': 'minecraft:the_end',
    'nether': 'minecraft:the_nether',
    'end': 'minecraft:the_end',
    'minecraft:overworld': 'minecraft:overworld',
    'minecraft:the_nether': 'minecraft:the_nether',
    'minecraft:the_end': 'minecraft:the_end'
}

HUMDIMS = {
    'minecraft:overworld': '主世界',
    'minecraft:the_nether': '下界',
    'minecraft:the_end': '末地'
}

DEFAULT_CONFIG = {
    'spec': 1,
    'spec_other': 2,
    'tp': 1,
    'back': 1
}

HELP_MESSAGE = '''§6!!spec §7旁观/生存切换
§6!!spec <player> §7切换他人模式
§6!!tp [dimension] [position] §7传送至指定地点
§6!!back §7返回上个地点'''


class Config(Serializable):
    short_command: bool = True
    spec: int = 1
    spec_other: int = 2
    tp: int = 1
    back: int = 1


config: Config
data: dict
minecraft_data_api: Optional[Any]


def nether_to_overworld(x, z):
    return int(float(x)) * 8, int(float(z)) * 8


def overworld_to_nether(x, z):
    return floor(float(x) / 8 + 0.5), floor(float(z) / 8 + 0.5)


def load_data_from_world(server: PluginServerInterface):
    """从与world同级的目录加载数据"""
    try:
        working_dir = server.get_mcdr_config().get('working_directory', '.')
        data_file_path = os.path.join(working_dir, 'world', 'spec_data.json')
        
        server.logger.debug(f"尝试从路径加载数据: {data_file_path}")
        server.logger.debug(f"文件是否存在: {os.path.exists(data_file_path)}")
        
        if os.path.exists(data_file_path):
            with open(data_file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                server.logger.debug(f"成功加载数据，包含 {len(content.get('data', {}))} 个条目")
                return content.get('data', {})
        else:
            server.logger.debug("数据文件不存在，返回空数据")
            return {}
    except Exception as e:
        server.logger.error(f"从与world同级目录加载数据时出错: {e}")
        return {}


def save_data_to_world(server: PluginServerInterface, data):
    """将数据保存到与world同级的目录"""
    try:
        working_dir = server.get_mcdr_config().get('working_directory', '.')
        data_file_path = os.path.join(working_dir, 'world', 'spec_data.json')
        
        server.logger.debug(f"保存数据到: {data_file_path}")
        server.logger.debug(f"保存的数据条目数: {len(data)}")
        
        with open(data_file_path, 'w', encoding='utf-8') as f:
            json.dump({'data': data}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        server.logger.error(f"保存数据到与world同级目录时出错: {e}")


def on_load(server: PluginServerInterface, old):
    global config, data, minecraft_data_api
    config = server.load_config_simple(
        'config.json',
        default_config=DEFAULT_CONFIG,
        target_class=Config
    )
    
    # 定义数据文件路径 (新位置在 world 目录下)
    working_dir = server.get_mcdr_config().get('working_directory', '.')
    data_file_path = os.path.join(working_dir, 'world', 'spec_data.json')
    
    # 确保目录存在
    data_dir = os.path.dirname(data_file_path)
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
            server.logger.debug(f"创建目录: {data_dir}")
        except Exception as e:
            server.logger.error(f"创建目录 {data_dir} 失败: {e}")
    
    # 查找旧数据文件 (在gamemode插件目录中)
    old_data_file = None
    plugins_dir = os.path.dirname(server.get_data_folder())  # 获取plugins目录
    gamemode_plugin_dir = os.path.join(plugins_dir, 'gamemode')
    
    # 检查gamemode插件目录是否存在
    if os.path.exists(gamemode_plugin_dir):
        potential_old_data_file = os.path.join(gamemode_plugin_dir, 'data.json')
        if os.path.exists(potential_old_data_file):
            old_data_file = potential_old_data_file
            server.logger.debug(f"找到gamemode插件目录中的旧数据文件: {old_data_file}")
    
    # 如果没找到，尝试其他可能的位置
    if not old_data_file:
        # 尝试直接在plugins目录下查找
        potential_old_data_file = os.path.join(plugins_dir, 'gamemode_data.json')
        if os.path.exists(potential_old_data_file):
            old_data_file = potential_old_data_file
            server.logger.debug(f"找到plugins目录中的旧数据文件: {old_data_file}")
    
    server.logger.debug(f"新数据文件路径: {data_file_path}")
    server.logger.debug(f"新数据文件是否存在: {os.path.exists(data_file_path)}")
    
    # 如果找到了旧数据文件，且新的数据文件不存在，则迁移数据
    if old_data_file and not os.path.exists(data_file_path):
        try:
            server.logger.info(f'检测到gamemode插件的旧数据文件，正在迁移...')
            server.logger.debug(f'旧数据文件路径: {old_data_file}')
            
            # 尝试读取旧格式数据
            old_data = {}
            try:
                with open(old_data_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:  # 文件不为空
                        old_content = json.loads(content)
                        # 检查旧数据格式
                        if isinstance(old_content, dict):
                            if 'data' in old_content and isinstance(old_content['data'], dict):
                                # 已经是 {'data': data} 格式
                                old_data = old_content['data']
                                server.logger.info('旧数据是包含"data"键的格式，提取数据')
                            else:
                                # 直接是数据字典格式
                                old_data = old_content
                                server.logger.info('旧数据是直接字典格式')
                        else:
                            server.logger.warning(f'旧数据格式不正确: {type(old_content)}')
                    else:
                        server.logger.warning('旧数据文件为空')
            except json.JSONDecodeError as e:
                server.logger.error(f'旧数据文件JSON格式错误: {e}')
            except Exception as e:
                server.logger.error(f'读取旧数据文件时出错: {e}')
            
            # 保存为新格式到 world 目录
            save_data_to_world(server, old_data)
            server.logger.info(f'已成功将数据从 {old_data_file} 迁移到 {data_file_path}')
        except Exception as e:
            server.logger.error(f'迁移旧数据时出错: {e}')
            # 出错时初始化为空数据
            try:
                save_data_to_world(server, {})
            except Exception as e2:
                server.logger.error(f'初始化空数据时也出错: {e2}')
    elif old_data_file and os.path.exists(data_file_path):
        server.logger.debug("旧数据文件和新数据文件都存在，跳过迁移")
    elif not old_data_file:
        server.logger.debug("未检测到gamemode插件的旧数据文件")
    
    data = load_data_from_world(server)
    minecraft_data_api = server.get_plugin_instance('minecraft_data_api')

    server.register_help_message('!!spec help', 'Gamemode 插件帮助')



    @new_thread('Gamemode switch mode')
    def change_mode(src, ctx):
        if src.is_console:
            return src.reply('§c仅允许玩家使用')
        player = src.player if ctx == {} else ctx['player']
        if player not in data.keys():
            server.tell(player, '§a已切换至旁观模式')
            sur_to_spec(server, player)
        else:
            use_time = ceil((time.time() - data[player]['time']) / 60)
            server.tell(player, f'§a您使用了§e{use_time}min')
            spec_to_sur(server, player)

    @new_thread('Gamemode tp')
    def tp(src: PlayerCommandSource, ctx):
        def coordValid(a):
            if a.count('-') > 1 or a.count('.') > 1 or a.startswith(
                    '.') or a.endswith('.'):
                return False
            a = a.replace('-', '')
            a = a.replace('.', '')
            if a.isdigit():
                return True
            return False

        if src.is_console:
            return src.reply('§c仅允许玩家使用')
        if src.player not in data.keys():
            src.reply('§c您只能在旁观模式下传送')

        params = []

        if ctx.get('param1', '') != '':
            params.append(ctx['param1'])
            if ctx.get('param2', '') != '':
                params.append(ctx['param2'])
                if ctx.get('param3', '') != '':
                    params.append(ctx['param3'])
                    if ctx.get('param4', '') != '':
                        params.append(ctx['param4'])

        dim = ''
        pos = ''
        humpos = ''

        if len(params) == 1:  # only dimension
            if params[0] not in DIMENSIONS.keys():
                src.reply('§c没有此维度')
            else:
                try:
                    current_dim = minecraft_data_api.get_player_info(src.player, 'Dimension')
                except Exception as e:
                    src.reply('§c无法获取玩家当前维度信息')
                    server.logger.error(f'获取玩家 {src.player} 维度信息失败: {e}')
                    return
                    
                if DIMENSIONS[params[0]] == DIMENSIONS[current_dim]:
                    src.reply('§c您正在此维度！')
                elif (DIMENSIONS[params[0]] == 'minecraft:the_nether') and (
                        DIMENSIONS[current_dim] == 'minecraft:overworld'):
                    dim = DIMENSIONS[params[0]]
                    try:
                        orgpos = [
                            str(x) for x in
                            minecraft_data_api.get_player_info(src.player, 'Pos')
                        ]
                    except Exception as e:
                        src.reply('§c无法获取玩家当前位置信息')
                        server.logger.error(f'获取玩家 {src.player} 位置信息失败: {e}')
                        return
                        
                    newposx, newposz = overworld_to_nether(orgpos[0], orgpos[2])
                    pos = ' '.join((str(newposx), orgpos[1], str(newposz)))
                    humpos = ' '.join(
                        (str(newposx), str(int(float(orgpos[1]))), str(newposz))
                    )
                elif (DIMENSIONS[params[0]] == 'minecraft:overworld') and (
                        DIMENSIONS[current_dim] == 'minecraft:the_nether'):
                    dim = DIMENSIONS[params[0]]
                    try:
                        orgpos = [
                            str(x) for x in
                            minecraft_data_api.get_player_info(src.player, 'Pos')
                        ]
                    except Exception as e:
                        src.reply('§c无法获取玩家当前位置信息')
                        server.logger.error(f'获取玩家 {src.player} 位置信息失败: {e}')
                        return
                        
                    newposx, newposz = nether_to_overworld(orgpos[0], orgpos[2])
                    pos = ' '.join((str(newposx), orgpos[1], str(newposz)))
                    humpos = ' '.join(
                        (str(newposx), str(int(float(orgpos[1]))), str(newposz))
                    )
                else:
                    dim = DIMENSIONS[params[0]]
                    pos = '0 80 0'
                    humpos = '0 80 0'

        elif len(params) == 3:  # only position
            if not coordValid(params[0]) or not coordValid(params[1]) or not coordValid(params[2]):
                src.reply('§c坐标不合法')
            else:
                try:
                    dim = DIMENSIONS[
                        minecraft_data_api.get_player_info(src.player, 'Dimension')
                    ]
                except Exception as e:
                    src.reply('§c无法获取玩家当前维度信息')
                    server.logger.error(f'获取玩家 {src.player} 维度信息失败: {e}')
                    return
                    
                pos = ' '.join(
                    (
                        str(float(params[0])),
                        str(params[1]),
                        str(params[2])
                    )
                )
                humpos = ' '.join(
                    (
                        str(int(float(params[0]))),
                        str(int(params[1])),
                        str(int(params[2]))
                    )
                )

        elif len(params) == 4:  # dimension + position
            if params[0] not in DIMENSIONS.keys():
                src.reply('§c没有此维度')
            else:
                dim = DIMENSIONS[params[0]]

            if not coordValid(params[1]) or not coordValid(params[2]) or not coordValid(params[3]):
                src.reply('§c坐标不合法')
                return
                
            pos = ' '.join((str(params[1]), str(params[2]), str(params[3])))
            humpos = ' '.join(
                (str(int(params[1])), str(int(params[2])), str(int(params[3])))
            )

        if dim != '' and pos != '' and params != '':
            try:
                current_dim = minecraft_data_api.get_player_info(src.player, 'Dimension')
                current_pos = minecraft_data_api.get_player_info(src.player, 'Pos')
                
                data[src.player]['back'] = {
                    'dim': DIMENSIONS[current_dim],
                    'pos': current_pos
                }
                save_data(server)
                server.execute(f'execute in {dim} run tp {src.player} {pos}')
                humdim = HUMDIMS[dim]
                src.reply(f'§a传送至§e{humdim}§a, 坐标§e{humpos}')
            except Exception as e:
                src.reply('§c传送过程中发生错误')
                server.logger.error(f'传送玩家 {src.player} 时发生错误: {e}')

    @new_thread('Gamemode back')
    def back(src: PlayerCommandSource):
        if src.is_console:
            return src.reply('§c仅允许玩家使用')
        if src.player not in data.keys():
            return src.reply('§c您只能在旁观模式下传送')
        else:
            try:
                dim = data[src.player]['back']['dim']
                pos = [str(x) for x in data[src.player]['back']['pos']]
                
                current_dim = minecraft_data_api.get_player_info(src.player, 'Dimension')
                current_pos = minecraft_data_api.get_player_info(src.player, 'Pos')
                
                data[src.player]['back'] = {
                    'dim': DIMENSIONS[current_dim],
                    'pos': current_pos
                }
                save_data(server)
                server.execute(
                    f'execute in {dim} run tp {src.player} {" ".join(pos)}'
                )
                src.reply('§a已将您传送至上个地点')
            except Exception as e:
                src.reply('§c返回上个地点时发生错误')
                server.logger.error(f'玩家 {src.player} 返回上个地点时发生错误: {e}')

    # spec literals
    spec_literals = ['!!spec']
    if config.short_command:
        spec_literals1 = ['!s', '！s', '!c', '！c', '!S', '！S', '!C', '！C']
        spec_literals.extend(spec_literals1)
    # register
    server.register_command(
        Literal(spec_literals)
        .requires(lambda src: src.has_permission(config.spec))
        .runs(change_mode)
        .then(
            Literal('help')
            .runs(lambda src: src.reply(HELP_MESSAGE))
        )
        .then(
            Text('player')
            .requires(
                lambda src: src.has_permission(config.spec_other)
            )
            .runs(change_mode)
        )
    )
    server.register_command(
        Literal('!!tp')
        .requires(lambda src: src.has_permission(config.tp))
        .then(
            Text('param1')
            .runs(tp).  # !!tp <dimension> -- param1 = dimension
            then(
                Float('param2')
                .then(
                    Float('param3')
                    # !!tp <x> <y> <z> -- param1 = x, param2 = y, param3 = z
                    .runs(tp)
                    .then(
                        # !!tp <dimension> <x> <y> <z> -- param1 = dimension, param2 = x, param3 = y, param4 = z
                        Float('param4')
                        .runs(tp)
                    )
                )
            )
        )
    )
    server.register_command(
        Literal('!!back')
        .requires(lambda src: src.has_permission(config.back))
        .runs(back)
    )


def save_data(server: PluginServerInterface):
    # 保存数据到server/world目录
    save_data_to_world(server, data)


def sur_to_spec(server, player):
    try:
        dim = DIMENSIONS[minecraft_data_api.get_player_info(player, 'Dimension')]
        pos = minecraft_data_api.get_player_info(player, 'Pos')
        data[player] = {
            'dim': dim,
            'pos': pos,
            'time': time.time(),
            'back': {
                'dim': dim,
                'pos': pos
            }
        }
        server.execute(f'gamemode spectator {player}')
        save_data(server)
    except Exception as e:
        server.logger.error(f'切换玩家 {player} 到旁观模式时发生错误: {e}')


def spec_to_sur(server, player):
    try:
        dim = data[player]['dim']
        pos = [str(x) for x in data[player]['pos']]
        server.execute(
            'execute in {} run tp {} {}'.format(dim, player, ' '.join(pos)))
        server.execute(f'gamemode survival {player}')
        del data[player]
        save_data(server)
    except Exception as e:
        server.logger.error(f'切换玩家 {player} 到生存模式时发生错误: {e}')


def on_player_joined(server, player, info):
    if player in data.keys():
        server.execute(f'gamemode spectator {player}')


def delayed_reload_plugin(server: PluginServerInterface):
    """延迟3秒后重新加载插件"""
    server.logger.info("服务器启动完成，将在3秒后重新加载插件")
    time.sleep(3)
    server.logger.info("重新加载 spec 插件")
    server.reload_plugin('spec')


def on_server_startup(server: PluginServerInterface):
    """服务器启动完成时的回调"""
    # 启动一个新线程来延迟重新加载插件
    Thread(target=delayed_reload_plugin, args=(server,), daemon=True).start()
    server.logger.info("已启动插件重载功能")

