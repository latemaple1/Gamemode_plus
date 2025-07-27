# Gamemode_plus

[![MCDReforged](https://img.shields.io/badge/MCDReforged-2.0+-blue)](https://github.com/MCDReforged/MCDReforged)
[![Python](https://img.shields.io/badge/Python-3.6+-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/late_maple/Gamemode_plus)](LICENSE)

一个功能强大的MCDReforged插件，提供便捷的游戏模式切换、传送和位置记录功能。

> 本插件基于 [AnzhiZhang](https://github.com/AnzhiZhang) 的 [gamemode插件](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/src/gamemode) 进行了功能增强和改进。

## 功能特性

- **游戏模式快速切换**：在生存模式和旁观模式之间一键切换
- **智能传送系统**：支持维度间坐标自动转换传送
- **位置记忆功能**：自动记录并返回上一个位置
- **权限控制系统**：可为不同命令设置权限等级
- **数据持久化**：玩家数据自动保存，服务器重启后不丢失
- **数据迁移**：自动从旧版gamemode插件迁移数据
- **增强的命令系统**：提供更多命令选项和更友好的用户交互
- **多样化的短命令支持**：支持多种大小写及中英文感叹号的缩写命令

## 命令说明

| 命令 | 权限等级 | 说明 |
|------|---------|------|
| `!!spec` | 1 | 在生存模式和旁观模式之间切换 |
| `!!spec <player>` | 2 | 切换指定玩家的游戏模式 |
| `!!tp [dimension] [position]` | 1 | 传送到指定维度或坐标 |
| `!!back` | 1 | 返回上一个位置 |

### 详细命令用法

#### !!spec - 游戏模式切换
```
!!spec                    - 在当前玩家的生存/旁观模式间切换
!!spec <player>           - 切换指定玩家的游戏模式
!!spec help               - 显示帮助信息
```

短命令支持（当short_command配置为true时）：
- `!s` / `！s` (英文/中文感叹号，小写)
- `!S` / `！S` (英文/中文感叹号，大写)
- `!c` / `！c` (英文/中文感叹号，小写)
- `!C` / `！C` (英文/中文感叹号，大写)

#### !!tp - 传送命令
```
!!tp <dimension>          - 传送到指定维度（自动坐标转换）
!!tp <x> <y> <z>          - 传送到当前维度的指定坐标
!!tp <dimension> <x> <y> <z> - 传送到指定维度的指定坐标
```

支持的维度标识符：
- 主世界: `overworld`, `0`, `minecraft:overworld`
- 下界: `nether`, `the_nether`, `-1`, `minecraft:the_nether`
- 末地: `end`, `the_end`, `1`, `minecraft:the_end`


## 相比原版的改进

1. **优化的数据存储**：将玩家数据统一保存到 `server/world/spec_data.json`，避免数据丢失
2. **自动数据迁移**：插件会自动从旧版gamemode插件迁移数据，无需手动操作
3. **增强的错误处理**：改进了错误处理机制，提供更详细的日志信息
4. **更好的维度传送**：优化了维度间传送的坐标自动转换功能
5. **多样化的短命令支持**：增加对多种大小写形式及中英文感叹号的支持（`!s`、`！s`、`!S`、`！S`、`!c`、`！c`、`!C`、`！C`）
6. **配置灵活性**：提供更多配置选项，方便服务器管理员自定义插件行为

## 权限配置

插件默认权限配置如下：
- spec: 1 (普通玩家可切换自己的游戏模式)
- spec_other: 2 (需权限才能切换他人游戏模式)
- tp: 1 (普通玩家可使用传送功能)
- back: 1 (普通玩家可使用返回功能)

## 安装方法

1. 确保已安装 [MCDReforged](https://github.com/MCDReforged/MCDReforged) 2.0+ 和 [minecraft_data_api](https://github.com/MCDReforged/MCDReforgedPlugins/tree/master/src/minecraft_data_api) 插件
2. 下载本插件的最新版本
3. 将插件文件放入 MCDReforged 的 `plugins` 文件夹中
4. 重启服务器或使用 `!!MCDR reload plugin gamemode_plus` 命令加载插件

## 配置文件

插件配置文件位于 `config/gamemode_plus/config.json`：

```json
{
    "short_command": true,
    "spec": 1,
    "spec_other": 2,
    "tp": 1,
    "back": 1
}
```

配置项说明：
- short_command: 是否启用短命令（如 `!s`、`!c` 等，支持大小写及中英文感叹号）
- spec: `!!spec` 命令的权限等级
- spec_other: `!!spec <player>` 命令的权限等级
- tp: `!!tp` 命令的权限等级
- back: `!!back` 命令的权限等级

## 数据存储

玩家数据存储在 `server/world/spec_data.json` 文件中，包含玩家的当前位置、游戏模式和上次位置信息。

当检测到旧版gamemode插件的数据文件时，插件会自动迁移数据到新位置，确保无缝升级体验。

## 兼容性

- 兼容 MCDReforged 2.0+
- 依赖 minecraft_data_api 插件 (>=1.1.0)

## 更新日志

### v1.2.0
- 优化数据存储位置，统一保存到 `server/world/spec_data.json`
- 添加从旧版gamemode插件自动迁移数据功能
- 改进错误处理和日志记录
- 修复部分传送相关的bug
- 增强短命令支持，现在支持多种大小写形式及中英文感叹号

## 开源许可证

本项目基于原作者 [AnzhiZhang](https://github.com/AnzhiZhang) 的工作进行开发，采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解更多详情。