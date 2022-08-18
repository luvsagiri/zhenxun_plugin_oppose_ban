from nonebot.adapters.onebot.v11 import Bot, GroupBanNoticeEvent
from nonebot import on_notice, logger
from configs.config import NICKNAME, Config
from models.ban_user import BanUser
from models.group_info import GroupInfo

__zx_plugin_name__ = "反对禁言 [Hidden]"
__plugin_version__ = 0.1
__plugin_author__ = "luvsagiri"
__plugin_usage__ = f"""
usage：
    爱用不用,sb滚
"""

__plugin_configs__ = {
    "auto_leave_group_after_ban": {
        "value": True,
        "help": "被禁言后是否自动退出群里(并自动删除群认证)",
        "default_value": True, },
    "auto_ban_operator": {
        "value": True,
        "help": "是否自动将操作人加入真寻ban列表",
        "default_value": True, },
}


group_ban_self_handle = on_notice(priority=1, block=False)


@group_ban_self_handle.handle()
async def _(bot: Bot, event: GroupBanNoticeEvent):
    auto_leave_group_after_ban = Config.get_config("oppose_ban", "auto_leave_group_after_ban")
    auto_ban_operator = Config.get_config("oppose_ban", "auto_ban_operator")
    user_id = event.user_id
    group_id = event.group_id
    if user_id == event.self_id and event.sub_type == "ban":
        await bot.send_private_msg(
            user_id=int(list(bot.config.superusers)[0]),
            message=f"唔，{NICKNAME}被禁言了...\n操作者ID{event.operator_id},\n事件发生群ID{group_id}。\n禁言时长:{event.duration}秒",
        )
        if auto_leave_group_after_ban:  # 退群删认证
            await bot.set_group_leave(group_id=group_id)  # 退群

            # 更新群信息
            gl = await bot.get_group_list()
            gl = [g["group_id"] for g in gl]
            num = 0
            rst = ""
            for g in gl:
                group_info = await bot.get_group_info(group_id=g)
                if await GroupInfo.add_group_info(
                        group_info["group_id"],
                        group_info["group_name"],
                        group_info["max_member_count"],
                        group_info["member_count"],
                        1
                ):
                    num += 1
                    logger.info(f"自动更新群组 {g} 信息成功")
                else:
                    logger.info(f"自动更新群组 {g} 信息失败")
                    rst += f"{g} 更新失败\n"
            await bot.send_private_msg(user_id=list(bot.config.superusers)[0],
                                       message=f"成功更新了 {num} 个群的信息\n{rst[:-1]}")

            # 退群检查
            gl2 = await bot.get_group_list()
            if int(event.group_id) in gl2:
                await bot.send_private_msg(user_id=list(bot.config.superusers)[0],
                                           message=f"自动退群可能失败")
            else:
                await bot.send_private_msg(
                    user_id=int(list(bot.config.superusers)[0]),
                    message=f"自动退出群{group_id}成功",
                )
            # 删除认证
            await GroupInfo.set_group_flag(group_id, 0)
            await bot.send_private_msg(user_id=list(bot.config.superusers)[0],
                                       message=f"已删除群认证")

        if auto_ban_operator:
            await BanUser.ban(event.operator_id, 10, 99999999)
            await bot.send_private_msg(
                user_id=int(list(bot.config.superusers)[0]),
                message=f"已将 {event.operator_id} 拉入黑名单！")
