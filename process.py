import psutil

class ProcessHandler:
    def __init__(self, target_process_name):
        self.target_process_name = target_process_name
        self.target_pid = None

    def is_process_running(self):
        """Проверка, запущен ли процесс с данным именем."""
        for proc in psutil.process_iter(['name', 'pid']):
            if proc.info['name'] == self.target_process_name:
                self.target_pid = proc.info['pid']
                return True
        return False