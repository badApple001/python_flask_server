import os
import importlib
import tools.log as log
import tools.File as File

channels = []
def dispatch( msg ):
    channel_name = msg.get('channel')

    if not channel_name.startswith('channel.'):
        channel_name = f'channel.{channel_name}'
    channel = importlib.import_module(channel_name)
    try:
        return channel.apply( msg )
    except Exception as e:
        log.print_exc()
        return str(e)

def get_local_channels():
    paths = os.listdir('./channel/')
    _channels = []
    for path in paths:
        if path.endswith('.py'):
            clss = path[:-3]
            _channels.append(f'channel.{clss}')
    return _channels

def update():
    global channels
    if len(channels) == 0:
        log.debug("正在加载管道...")
        try:
            channels = get_local_channels()
            for channel in channels:
                log.debug(channel)
            update_cls = ",".join(channels)
            File.WriteAllText(os.path.join(os.getcwd(),'hot_update/update_file.txt').replace('\\','/'),update_cls)
            log.debug("加载管道完成")
        except:
            log.print_exception()
    else:
        _channels = get_local_channels()
        if len(_channels) != len(channels):
            log.debug("渠道更新中...")
            channels = _channels
            for channel in channels:
                log.debug(channel)
            try:
                update_cls = ",".join(_channels)
                File.WriteAllText(os.path.join(os.getcwd(),'hot_update/update_file.txt').replace('\\','/'),update_cls)
            except:
                log.print_exception()
                log.print_exc()





