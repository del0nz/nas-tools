from apscheduler.schedulers.blocking import BlockingScheduler
import log
from config import AUTO_REMOVE_TORRENTS_INTERVAL, PT_TRANSFER_INTERVAL, Config, METAINFO_SAVE_INTERVAL, \
    RELOAD_CONFIG_INTERVAL, SYNC_TRANSFER_INTERVAL
from monitor.media_sync import Sync
from scheduler.autoremove_torrents import AutoRemoveTorrents
from scheduler.douban_sync import DoubanSync
from scheduler.pt_signin import PTSignin
from scheduler.pt_transfer import PTTransfer
from scheduler.rss_download import RSSDownloader
from utils.functions import singleton
from utils.meta_helper import MetaHelper


@singleton
class Scheduler:
    SCHEDULER = None
    __pt = None
    __douban = None

    def __init__(self):
        self.init_config()
        self.SCHEDULER = BlockingScheduler(timezone="Asia/Shanghai")

    def init_config(self):
        config = Config()
        self.__pt = config.get_config('pt')
        self.__douban = config.get_config('douban')

    def run_service(self):
        if not self.SCHEDULER:
            return
        if self.__pt:
            # PT种子清理
            pt_seeding_time = self.__pt.get('pt_seeding_time')
            if pt_seeding_time:
                self.SCHEDULER.add_job(AutoRemoveTorrents().run_schedule,
                                       'interval',
                                       seconds=AUTO_REMOVE_TORRENTS_INTERVAL)
                log.info("【RUN】scheduler.autoremove_torrents启动...")

            # PT站签到
            ptsignin_cron = str(self.__pt.get('ptsignin_cron'))
            if ptsignin_cron:
                err_msg = None
                if ptsignin_cron.find(':') != -1:
                    try:
                        hour = int(ptsignin_cron.split(":")[0])
                        minute = int(ptsignin_cron.split(":")[1])
                        self.SCHEDULER.add_job(PTSignin().run_schedule,
                                               "cron",
                                               hour=hour,
                                               minute=minute)
                    except Exception as e:
                        err_msg = str(e)
                else:
                    try:
                        seconds = round(float(ptsignin_cron) * 3600)
                        self.SCHEDULER.add_job(PTSignin().run_schedule,
                                               "interval",
                                               seconds=seconds)
                    except Exception as e:
                        err_msg = str(e)
                if err_msg:
                    log.info("【RUN】scheduler.pt_signin启动失败：%s" % err_msg)
                else:
                    log.info("【RUN】scheduler.pt_signin启动...")

            # PT文件转移
            pt_monitor = self.__pt.get('pt_monitor')
            if pt_monitor:
                self.SCHEDULER.add_job(PTTransfer().run_schedule, 'interval', seconds=PT_TRANSFER_INTERVAL)
                log.info("【RUN】scheduler.pt_transfer启动...")

            # RSS下载器
            pt_check_interval = self.__pt.get('pt_check_interval')
            if pt_check_interval:
                self.SCHEDULER.add_job(RSSDownloader().run_schedule, 'interval', seconds=int(pt_check_interval))
                log.info("【RUN】scheduler.rss_download启动...")

        # 豆瓣电影同步
        if self.__douban:
            douban_interval = self.__douban.get('interval')
            if douban_interval:
                self.SCHEDULER.add_job(DoubanSync().run_schedule, 'interval', seconds=float(douban_interval) * 3600)
                log.info("【RUN】scheduler.douban_sync启动...")

        # 配置定时生效
        self.SCHEDULER.add_job(Config().init_config, 'interval', seconds=RELOAD_CONFIG_INTERVAL)

        # 元数据定时保存
        self.SCHEDULER.add_job(MetaHelper().save_meta_data, 'interval', seconds=METAINFO_SAVE_INTERVAL)

        # 定时把队列中的监控文件转移走
        self.SCHEDULER.add_job(Sync().transfer_mon_files, 'interval', seconds=SYNC_TRANSFER_INTERVAL)

        self.SCHEDULER.start()

    def stop_service(self):
        if self.SCHEDULER:
            self.SCHEDULER.remove_all_jobs()
            self.SCHEDULER.shutdown()
