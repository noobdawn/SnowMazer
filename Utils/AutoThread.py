import threading
from typing import Type
import Data.AutoData as ad

class WorkerThread(threading.Thread):
    """
    工作线程基类，子类需实现 _run_job 方法
    """
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()   # 停止信号
        self._pause_event = threading.Event()  # 暂停信号
        self._pause_flag = threading.Lock()    # 防止重复暂停/恢复
        self._pause_event.set()                # 初始允许运行

    def _run_job(self):
        """线程主循环，处理暂停/恢复逻辑"""
        # while not self._stop_event.is_set():
        #     self._pause_event.wait()           # 如果暂停则阻塞
        #     self._task()                       # 执行子类具体任务
        raise NotImplementedError("子类需实现 _run_job 方法")    

    def run(self):
        try:
            self._run_job()
        except Exception as e:
            ad.logger.error(f"线程异常：{e}")
            raise e

    def pause(self):
        """挂起线程"""
        with self._pause_flag:
            self._pause_event.clear()

    def resume(self):
        """恢复线程"""
        with self._pause_flag:
            self._pause_event.set()

    def stop(self):
        """停止线程（下次循环退出）"""
        self._stop_event.set()
        self.resume()  # 确保线程退出阻塞状态

    


class ThreadManager:
    """
    线程管理器（单例），控制工作线程的生命周期
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance._current_thread = None
                cls._instance._thread_lock = threading.Lock()
            return cls._instance

    def start_new(self, worker_cls: Type[WorkerThread], *args, **kwargs):
        """
        启动新线程，若已有线程运行则先停止
        - worker_cls : 继承自 WorkerThread 的子类
        """
        with self._thread_lock:
            if self._current_thread:
                self._current_thread.stop()
                self._current_thread.join()

            self._current_thread = worker_cls(*args, **kwargs)
            self._current_thread.start()

    def pause(self):
        """挂起当前线程"""
        with self._thread_lock:
            if self._current_thread and self._current_thread.is_alive():
                self._current_thread.pause()

    def resume(self):
        """恢复当前线程"""
        with self._thread_lock:
            if self._current_thread and self._current_thread.is_alive():
                self._current_thread.resume()

    def stop(self):
        """停止当前线程"""
        with self._thread_lock:
            if self._current_thread:
                self._current_thread.stop()
                self._current_thread.join()
                self._current_thread = None

    def get_current_worker_class(self):
        """获取当前线程的类类型（用于类型判断）"""
        with self._thread_lock:
            return self._current_thread.__class__ if self._current_thread else None

    def get_current_worker_class_name(self):
        """获取当前线程的类名（用于显示）"""
        with self._thread_lock:
            return self._current_thread.__class__.__name__ if self._current_thread else "无活动线程"