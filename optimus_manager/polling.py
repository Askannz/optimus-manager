import time


def poll_block(f, poll_interval=0.2, timeout=2):

    t0 = time.time()
    t = t0
    while abs(t - t0) < timeout:
        if not f():
            return True
        else:
            time.sleep(poll_interval)
            t = time.time()

    return False
