# import paddle
# paddle.utils.run_check()

# import requests
#
#
# objectname = "dicom-save/03100003/2022/0518/0001084330/C20220518212/20220518_03100003_0001084330_C20220518212_383.zip"
# r = requests.get("http://121.37.147.178:8087/dicom_view?objectname="+objectname)
# print(r)
import time
import random
import statsd
c = statsd.StatsClient('localhost', 8125, prefix="http")

print(random.randint(0, 100))

# while True:
# # c.set('users', "0594")
#     c.incr(stat='ris,hid=05940004', count=random.randint(0, 100))
# c.timing(stat='pacs,hid=05940001', delta=320)
# c.incr(stat='05940002', count=random.randint(0, 100), rate=0.5)  # Increment the 'foo' counter.
# c.timing('stats.timed', 320)  # Record a 320ms 'stats.timed'.