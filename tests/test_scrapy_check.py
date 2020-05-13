import os
import subprocess
import sys


def test_scrapy_check():
    run_thru_shell = sys.platform.startswith("win")
    proc = subprocess.Popen(["scrapy", "check"], shell=run_thru_shell, cwd=os.getcwd(),)
    exit_status = proc.wait()
    assert exit_status == 0
