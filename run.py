import os
import signal
import threading
from config import Config
from monitor.run import run_monitor, stop_monitor
from scheduler.run import run_scheduler, stop_scheduler
from utils.check_config import check_config
from version import APP_VERSION
from web.app import FlaskApp


def sigal_handler(num, stack):
    print('捕捉到退出信号：%s，开始退出...' % num)
    # 停止定时服务
    stop_scheduler()
    # 停止监控
    stop_monitor()
    # 退出主进程
    quit()


if __name__ == "__main__":
    # 参数
    os.environ['TZ'] = 'Asia/Shanghai'
    print("配置文件地址：%s" % os.environ.get('NASTOOL_CONFIG'))
    print('NASTool 当前版本号：%s' % APP_VERSION)

    # 检查配置文件
    config = Config()
    if not check_config(config):
        quit()

    # 设置全局代理
    app_cfg = config.get_config('app')
    if app_cfg:
        proxies = app_cfg.get('proxies')
        if proxies:
            http_proxy = proxies.get('http')
            if http_proxy:
                os.environ['HTTP_PROXY'] = http_proxy
            https_proxy = proxies.get('https')
            if https_proxy:
                os.environ['HTTPS_PROXY'] = https_proxy

    # 启动进程
    print("开始启动进程...")

    # 退出事件
    signal.signal(signal.SIGINT, sigal_handler)
    signal.signal(signal.SIGTERM, sigal_handler)

    # 启动定时服务
    run_scheduler()

    # 启动监控服务
    run_monitor()

    # 启动主WEB服务
    FlaskApp().run_service()
